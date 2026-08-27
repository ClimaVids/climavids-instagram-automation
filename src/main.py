"""CLI entry point for the Phase 1 bot."""

from __future__ import annotations

import argparse

from .comment_handler import run as run_comment_cycle
from .content_publisher import publish_daily_content


def run_comments() -> int:
    return run_comment_cycle()


def run_daily_content() -> int:
    print(publish_daily_content())
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["comments", "daily-content"])
    args = parser.parse_args()
    return run_comments() if args.mode == "comments" else run_daily_content()


if __name__ == "__main__":
    raise SystemExit(main())
