"""Daily Feed scheduler; one data-driven seasonal post per Iran-local day."""

from __future__ import annotations

import os
import random
from datetime import datetime, time
from zoneinfo import ZoneInfo

from free_content_services import fetch_pexels_media, generate_seasonal_caption
from seasonal_forecast_fetcher import seasonal_data_or_cache
from state_manager import load_state, save_state

DRY_RUN = True
IRAN_TZ = ZoneInfo("Asia/Tehran")
WINDOWS = (("morning", time(10, 0), time(12, 0)), ("evening", time(20, 0), time(22, 0)))


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
    return random.random() * 100 < max(0, min(100, chance))


def prepare_content(season_key: str) -> dict[str, object] | None:
    forecast = seasonal_data_or_cache(season_key)
    if forecast.get("data_quality") == "none":
        return None
    caption = generate_seasonal_caption(forecast)
    if not caption:
        return None
    media = fetch_pexels_media("Iran seasonal forecast climate map")
    return {"season_key": season_key, "forecast": forecast, "caption": caption, "media": media}


def publish_daily_content() -> int:
    now = datetime.now(IRAN_TZ)
    window = current_window(now)
    if window is None:
        print("SKIP: outside Iran seasonal publishing windows (10:00-12:00 or 20:00-22:00).")
        return 0

    state = load_state()
    today = now.date().isoformat()
    if state.metadata.get("last_feed_post_date") == today:
        print("SKIP: today's single Feed post has already been recorded.")
        return 0
    if not should_attempt_post(now):
        print(f"SKIP: inside {window}, but the {os.getenv('RANDOM_POST_CHANCE', '70')}% chance gate declined this run.")
        return 0

    season_key = f"{now.year}-{now.month:02d}-seasonal-iran"
    content = prepare_content(season_key)
    if not content:
        print("SKIP: no validated current or cached seasonal forecast data is available; no generic content will be produced.")
        return 0

    if DRY_RUN:
        print(f"DRY-RUN: seasonal Feed post for Iran would be prepared in the {window} window.")
        print(f"Season key: {content['season_key']}")
        print(f"Caption: {content['caption']}")
        return 0

    state.metadata["last_feed_post_date"] = today
    state.metadata["last_forecast_season_key"] = season_key
    save_state(state)
    raise RuntimeError("Live Feed publishing is disabled until explicit approval.")


if __name__ == "__main__":
    raise SystemExit(publish_daily_content())
