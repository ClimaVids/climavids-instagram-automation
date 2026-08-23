"""Free-tier content services with safe fallbacks and no fabricated forecast data."""

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


def generate_seasonal_caption(forecast: dict[str, Any]) -> str | None:
    """Generate an identity-branded caption strictly from supplied forecast evidence."""
    prompt = (
        "برای Instagram کلیماویدز یک کپشن فارسی درباره پیش‌بینی فصلی ایران بنویس. "
        "این محتوا باید با نام «دکتر ایمانی‌پور» و برند ClimaVids شناسه‌دار باشد و ترجیحاً با «بر اساس تحلیل دکتر ایمانی‌پور از مدل‌های جهانی...» یا جمله‌ای هم‌معنا شروع شود. "
        "فقط از داده‌ها و شواهد موجود در متن ورودی استفاده کن؛ هیچ عدد، درصد، منطقه یا رابطه اقلیمی را حدس نزن. "
        "اگر داده عددی کافی نیست، صریحاً محدودیت را توضیح بده و ادعای کمی نساز. "
        "ساختار پیشنهادی: عنوان علمی، خلاصه بارش و دما، اعداد موجود با واحد و منبع، تحلیل مختصر سازوکارهای کلان فقط اگر در داده‌ها پشتیبانی شده، پیامدهای محتاطانه برای آب و کشاورزی، و یک سؤال تعاملی. "
        "لحن علمی اما قابل‌فهم، گرم، انسانی و مسئولانه باشد. حداکثر 1400 کاراکتر.\n\n"
        f"داده‌های پیش‌بینی فصلی:\n{json.dumps(forecast, ensure_ascii=False, indent=2)[:18000]}"
    )
    return _gemini_text(prompt, timeout=45)


def generate_gemini_reply(comment_text: str) -> str | None:
    prompt = (
        "برای کامنت زیر یک پاسخ کوتاه، گرم و طبیعی به فارسی بنویس. "
        "پاسخ باید مشخصاً به محتوای همان کامنت مرتبط باشد، از ادعای علمی ساختگی دوری کند و در صورت مناسب بودن یک سؤال مرتبط بپرسد. حداکثر 220 کاراکتر.\n"
        f"کامنت: {comment_text}"
    )
    return _gemini_text(prompt, timeout=20)
