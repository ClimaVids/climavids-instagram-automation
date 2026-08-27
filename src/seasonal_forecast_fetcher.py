"""Fetch and persist trustworthy seasonal-forecast source evidence for Iran.

This module deliberately does not infer numeric forecast values from HTML page text.
Numeric values must come from a machine-readable forecast dataset and a dedicated
parser before they are allowed into content generation.
"""

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
REQUEST_TIMEOUT = 30

# Official, public source pages. These are source references, not numeric datasets.
ECMWF_TEMPERATURE = "https://www.ecmwf.int/en/forecasts/datasets/2-m-temperature-area-averages-seasonal-forecast-seas5"
ECMWF_PRECIPITATION = "https://www.ecmwf.int/en/forecasts/datasets/precipitation-area-averages-seasonal-forecast-seas5"
ECMWF_ACCESS = "https://www.ecmwf.int/en/forecasts/accessing-forecasts"
CFS_CATALOG = "https://www.ncei.noaa.gov/products/weather-climate-models/climate-forecast-system"
CFS_NOMADS_ROOT = "https://nomads.ncep.noaa.gov/pub/data/nccf/com/cfs/prod/"
CFS_GRIBFILTER = "https://nomads.ncep.noaa.gov/gribfilter.php?ds=cfs_flx"
IRIMO_HOME = "https://www.irimo.ir/"


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
        return {"version": 2, "updated_at": None, "records": {}, "latest": None}


def _save_cache(cache: dict[str, Any]) -> None:
    payload = json.dumps(cache, ensure_ascii=False, indent=2) + "\n"
    try:
        CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
        CACHE_FILE.write_text(payload, encoding="utf-8")
    except OSError:
        return

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
        pass


def _cache_key(provider: str, season_key: str) -> str:
    return hashlib.sha256(f"{provider}:{season_key}".encode()).hexdigest()[:24]


def _extract_links(html: str, base_url: str, labels: tuple[str, ...]) -> list[dict[str, str]]:
    soup = BeautifulSoup(html, "html.parser")
    links: list[dict[str, str]] = []
    for anchor in soup.find_all("a", href=True):
        label = anchor.get_text(" ", strip=True)
        href = urljoin(base_url, anchor["href"])
        lowered = f"{label} {href}".lower()
        if any(term.lower() in lowered for term in labels):
            links.append({"label": label[:160], "url": href})
    return links[:30]


def fetch_ecmwf(season_key: str) -> dict[str, Any]:
    temp_response = requests.get(ECMWF_TEMPERATURE, timeout=REQUEST_TIMEOUT)
    temp_response.raise_for_status()
    precip_response = requests.get(ECMWF_PRECIPITATION, timeout=REQUEST_TIMEOUT)
    precip_response.raise_for_status()

    temp_text = BeautifulSoup(temp_response.text, "html.parser").get_text(" ", strip=True)
    precip_text = BeautifulSoup(precip_response.text, "html.parser").get_text(" ", strip=True)

    # Do not parse chart-page prose for numbers. The pages expose the official
    # seasonal products and Open Charts, but numeric values are rendered separately.
    return {
        "provider": "ECMWF",
        "source_url": ECMWF_TEMPERATURE,
        "source_urls": [ECMWF_TEMPERATURE, ECMWF_PRECIPITATION, ECMWF_ACCESS],
        "retrieved_at": _now(),
        "season_key": season_key,
        "status": "official_seasonal_chart_sources_verified",
        "numeric": {},
        "numeric_source_ready": False,
        "products": ["2m temperature area averages", "precipitation area averages"],
        "evidence": {
            "temperature_page": temp_text[:1200],
            "precipitation_page": precip_text[:1200],
        },
        "note": "Numeric forecast values are intentionally left empty until a machine-readable ECMWF dataset or chart payload is parsed by a dedicated adapter.",
    }


def _latest_cfs_runs() -> list[str]:
    response = requests.get(CFS_NOMADS_ROOT, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    html = response.text
    dates = sorted(set(re.findall(r"cfs\.(\d{8})/", html)), reverse=True)
    return dates[:5]


def fetch_cfs(season_key: str) -> dict[str, Any]:
    response = requests.get(CFS_CATALOG, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    text = soup.get_text(" ", strip=True)
    latest_runs = _latest_cfs_runs()

    return {
        "provider": "NOAA/NCEP CFSv2",
        "source_url": CFS_CATALOG,
        "nomads_root": CFS_NOMADS_ROOT,
        "grib_filter": CFS_GRIBFILTER,
        "retrieved_at": _now(),
        "season_key": season_key,
        "status": "operational_9_month_forecast_source_verified",
        "numeric": {},
        "numeric_source_ready": True,
        "latest_runs": latest_runs,
        "forecast_horizon": "~9 months",
        "format": "GRIB2",
        "evidence": text[:1800],
        "note": "CFSv2 numeric extraction requires a dedicated GRIB2 subset/decoder path; no values are inferred from the catalog HTML.",
    }


def fetch_irimo(season_key: str) -> dict[str, Any]:
    response = requests.get(
        IRIMO_HOME,
        timeout=REQUEST_TIMEOUT,
        headers={"User-Agent": "ClimaVidsSeasonalBot/2.0"},
    )
    response.raise_for_status()
    links = _extract_links(
        response.text,
        IRIMO_HOME,
        ("فصلی", "پیش بینی", "پیش‌بینی", "چشم انداز", "چشم‌انداز", "forecast", "seasonal"),
    )
    return {
        "provider": "IRIMO",
        "source_url": IRIMO_HOME,
        "retrieved_at": _now(),
        "season_key": season_key,
        "status": "official_site_scanned",
        "numeric": {},
        "numeric_source_ready": bool(links),
        "candidate_reports": links,
        "note": "IRIMO numeric values are not extracted from generic page HTML; a dedicated report parser is required before use in content.",
    }


def fetch_seasonal_forecasts(season_key: str) -> dict[str, Any]:
    cache = _load_cache()
    cache.setdefault("records", {})
    result: dict[str, Any] = {
        "season_key": season_key,
        "retrieved_at": _now(),
        "sources": {},
        "data_quality": "none",
    }

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
                "numeric_source_ready": False,
            }

    numeric_sources = [
        src for src in result["sources"].values()
        if isinstance(src, dict) and isinstance(src.get("numeric"), dict) and src["numeric"]
    ]
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
