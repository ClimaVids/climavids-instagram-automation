"""Daily content publishing boundary.

Phase 1 intentionally stays in dry-run mode; real media creation/publication
will be implemented only after the Meta account and publishing permissions are
verified.
"""

from __future__ import annotations

import os


def publish_daily_content() -> dict[str, object]:
    dry_run = os.getenv("DRY_RUN", "true").strip().lower() not in {"0", "false", "no"}
    if dry_run:
        return {"status": "dry-run", "published": False}
    raise RuntimeError("Live publishing is not enabled in Phase 1")
