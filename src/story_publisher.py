"""Optional daily Story preparation based only on Iran seasonal forecasts."""

from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from free_content_services import fetch_pexels_media, generate_seasonal_caption
from seasonal_forecast_fetcher import seasonal_data_or_cache
from state_manager import load_state, save_state

DRY_RUN = True
STORY_ENABLED = True
IRAN_TZ = ZoneInfo("Asia/Tehran")


def prepare_story(season_key: str) -> dict[str, object] | None:
    forecast = seasonal_data_or_cache(season_key)
    if forecast.get("data_quality") != "numeric_or_mixed":
        return None
    text = generate_seasonal_caption(forecast)
    if not text:
        return None
    media = fetch_pexels_media("Iran seasonal climate forecast portrait")
    return {"season_key": season_key, "text": text, "media": media, "forecast": forecast}


def publish_daily_story() -> int:
    if not STORY_ENABLED:
        print("SKIP: daily Story feature is disabled.")
        return 0

    now = datetime.now(IRAN_TZ)
    state = load_state()
    today = now.date().isoformat()
    if state.metadata.get("last_story_date") == today:
        print("SKIP: today's Story has already been recorded.")
        return 0

    season_key = f"{now.year}-{now.month:02d}-seasonal-iran"
    story = prepare_story(season_key)
    if not story:
        print("SKIP: no current or cached numeric seasonal evidence is available; no generic Story will be produced.")
        return 0

    media = story.get("media")
    print(f"Seasonal Story media source: {media.get('source') if isinstance(media, dict) else 'unknown'}")
    print(f"Seasonal Story text: {story['text']}")

    if DRY_RUN:
        print("DRY-RUN: seasonal Story prepared but not published to Instagram.")
        return 0

    state.metadata["last_story_date"] = today
    state.metadata["last_forecast_season_key"] = season_key
    save_state(state)
    raise RuntimeError("Live Story publishing is disabled until explicit approval.")


if __name__ == "__main__":
    raise SystemExit(publish_daily_story())
