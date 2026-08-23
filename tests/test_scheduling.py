import os
import unittest
from datetime import datetime
from zoneinfo import ZoneInfo

from src.content_publisher import current_window, should_attempt_post


class TestScheduling(unittest.TestCase):
    tz = ZoneInfo("Asia/Tehran")

    def test_windows(self):
        self.assertEqual(current_window(datetime(2026, 8, 23, 10, 30, tzinfo=self.tz)), "morning")
        self.assertEqual(current_window(datetime(2026, 8, 23, 21, 15, tzinfo=self.tz)), "evening")
        self.assertIsNone(current_window(datetime(2026, 8, 23, 15, 0, tzinfo=self.tz)))

    def test_chance_boundaries(self):
        self.assertFalse(should_attempt_post(datetime(2026, 8, 23, 11, 0, tzinfo=self.tz), 0))
        self.assertTrue(should_attempt_post(datetime(2026, 8, 23, 11, 0, tzinfo=self.tz), 100))


if __name__ == "__main__":
    unittest.main()
