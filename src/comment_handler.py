"""Comment processing rules independent of the Instagram transport."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True)
class Comment:
    id: str
    text: str
    owner_has_replied: bool = False


def should_process(comment: Comment, processed_ids: set[str]) -> bool:
    if not comment.id or comment.id in processed_ids:
        return False
    if comment.owner_has_replied:
        return False
    return bool(comment.text.strip())


def draft_reply(comment: Comment, generator: Callable[[str], str] | None = None) -> str:
    """Return a conservative placeholder until the AI/reply policy is configured."""
    if generator:
        reply = generator(comment.text).strip()
        if reply:
            return reply
    return "ممنون که دیدگاهتان را با ما به اشتراک گذاشتید."
