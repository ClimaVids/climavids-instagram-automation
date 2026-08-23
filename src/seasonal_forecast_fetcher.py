"""Fetch and persist Iran seasonal-forecast evidence on the state branch."""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

STATE_BRANCH = os.getenv("STATE_BRANCH", "state")
CACHE_FILE = Path(os.getenv("SEASONAL_CACHE_FILE", "seasonal_forecast_cache.json"))
ECMWF_CHARTS = "https://charts.ecmwf.int/?facets={%22Range%22:[%22Long+%28Months%29%22,%22Seasonal%22],%22Type%22:[%22Forecasts%22]}"
CFS_CATALOG = "https://www.ncei.noaa.gov/products/weather-climate-models/climate-forecast-system"
IRIMO_HOME = "https://www.irimo.ir/"
REQUEST_TIMEOUT = 30


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _git(*args: str, cwd: str | Path | None = None) -> str:
    result = subprocess.run(args, cwd=cwd, check=True, capture_output=True, text=True)
    return result.stdout.strip()


def _load_cache() -> dict[str, Any]:
    try:
        return json.loads(CACHE_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        pass

    try:
        _git("git", "fetch", "origin", STATE_BRANCH)
        raw = _git("git", "show", f"origin/{STATE_BRANCH}:{CACHE_FILE.as_posix()}")
        return json.loads(raw)
    except (subprocess.CalledProcessError, ValueError, TypeError, OSError):
        return {"version": 1, "updated_at": None, "records": {}, "latest": None}


def _save_cache(cache: dict[str, Any]) -> None:
    payload = json.dumps(cache, ensure_ascii=False, indent=2) + "\n"
    try:
        CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
        CACHE_FILE.write_text(payload, encoding="utf-8")
    except OSError:
        return

    # Persist cache outside the application branch so Runner teardown cannot erase it.
    try:
        _git("git", "fetch", "origin", STATE_BRANCH)
        with tempfile.TemporaryDirectory(prefix="climavids-seasonal-cache-") as tmp:
            worktree = Path(tmp) / "state-worktree"
            _git("git", "worktree", "add", "--detach", str(worktree), f"origin/{STATE_BRANCH}")
            try:
                target = worktree / CACHE_FILE
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(payload, encoding="utf-8")
                _git("git", "config", "user.name", "github-actions[bot]", cwd=worktree)
                _git("git", "config", "user.email", "41898282+github-actions[bot]@users.noreply.github.com", cwd=worktree)
                _git("git", "add", CACHE_FILE.as_posix(), cwd=worktree)
                status = subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=worktree)
                if status.returncode != 0:
                    _git("git", "commit", "-m", "Update seasonal forecast cache", cwd=worktree)
                    _git("git", "push", "origin", f"HEAD:{STATE_BRANCH}", cwd=worktree)
            finally:
                subprocess.run(["git", "worktree", "remove", "--force", str(worktree)], check=False, capture_output=True, text=True)
    except (subprocess.CalledProcessError, OSError):
        # Cache persistence is best-effort; current-run data can still be used safely.
        pass


def _cache_key(provider: str, season_key: str) -> str:
    return hashlib.sha256(f"{provider}:{season_key}".encode()).hexdigest()[:24]


def _extract_numeric(text: str, keywords: tuple[str, ...]) -> float | None:
    lowered = text.lower()
    for keyword in keywords:
        pos = lowered.find(keyword.lower())
        if pos < 0:
            continue
        snippet = text[max(0, pos - 80): pos + 220]
        match = re.search(r"([-+]?\d+(?:[.,]\d+)?)\s*(?:°?c|mm|%)", snippet, re.I)
        if match:
            try:
                return float(match.group(1).replace(",", "."))
            except ValueError:
                continue
    return None


