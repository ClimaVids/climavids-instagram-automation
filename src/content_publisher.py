"""Daily Feed scheduler; one high-quality post per Iran-local day."""

from __future__ import annotations

import os
import random
from datetime import datetime, time
from zoneinfo import ZoneInfo

from free_content_services import fallback_caption, fetch_pexels_media, generate_gemini_caption
from state_manager import load_state, save_state

DRY_RUN = True
IRAN_TZ = ZoneInfo("Asia/Tehran")
WINDOWS = (
    ("morning", time(10, 0), time(12, 0)),
    ("evening", time(20, 0), time(22, 0)),
)


def current_window(now: datetime | None = None) -> str | None:
    now = now or datetime.now(IRAN_TZ)
    local_time = now.timetz().replace(tzinfo=None)
    for name, start, end in WINDOWS:
        if start <= local_time < end:
            return name
    return None


def should_attempt_post(now: datetime | None = None, chance_percent: int | None = None) -> bool:
    if current_window(now) is None:
        return False
    chance = chance_percent if chance_percent is not None else int(os.getenv("RANDOM_POST_CHANCE", "70"))
    chance = max(0, min(100, chance))
    return random.random() * 100 < chance


def prepare_content(topic: str = "آب‌وهوا و اقلیم امروز") -> dict[str, object]:
    media = fetch_pexels_media(topic)
    caption = generate_gemini_caption(topic)
    if not caption.strip():
        caption = fallback_caption()
    return {"topic": topic, "caption": caption, "media": media}


def publish_daily_content() -> int:
    now = datetime.now(IRAN_TZ)
    window = current_window(now)
    if window is None:
        print("SKIP: outside Iran publishing windows (10:00-12:00 or 20:00-22:00).")
        return 0

    state = load_state()
    today = now.date().isoformat()
    if state.metadata.get("last_feed_post_date") == today:
        print("SKIP: today's single Feed post has already been recorded.")
        return 0

    if not should_attempt_post(now):
        print(f"SKIP: inside {window}, but the {os.getenv('RANDOM_POST_CHANCE', '70')}% chance gate declined this run.")
        return 0

    content = prepare_content("توضیح عمیق و کاربردی درباره یک پدیده مهم هواشناسی یا اقلیمی")
    if DRY_RUN:
        print(f"DRY-RUN: one high-quality Feed post would be prepared in the {window} window.")
        print(f"Caption: {content['caption']}")
        media = content.get("media")
        print(f"Media source: {media.get('source') if isinstance(media, dict) else 'unknown'}")
        return 0

    state.metadata["last_feed_post_date"] = today
    save_state(state)
    raise RuntimeError("Live Feed publishing is disabled until explicit approval.")


if __name__ == "__main__":
    raise SystemExit(publish_daily_content())
