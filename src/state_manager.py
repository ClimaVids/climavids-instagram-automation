"""Runtime state stored on the dedicated `state` branch."""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

STATE_BRANCH = os.getenv("STATE_BRANCH", "state")
STATE_FILE = os.getenv("STATE_FILE", "state.json")


@dataclass
class BotState:
    comment_ids: set[str] = field(default_factory=set)
    last_run_at: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "BotState":
        ids = payload.get("comment_ids", payload.get("processed_comments", []))
        return cls(
            comment_ids={str(x) for x in ids},
            last_run_at=payload.get("last_run_at"),
            metadata=dict(payload.get("metadata", {})),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "comment_ids": sorted(self.comment_ids),
            "last_run_at": self.last_run_at,
            "metadata": self.metadata,
        }


def _run(*args: str, cwd: str | Path | None = None) -> str:
    result = subprocess.run(args, cwd=cwd, check=True, capture_output=True, text=True)
    return result.stdout.strip()


def load_state() -> BotState:
    """Read state.json from the remote `state` branch without changing the worktree."""
    try:
        _run("git", "fetch", "origin", f"{STATE_BRANCH}:refs/remotes/origin/{STATE_BRANCH}")
        raw = _run("git", "show", f"origin/{STATE_BRANCH}:{STATE_FILE}")
    except subprocess.CalledProcessError:
        return BotState()
    if not raw.strip():
        return BotState()
    return BotState.from_dict(json.loads(raw))


def save_state(new_data: BotState | dict[str, Any]) -> None:
    """Commit state atomically on the dedicated state branch and push it."""
    state = new_data if isinstance(new_data, BotState) else BotState.from_dict(new_data)
    state.last_run_at = datetime.now(timezone.utc).isoformat()

    with tempfile.TemporaryDirectory(prefix="climavids-state-") as tmp:
        worktree = Path(tmp) / "state-worktree"
        _run("git", "fetch", "origin", STATE_BRANCH)
        _run("git", "worktree", "add", "--detach", str(worktree), f"origin/{STATE_BRANCH}")
        try:
            (worktree / STATE_FILE).write_text(
                json.dumps(state.to_dict(), ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            _run("git", "config", "user.name", "github-actions[bot]", cwd=worktree)
            _run("git", "config", "user.email", "41898282+github-actions[bot]@users.noreply.github.com", cwd=worktree)
            _run("git", "add", STATE_FILE, cwd=worktree)
            status = subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=worktree)
            if status.returncode == 0:
                return
            _run("git", "commit", "-m", "Update runtime state", cwd=worktree)
            _run("git", "push", "origin", f"HEAD:{STATE_BRANCH}", cwd=worktree)
        finally:
            subprocess.run(["git", "worktree", "remove", "--force", str(worktree)], check=False, capture_output=True, text=True)
