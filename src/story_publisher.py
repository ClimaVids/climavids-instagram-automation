"""Optional daily Instagram Story preparation/publishing boundary."""

from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from free_content_services import fetch_pexels_media, generate_gemini_caption
from state_manager import load_state, save_state

DRY_RUN = True
STORY_ENABLED = True
IRAN_TZ = ZoneInfo("Asia/Tehran")


def prepare_story() -> dict[str, object]:
    topic = "یک نکته جذاب هواشناسی یا اقلیمی برای استوری امروز"
    media = fetch_pexels_media("weather sky climate portrait")
    text = generate_gemini_caption(topic)
    return {"topic": topic, "text": text, "media": media}


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

    story = prepare_story()
    media = story.get("media")
    print(f"Story media source: {media.get('source') if isinstance(media, dict) else 'unknown'}")
    print(f"Story text: {story['text']}")

    if DRY_RUN:
        print("DRY-RUN: Story prepared but not published to Instagram.")
        return 0

    state.metadata["last_story_date"] = today
    save_state(state)
    raise RuntimeError("Live Story publishing is disabled until explicit approval.")


if __name__ == "__main__":
    raise SystemExit(publish_daily_story())