def fetch_ecmwf(season_key: str) -> dict[str, Any]:
    response = requests.get(ECMWF_CHARTS, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    text = BeautifulSoup(response.text, "html.parser").get_text(" ", strip=True)
    numeric: dict[str, float] = {}
    temp = _extract_numeric(text, ("temperature anomaly", "2 m temperature"))
    precip = _extract_numeric(text, ("precipitation anomaly", "precipitation"))
    if temp is not None:
        numeric["temperature_anomaly_c"] = temp
    if precip is not None:
        numeric["precipitation_value"] = precip
    return {
        "provider": "ECMWF",
        "source_url": ECMWF_CHARTS,
        "retrieved_at": _now(),
        "season_key": season_key,
        "status": "official_seasonal_chart_source",
        "numeric": numeric,
        "evidence": text[:3000],
        "note": "Official SEAS5 seasonal charts are public; raw SEAS5 files are not assumed to be part of the free Open Data subset.",
    }


def fetch_cfs(season_key: str) -> dict[str, Any]:
    response = requests.get(CFS_CATALOG, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    text = soup.get_text(" ", strip=True)
    links = []
    for anchor in soup.find_all("a", href=True):
        href = urljoin(CFS_CATALOG, anchor["href"])
        label = anchor.get_text(" ", strip=True)
        if "forecast" in label.lower() or "tds" in label.lower():
            links.append({"label": label[:120], "url": href})
    return {
        "provider": "NOAA/NCEP CFSv2",
        "source_url": CFS_CATALOG,
        "retrieved_at": _now(),
        "season_key": season_key,
        "status": "operational_9_month_forecast_catalog",
        "numeric": {},
        "forecast_horizon": "~9 months",
        "data_access_links": links[:20],
        "evidence": text[:3000],
    }


def fetch_irimo(season_key: str) -> dict[str, Any]:
    response = requests.get(IRIMO_HOME, timeout=REQUEST_TIMEOUT, headers={"User-Agent": "ClimaVidsSeasonalBot/1.0"})
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    candidates = []
    for anchor in soup.find_all("a", href=True):
        label = anchor.get_text(" ", strip=True)
        href = urljoin(IRIMO_HOME, anchor["href"])
        if any(term in label for term in ("فصلی", "پیش بینی", "پیش‌بینی", "چشم انداز", "چشم‌انداز")):
            candidates.append({"title": label[:200], "url": href})
    return {
        "provider": "IRIMO",
        "source_url": IRIMO_HOME,
        "retrieved_at": _now(),
        "season_key": season_key,
        "status": "official_site_scan",
        "numeric": {},
        "candidate_reports": candidates[:20],
    }


def fetch_seasonal_forecasts(season_key: str) -> dict[str, Any]:
    cache = _load_cache()
    cache.setdefault("records", {})
    result: dict[str, Any] = {"season_key": season_key, "retrieved_at": _now(), "sources": {}, "data_quality": "none"}

    for provider, func in (("ecmwf", fetch_ecmwf), ("cfs", fetch_cfs), ("irimo", fetch_irimo)):
        key = _cache_key(provider, season_key)
        try:
            record = func(season_key)
            cache["records"][key] = record
            result["sources"][provider] = record
        except (requests.RequestException, ValueError, TypeError, KeyError) as exc:
            result["sources"][provider] = cache["records"].get(key) or {
                "provider": provider,
                "status": "unavailable",
                "error": type(exc).__name__,
                "numeric": {},
            }

    numeric_sources = [src for src in result["sources"].values() if isinstance(src, dict) and src.get("numeric")]
    result["data_quality"] = "numeric_or_mixed" if numeric_sources else "official-source-metadata-only"
    cache["updated_at"] = _now()
    cache["latest"] = result
    _save_cache(cache)
    return result


def load_latest_forecast() -> dict[str, Any] | None:
    latest = _load_cache().get("latest")
    return latest if isinstance(latest, dict) else None


def seasonal_data_or_cache(season_key: str) -> dict[str, Any]:
    try:
        return fetch_seasonal_forecasts(season_key)
    except Exception:
        latest = load_latest_forecast()
        if latest:
            return latest
        raise
