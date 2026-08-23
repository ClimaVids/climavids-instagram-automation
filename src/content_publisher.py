"""Daily content generation boundary.

Phase 1 never publishes real Instagram content. It may prepare a caption and
an optional Pexels asset for inspection, then stops at the publishing boundary.
"""

from __future__ import annotations

from free_content_services import fetch_pexels_media, generate_gemini_caption

DRY_RUN = True


def publish_daily_content() -> int:
    topic = "تغییرات آب‌وهوا و اثر آن بر زندگی روزمره"
    media = fetch_pexels_media("climate weather earth nature")
    caption = generate_gemini_caption(topic)

    print(f"Content source: {media['source']}")
    print(f"Caption: {caption}")
    if media.get("photographer"):
        print(f"Pexels photographer: {media['photographer']}")

    if DRY_RUN:
        print("DRY-RUN: در این مرحله هستیم و هیچ محتوای واقعی در اینستاگرام منتشر نمی‌شود.")
        print("DRY-RUN: همین محتوا برای انتشار روزانه آماده می‌شد.")
        return 0

    raise RuntimeError("Live publishing is disabled until explicit Phase 2 approval.")


if __name__ == "__main__":
    raise SystemExit(publish_daily_content())
