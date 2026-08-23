"""Fetch and cache Iran seasonal-forecast evidence from authoritative sources.

Sources:
- ECMWF Seasonal Forecast / Open Charts: official SEAS5 metadata and public
  chart pages. The free ECMWF Open Data subset does not currently expose the
  full SEAS5 raw files, so this adapter never invents numeric ECMWF values.
- NOAA/NCEP CFSv2: official operational 9-month forecast catalog and public
  HTTPS/TDS endpoints.
- IRIMO: official website/report pages, best-effort HTML extraction.

The output is deliberately conservative: only numeric values that can be
parsed from a source are exposed. Otherwise the last validated cache is used.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

CACHE_FILE = Path(os.getenv("SEASONAL_CACHE_FILE", "state/seasonal_forecast_cache.json"))
ECMWF_CHARTS = "https://charts.ecmwf.int/?facets={%22Range%22:[%22Long+%28Months%29%22,%22Seasonal%22],%22Type%22:[%22Forecasts%22]}"
CFS_CATALOG = "https://www.ncei.noaa.gov/products/weather-climate-models/climate-forecast-system"
IRIMO_HOME = "https://www.irimo.ir/"
REQUEST_TIMEOUT = 30


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_cache() -> dict[str, Any]:
    try:
        return json.loads(CACHE_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        return {"version": 1, "updated_at": None, "records": {}}


def _save_cache(cache: dict[str, Any]) -> None:
    try:
        CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
        CACHE_FILE.write_text(json.dumps(cache, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    except OSError:
        pass


def _cache_key(provider: str, season_key: str) -> str:
    return hashlib.sha256(f"{provider}:{season_key}".encode()).hexdigest()[:24]


def _extract_numeric(text: str, keywords: tuple[str, ...]) -> float | None:
    lowered = text.lower()
    for keyword in keywords:
        pos = lowered.find(keyword.lower())
        if pos < 0:
            continue
        snippet = text[max(0, pos - 80): pos + 180]
        match = re.search(r"([-+]?\d+(?:[.,]\d+)?)\s*(?:°?c|mm|%)?", snippet, re.I)
        if match:
            try:
                return float(match.group(1).replace(",", "."))
            except ValueError:
                continue
    return None


def fetch_ecmwf(season_key: str) -> dict[str, Any]:
    """Fetch official ECMWF seasonal chart evidence without fabricating raw data."""
    response = requests.get(ECMWF_CHARTS, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    text = BeautifulSoup(response.text, "html.parser").get_text(" ", strip=True)
    record = {
        "provider": "ECMWF",
        "source_url": ECMWF_CHARTS,
        "retrieved_at": _now(),
        "season_key": season_key,
        "status": "official_seasonal_chart_source",
        "numeric": {},
        "evidence": text[:3000],
        "note": "Official SEAS5 seasonal charts are available publicly; raw SEAS5 files are not assumed to be part of the free Open Data subset.",
    }
    # Only keep an explicitly parsed anomaly when the public page exposes it.
    temp = _extract_numeric(text, ("temperature anomaly", "2 m temperature"))
    precip = _extract_numeric(text, ("precipitation anomaly", "precipitation"))
    if temp is not None:
        record["numeric"]["temperature_anomaly_c"] = temp
    if precip is not None:
        record["numeric"]["precipitation_value"] = precip
    return record


def fetch_cfs(season_key: str) -> dict[str, Any]:
    """Record the official CFSv2 operational seasonal source and parse numeric page evidence when present."""
    response = requests.get(CFS_CATALOG, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    text = soup.get_text(" ", strip=True)
    record = {
        "provider": "NOAA/NCEP CFSv2",
        "source_url": CFS_CATALOG,
        "retrieved_at": _now(),
        "season_key": season_key,
        "status": "operational_9_month_forecast_catalog",
        "numeric": {},
        "evidence": text[:3000],
        "forecast_horizon": "~9 months",
    }
    links = []
    for anchor in soup.find_all("a", href=True):
        href = urljoin(CFS_CATALOG, anchor["href"])
        label = anchor.get_text(" ", strip=True)
        if "forecast" in label.lower() or "tds" in label.lower() or "https" in label.lower():
            links.append({"label": label[:120], "url": href})
    record["data_access_links"] = links[:20]
    return record


def fetch_irimo(season_key: str) -> dict[str, Any]:
    """Best-effort extraction from the official IRIMO website; cache on failure."""
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
            cached = cache["records"].get(key)
            result["sources"][provider] = cached or {
                "provider": provider,
                "status": "unavailable",
                "error": type(exc).__name__,
                "numeric": {},
            }

    has_numeric = any(src.get("numeric") for src in result["sources"].values() if isinstance(src, dict))
    result["data_quality"] = "numeric_or_mixed" if has_numeric else "official-source-metadata-only"
    cache["updated_at"] = _now()
    cache["latest"] = result
    _save_cache(cache)
    return result


def load_latest_forecast() -> dict[str, Any] | None:
    cache = _load_cache()
    latest = cache.get("latest")
    return latest if isinstance(latest, dict) else None


def seasonal_data_or_cache(season_key: str) -> dict[str, Any]:
    try:
        return fetch_seasonal_forecasts(season_key)
    except Exception:
        latest = load_latest_forecast()
        if latest:
            return latest
        raise
