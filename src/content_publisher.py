"""Daily Feed scheduler using official forecast charts."""

from __future__ import annotations

import os
import random
from datetime import datetime, time
from zoneinfo import ZoneInfo

from .free_content_services import generate_chart_caption
from .official_chart_engine import fetch_ecmwf_precipitation_chart
from .state_manager import load_state, save_state

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
    """Prepare an official ECMWF chart and a short audience-facing caption."""
    del season_key
    try:
        chart = fetch_ecmwf_precipitation_chart(area="ASIA", stats="ensm")
    except Exception as exc:
        print(f"SKIP: official ECMWF chart could not be retrieved ({type(exc).__name__}).")
        return None
    caption = generate_chart_caption(chart)
    if not caption:
        return None
    return {"chart": chart, "caption": caption}


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

    content = prepare_content(today)
    if not content:
        print("SKIP: no verified official forecast chart is available; no generic content will be produced.")
        return 0

    chart = content["chart"]
    if DRY_RUN:
        print(f"DRY-RUN: official forecast chart prepared in the {window} window.")
        print(f"Chart URL: {chart['chart_url']}")
        print(f"Image URL: {chart['image_url']}")
        print(f"Caption: {content['caption']}")
        return 0

    state.metadata["last_feed_post_date"] = today
    state.metadata["last_forecast_chart"] = chart
    save_state(state)
    raise RuntimeError("Live Feed publishing is disabled until explicit approval.")


if __name__ == "__main__":
    raise SystemExit(publish_daily_content())
