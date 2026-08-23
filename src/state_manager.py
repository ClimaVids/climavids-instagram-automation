"""State interface for the dedicated state branch.

Phase 1 keeps the format deliberately small so the storage backend can be
replaced later without changing comment-handling logic.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any


@dataclass
class BotState:
    processed_comments: set[str] = field(default_factory=set)
    token_expiry_unix: int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "processed_comments": sorted(self.processed_comments),
            "token_expiry_unix": self.token_expiry_unix,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "BotState":
        return cls(
            processed_comments=set(str(x) for x in payload.get("processed_comments", [])),
            token_expiry_unix=payload.get("token_expiry_unix"),
            metadata=dict(payload.get("metadata", {})),
        )


def load_state(raw: str) -> BotState:
    if not raw.strip():
        return BotState()
    return BotState.from_dict(json.loads(raw))


def dump_state(state: BotState) -> str:
    return json.dumps(state.to_dict(), ensure_ascii=False, indent=2) + "\n"
