"""Free-tier content services for ClimaVids."""

from __future__ import annotations

import json
import os
import random
from pathlib import Path
from typing import Any

import requests

CACHE_PATH = Path(os.getenv("CONTENT_CACHE_PATH", "state/content_cache.json"))


def _load_cache() -> dict[str, Any]:
    try:
        if CACHE_PATH.exists():
            return json.loads(CACHE_PATH.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        pass
    return {"captions": [], "media": {}}


def _save_cache(cache: dict[str, Any]) -> None:
    try:
        CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
        CACHE_PATH.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")
    except OSError:
        pass


def fetch_pexels_media(query: str = "Iran climate seasonal forecast") -> dict[str, Any]:
    api_key = os.getenv("PEXELS_API_KEY", "").strip()
    if not api_key:
        return _cached_media_or_empty(query)
    try:
        response = requests.get(
            "https://api.pexels.com/v1/search",
            headers={"Authorization": api_key},
            params={"query": query, "per_page": 10, "orientation": "portrait"},
            timeout=20,
        )
        response.raise_for_status()
        photos = response.json().get("photos", [])
        if not photos:
            return _cached_media_or_empty(query)
        photo = random.choice(photos)
        result = {
            "source": "pexels",
            "url": photo.get("src", {}).get("original", ""),
            "page_url": photo.get("url", ""),
            "photographer": photo.get("photographer"),
        }
        cache = _load_cache()
        cache.setdefault("media", {})[query] = result
        _save_cache(cache)
        return result
    except (requests.RequestException, ValueError, TypeError, KeyError):
        return _cached_media_or_empty(query)


def _cached_media_or_empty(query: str) -> dict[str, Any]:
    cache = _load_cache()
    return cache.get("media", {}).get(query, {"source": "none", "url": "", "photographer": None})


def _gemini_text(prompt: str, timeout: int = 30) -> str | None:
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        return None
    model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    try:
        response = requests.post(
            url,
            params={"key": api_key},
            json={"contents": [{"parts": [{"text": prompt}]}]},
            timeout=timeout,
        )
        response.raise_for_status()
        payload = response.json()
        return payload["candidates"][0]["content"]["parts"][0]["text"].strip() or None
    except (requests.RequestException, ValueError, KeyError, IndexError, TypeError):
        return None


def generate_chart_caption(chart: dict[str, Any]) -> str | None:
    """Create a short Persian caption from official chart metadata only."""
    period = str(chart.get("valid_month", ""))[:7]
    forecast_type = str(chart.get("forecast_type", "ensemble mean"))
    default = (
        "چشم‌انداز بارش ایران در دوره پیش‌رو بر اساس جدیدترین خروجی فصلی ECMWF.\n"
        f"نوع خروجی: {forecast_type}؛ دوره آغازشده از {period}.\n"
        "نقشه، چشم‌انداز احتمالاتی مدل را نشان می‌دهد و به معنی پیش‌بینی قطعی برای هر شهر نیست.\n\n"
        "Chart: ECMWF — CC BY 4.0\n"
        "ClimaVids | دکتر ایمانی‌پور"
    )

    if not os.getenv("GEMINI_API_KEY", "").strip():
        return default

    prompt = (
        "برای صفحه علمی ClimaVids یک کپشن فارسی کوتاه و دقیق درباره نقشه رسمی پیش‌بینی فصلی بنویس. "
        "هیچ عدد یا نتیجه‌ای خارج از متادیتای ورودی اضافه نکن. مخاطب می‌خواهد بداند چشم‌انداز بارش ایران چیست. "
        "حداکثر 500 کاراکتر. در پایان حتماً این دو خط را عیناً حفظ کن:\n"
        "Chart: ECMWF — CC BY 4.0\nClimaVids | دکتر ایمانی‌پور\n\n"
        f"Chart metadata:\n{json.dumps(chart, ensure_ascii=False, indent=2)[:8000]}"
    )
    return _gemini_text(prompt, timeout=30) or default


def generate_seasonal_caption(forecast: dict[str, Any]) -> str | None:
    """Backward-compatible wrapper for older callers."""
    return generate_chart_caption(forecast)


def generate_gemini_reply(comment_text: str) -> str | None:
    prompt = (
        "برای کامنت زیر یک پاسخ کوتاه، گرم و طبیعی به فارسی بنویس. "
        "پاسخ باید مشخصاً به محتوای همان کامنت مرتبط باشد، از ادعای علمی ساختگی دوری کند و در صورت مناسب بودن یک سؤال مرتبط بپرسد. حداکثر 220 کاراکتر.\n"
        f"کامنت: {comment_text}"
    )
    return _gemini_text(prompt, timeout=20)
