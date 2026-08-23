"""Optional free-tier content sources used by the daily dry-run pipeline."""

from __future__ import annotations

import os
from typing import Any

import requests

DEFAULT_CAPTION = "دانستنی اقلیمی امروز 🌍"
DEFAULT_MEDIA_URL = ""


def fetch_pexels_media(query: str = "climate weather nature") -> dict[str, Any]:
    api_key = os.getenv("PEXELS_API_KEY", "").strip()
    if not api_key:
        return {"source": "fallback", "url": DEFAULT_MEDIA_URL, "photographer": None}
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
            return {"source": "fallback", "url": DEFAULT_MEDIA_URL, "photographer": None}
        photo = photos[0]
        return {
            "source": "pexels",
            "url": photo.get("src", {}).get("original", ""),
            "page_url": photo.get("url", ""),
            "photographer": photo.get("photographer"),
        }
    except (requests.RequestException, ValueError, TypeError, KeyError):
        return {"source": "fallback", "url": DEFAULT_MEDIA_URL, "photographer": None}


def generate_gemini_caption(topic: str) -> str:
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        return DEFAULT_CAPTION
    model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    prompt = (
        "برای کانال علمی ClimaVids یک کپشن فارسی کوتاه و دقیق برای Instagram بنویس. "
        f"موضوع: {topic}. حداکثر 500 کاراکتر، بدون ادعاهای ساختگی و با لحن علمی و جذاب."
    )
    try:
        response = requests.post(
            url,
            params={"key": api_key},
            json={"contents": [{"parts": [{"text": prompt}]}]},
            timeout=30,
        )
        response.raise_for_status()
        payload = response.json()
        text = payload["candidates"][0]["content"]["parts"][0]["text"].strip()
        return text or DEFAULT_CAPTION
    except (requests.RequestException, ValueError, KeyError, IndexError, TypeError):
        return DEFAULT_CAPTION
