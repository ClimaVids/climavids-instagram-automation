"""Scheduled Instagram comment processor.

Phase 1 sends private replies only when explicitly taken out of DRY_RUN.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any

from instagram_client import InstagramAPIError, InstagramClient, dry_run_enabled
from state_manager import load_state, save_state

DEFAULT_REPLY = "ممنون از همراهی شما با کلیماویدز 🌱"


@dataclass(frozen=True)
class Comment:
    id: str
    text: str
    owner_has_replied: bool = False
    timestamp: str | None = None


def should_process(comment: Comment, processed_ids: set[str]) -> bool:
    return bool(comment.id and comment.text.strip() and comment.id not in processed_ids and not comment.owner_has_replied)


def draft_reply(comment: Comment) -> str:
    return DEFAULT_REPLY


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


def run() -> int:
    client = InstagramClient.from_env()
    client.check_and_warn_token()
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
