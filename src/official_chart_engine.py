"""Download and validate official forecast charts for ClimaVids.

The engine prefers the original chart image published by the provider rather than
reconstructing a map from scraped HTML. It records the product, forecast times,
image URL, and attribution required for reuse.
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any
from urllib.parse import urlencode

import requests

OPENCHARTS_API = "https://charts.ecmwf.int/opencharts-api/v1"
ECMWF_CHART_PRODUCT = "seasonal_system5_standard_rain"
ECMWF_CHART_PAGE = "https://charts.ecmwf.int/products/seasonal_system5_standard_rain"
REQUEST_TIMEOUT = 30


def _month_start(year: int, month: int) -> date:
    return date(year, month, 1)


def _next_month(value: date) -> date:
    if value.month == 12:
        return date(value.year + 1, 1, 1)
    return date(value.year, value.month + 1, 1)


def _yyyymmddhhmm(value: date) -> str:
    return value.strftime("%Y%m%d0000")


def build_ecmwf_precipitation_chart_url(
    *,
    base_time: date,
    valid_time: date,
    area: str = "GLOB",
    stats: str = "ensm",
) -> str:
    params = urlencode(
        {
            "area": area,
            "base_time": _yyyymmddhhmm(base_time),
            "stats": stats,
            "valid_time": _yyyymmddhhmm(valid_time),
        }
    )
    return f"{ECMWF_CHART_PAGE}?{params}"


def fetch_ecmwf_precipitation_chart(
    *,
    forecast_date: date | None = None,
    area: str = "GLOB",
    stats: str = "ensm",
) -> dict[str, Any]:
    """Return the exact ECMWF Open Charts image and its provenance.

    The ECMWF OpenCharts API returns metadata and a direct PNG link. No numeric
    values are inferred from HTML or from the rendered image.
    """
    now = forecast_date or datetime.now(timezone.utc).date()
    base_time = _month_start(now.year, now.month)
    valid_time = _next_month(base_time)

    params = {
        "area": area,
        "base_time": _yyyymmddhhmm(base_time),
        "stats": stats,
        "valid_time": _yyyymmddhhmm(valid_time),
    }
    endpoint = f"{OPENCHARTS_API}/products/{ECMWF_CHART_PRODUCT}/"
    response = requests.get(endpoint, params=params, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    payload = response.json()

    data = payload.get("data") or {}
    image = data.get("data") or data
    image_url = ((image.get("link") or {}).get("href")) if isinstance(image, dict) else None
    meta = payload.get("meta") or {}
    if not image_url:
        raise ValueError("ECMWF OpenCharts API returned no image URL")

    license_name = str(meta.get("license") or "CC-BY-4.0")
    copyright_text = str(meta.get("copyright") or "European Centre for Medium-Range Weather Forecasts (ECMWF)")
    chart_url = build_ecmwf_precipitation_chart_url(
        base_time=base_time,
        valid_time=valid_time,
        area=area,
        stats=stats,
    )

    return {
        "provider": "ECMWF",
        "product": ECMWF_CHART_PRODUCT,
        "variable": "precipitation",
        "chart_type": "seasonal_spatial_map",
        "area": area,
        "forecast_base_month": base_time.isoformat(),
        "valid_month": valid_time.isoformat(),
        "valid_period": "three-month season commencing with valid month",
        "forecast_type": "ensemble mean" if stats == "ensm" else stats,
        "chart_url": chart_url,
        "image_url": image_url,
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "license": license_name,
        "copyright": copyright_text,
        "modified": False,
        "attribution": "Chart: ECMWF — licensed under CC-BY-4.0",
    }
