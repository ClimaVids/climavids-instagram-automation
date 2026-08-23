"""Optional free-tier content services with safe local fallbacks and cache."""

from __future__ import annotations

import json
import os
import random
from pathlib import Path
from typing import Any

import requests

CACHE_PATH = Path(os.getenv("CONTENT_CACHE_PATH", "state/content_cache.json"))
DEFAULT_CAPTIONS = [
    "امروز آسمان شهر شما چه حال‌وهوایی دارد؟ 🌤️ یک عکس بفرستید یا برامان بنویسید.",
    "گاهی یک تغییر کوچک در دما، داستان بزرگی پشت خودش دارد. به نظرتان امروز هوا چه پیامی دارد؟ 🌍",
    "اگر قرار بود آب‌وهوای امروز شهر شما یک جمله باشد، چی می‌نوشتید؟ ☁️",
    "یک نکته اقلیمی جالب: چیزی که امروز در آسمان می‌بینیم، همیشه فقط درباره امروز نیست. نظر شما چیه؟",
    "امروز بیشتر با گرما درگیر بودید یا با باد؟ تجربه‌تان را در کامنت‌ها بنویسید. 🌬️",
    "ابرها فقط زیبا نیستند؛ هرکدام داستانی از دما و رطوبت را با خودشان دارند. ☁️",
    "به نظرتان کدام پدیده جوی از همه جذاب‌تر است: باران، برف، مه یا رعدوبرق؟",
    "هواشناسی یعنی پیدا کردن داستانی که پشت عددهای دما و بارش پنهان شده است. 📊",
    "امروز دمای شهر شما چند درجه بود؟ بیایید یک رکورد کوچک اقلیمی بسازیم. 🌡️",
    "گاهی یک نسیم ساده می‌تواند حس یک روز گرم را کاملاً عوض کند. امروز در شهر شما باد چطور بود؟",
    "اگر از پنجره بیرون را نگاه کنید، اولین نشانه تغییر هوا چیست؟ 👀",
    "باران برای شما بیشتر حس آرامش دارد یا خاطره؟ تجربه‌تان را با ما شریک شوید. 🌧️",
    "آسمان هر روز یک منظره تازه دارد؛ امروز نوبت کدام شهر است؟ عکس‌هایتان را بفرستید. 📸",
    "یک سؤال اقلیمی: چرا بعضی روزها هوا گرم‌تر حس می‌شود، حتی وقتی دما خیلی فرق نکرده؟",
    "شما برای پیش‌بینی هوا بیشتر به اپلیکیشن‌ها اعتماد می‌کنید یا به نشانه‌های آسمان؟",
    "تغییرات آب‌وهوا را خیلی وقت‌ها اول از رفتار ابرها و بادها می‌شود فهمید. شما چه نشانه‌ای را دنبال می‌کنید؟",
    "امروز یک پدیده جوی دیدید که ارزش عکس گرفتن داشته باشد؟ همین‌جا تعریفش کنید. 🌦️",
    "از نظر شما بهترین فصل برای تماشای آسمان کدام است؟ دلیل‌تان را هم بگویید. 🍂☀️",
    "یک روز معمولی می‌تواند کلی نکته علمی برای یاد گرفتن داشته باشد. امروز چه چیزی درباره هوا یاد گرفتید؟",
    "اقلیم فقط عدد و نمودار نیست؛ بخشی از زندگی روزمره ماست. امروز اثرش را کجا بیشتر حس کردید؟ 🌍",
]


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


def fallback_caption() -> str:
    cache = _load_cache()
    used = set(cache.get("captions", []))
    choices = [item for item in DEFAULT_CAPTIONS if item not in used] or DEFAULT_CAPTIONS
    caption = random.choice(choices)
    history = list(cache.get("captions", []))
    history.append(caption)
    cache["captions"] = history[-40:]
    _save_cache(cache)
    return caption


def fetch_pexels_media(query: str = "climate weather nature") -> dict[str, Any]:
    api_key = os.getenv("PEXELS_API_KEY", "").strip()
    if not api_key:
        return _cached_media_or_fallback(query)
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
            return _cached_media_or_fallback(query)
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
        return _cached_media_or_fallback(query)


def _cached_media_or_fallback(query: str) -> dict[str, Any]:
    cache = _load_cache()
    return cache.get("media", {}).get(query, {"source": "fallback", "url": "", "photographer": None})


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


def generate_gemini_caption(topic: str) -> str:
    prompt = (
        "برای Instagram کلیماویدز یک کپشن فارسی عمیق، دقیق و واقعاً ارزشمند بنویس. "
        "موضوع را فقط تعریف نکن؛ علت یا سازوکار پدیده، پیامد یا کاربرد آن برای زندگی روزمره، و یک نکته مشخص و قابل فهم برای مخاطب ارائه کن. "
        "لحن کاملاً محاوره‌ای، گرم، صمیمی و طبیعی باشد؛ مثل یک هواشناس باتجربه یا علاقه‌مند جدی به اقلیم که با مخاطبش راحت صحبت می‌کند، نه مثل متن تبلیغاتی یا رباتیک. "
        "هیچ عدد یا ادعای علمی را بدون اطمینان نساز. از کلی‌گویی، کلیشه و پرگویی خودداری کن. "
        "در پایان، اگر طبیعی بود، یک سؤال کوتاه برای تشویق گفتگو بپرس. "
        f"موضوع: {topic}. حداکثر 1000 کاراکتر."
    )
    return _gemini_text(prompt) or fallback_caption()


def generate_gemini_reply(comment_text: str) -> str | None:
    prompt = (
        "برای کامنت زیر یک پاسخ کوتاه، گرم و کاملاً طبیعی به فارسی بنویس. "
        "پاسخ باید مشخصاً به محتوای همان کامنت مرتبط باشد، نکته‌ای واقعی و مفید اضافه کند یا سؤال مرتبطی بپرسد، "
        "و از لحن تبلیغاتی و جمله‌های تکراری دوری کند. حداکثر 220 کاراکتر.\n"
        f"کامنت: {comment_text}"
    )
    return _gemini_text(prompt, timeout=20)
