"""Scheduled Instagram comment processor."""

from __future__ import annotations

import os
import random
import time
from dataclasses import dataclass
from typing import Any

from .free_content_services import generate_gemini_reply
from .instagram_client import InstagramAPIError, InstagramClient, dry_run_enabled
from .state_manager import load_state, save_state

DEFAULT_REPLIES = [
    "ممنون از همراهی شما با کلیماویدز 🌱",
    "خیلی ممنون که نظرتون رو با ما به اشتراک گذاشتید 🙏",
    "خوشحالیم که این مطلب براتون جالب بود 🌍",
    "ممنون که همراه کلیماویدز هستید؛ نظر شما برای ما مهمه.",
    "سپاس از شما 🌱 شما درباره این پدیده چه نظری دارید؟",
    "ممنون از توجه‌تون؛ امروز هوا در شهر شما چطوره؟ ☁️",
    "خیلی خوبه که این موضوع رو دنبال می‌کنید. تجربه شما چیه؟",
    "ممنون از کامنتتون 🌦️ شما این تغییر هوا رو چطور حس کردید؟",
    "سپاسگزاریم 🙏 به نظرتون این پدیده بیشتر در چه زمانی دیده می‌شه؟",
    "ممنون که نوشتید 🌍 شهر شما هم چنین شرایطی داشته؟",
    "از همراهی‌تون ممنونیم. شما بیشتر به کدوم پدیده جوی علاقه دارید؟",
    "مرسی از نظرتون 🌤️ امروز آسمان شهر شما چه شکلیه؟",
    "ممنون از پیام‌تون؛ تجربه شما می‌تونه برای بقیه هم جالب باشه.",
    "خیلی ممنون 🌱 اگر دوست داشتید بیشتر درباره‌اش بگید.",
    "سپاس از همراهی شما. به نظر خودتون دلیل این تغییر چی می‌تونه باشه؟",
    "ممنون که دیدگاهتون رو مطرح کردید 🌧️ در شهر شما هم همین اتفاق افتاده؟",
    "خوشحالیم که مشارکت کردید. امروز دمای شهر شما چند درجه بود؟ 🌡️",
    "مرسی از کامنتتون 🙏 دوست داریم تجربه محلی شما رو هم بدونیم.",
    "ممنون از شما 🌬️ وضعیت باد در شهر شما چطوره؟",
    "از اینکه همراه کلیماویدز هستید ممنونیم؛ منتظر تجربه و نظر شما هستیم. 🌍",
]


@dataclass(frozen=True)
class Comment:
    id: str
    text: str
    owner_has_replied: bool = False
    timestamp: str | None = None


def should_process(comment: Comment, processed_ids: set[str]) -> bool:
    return bool(comment.id and comment.text.strip() and comment.id not in processed_ids and not comment.owner_has_replied)


def draft_reply(comment: Comment, use_ai: bool | None = None) -> str:
    if use_ai is None:
        use_ai = os.getenv("ENABLE_AI_REPLIES", "true").strip().lower() not in {"0", "false", "no"}
    if use_ai:
        ai_reply = generate_gemini_reply(comment.text)
        if ai_reply and ai_reply.strip():
            return ai_reply.strip()
    return random.choice(DEFAULT_REPLIES)


def _as_comment(payload: dict[str, Any]) -> Comment:
    return Comment(
        id=str(payload.get("id", "")),
        text=str(payload.get("text", "")),
        owner_has_replied=bool(payload.get("owner_has_replied", False)),
        timestamp=payload.get("timestamp"),
    )


def _reply_with_backoff(client: InstagramClient, comment_id: str, message: str) -> dict[str, Any]:
    delay = 1.0
    for attempt in range(5):
        try:
            return client.send_private_reply(comment_id, message)
        except InstagramAPIError as exc:
            text = str(exc)
            rate_limited = "429" in text or "code': 4" in text or '"code": 4' in text
            if not rate_limited or attempt == 4:
                raise
            time.sleep(delay)
            delay *= 2
    raise RuntimeError("Unreachable retry state")


def _local_dry_run() -> int:
    sample = Comment(id="dry-run", text="این یک تست است")
    if should_process(sample, set()):
        print(f"DRY-RUN: would privately reply to {sample.id}: {draft_reply(sample)}")
    print("Comment cycle completed in safe local dry-run mode; no Instagram API call was made.")
    return 0


def run() -> int:
    token = os.getenv("INSTAGRAM_ACCESS_TOKEN", "").strip()
    account_id = os.getenv("INSTAGRAM_BUSINESS_ACCOUNT_ID", "").strip()
    if dry_run_enabled() and (not token or not account_id):
        return _local_dry_run()

    client = InstagramClient.from_env()
    if not dry_run_enabled():
        client.check_and_warn_token()
    else:
        print("DRY-RUN: Instagram reads are enabled; all comment replies remain blocked.")

    state = load_state()
    comments = client.get_recent_comments()
    processed_now = 0

    for payload in comments:
        comment = _as_comment(payload)
        if not should_process(comment, state.comment_ids):
            continue

        message = draft_reply(comment)
        if dry_run_enabled():
            print(f"DRY-RUN: would privately reply to {comment.id}: {message}")
        else:
            _reply_with_backoff(client, comment.id, message)
            print(f"Replied privately to comment {comment.id}")

        state.comment_ids.add(comment.id)
        processed_now += 1

    save_state(state)
    print(f"Comment cycle completed. Considered {len(comments)} comments; processed {processed_now}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
