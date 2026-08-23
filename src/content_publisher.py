"""Daily content publishing boundary.

Phase 1 never publishes real Instagram content.
"""

DRY_RUN = True


def publish_daily_content() -> int:
    if DRY_RUN:
        print("DRY-RUN: در این مرحله هستیم و محتوای روزانه منتشر نمی‌شود؛ فقط اجرای فرضی انجام شد.")
        return 0
    raise RuntimeError("Live publishing is disabled until explicit Phase 1 approval.")


if __name__ == "__main__":
    raise SystemExit(publish_daily_content())
