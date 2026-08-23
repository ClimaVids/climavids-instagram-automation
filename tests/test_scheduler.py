import os
import unittest
from datetime import datetime
from zoneinfo import ZoneInfo
from unittest.mock import patch

from src.content_publisher import content_slot, current_window, should_attempt_post
from src.comment_handler import DEFAULT_REPLIES, Comment, draft_reply, should_process


class TestScheduler(unittest.TestCase):
    def setUp(self) -> None:
        os.environ["RANDOM_POST_CHANCE"] = "70"

    def test_iran_morning_window(self) -> None:
        now = datetime(2026, 8, 23, 11, 0, tzinfo=ZoneInfo("Asia/Tehran"))
        self.assertEqual(current_window(now), "morning")
        self.assertEqual(content_slot(now), "2026-08-23:morning")

    def test_iran_evening_window(self) -> None:
        now = datetime(2026, 8, 23, 21, 0, tzinfo=ZoneInfo("Asia/Tehran"))
        self.assertEqual(current_window(now), "evening")

    def test_outside_window(self) -> None:
        now = datetime(2026, 8, 23, 14, 0, tzinfo=ZoneInfo("Asia/Tehran"))
        self.assertIsNone(current_window(now))
        self.assertFalse(should_attempt_post(now, 100))

    @patch("src.content_publisher.random.random", return_value=0.69)
    def test_probability_gate_accepts(self, _mock: object) -> None:
        now = datetime(2026, 8, 23, 11, 0, tzinfo=ZoneInfo("Asia/Tehran"))
        self.assertTrue(should_attempt_post(now, 70))

    @patch("src.content_publisher.random.random", return_value=0.70)
    def test_probability_gate_rejects(self, _mock: object) -> None:
        now = datetime(2026, 8, 23, 11, 0, tzinfo=ZoneInfo("Asia/Tehran"))
        self.assertFalse(should_attempt_post(now, 70))

    def test_twenty_default_replies(self) -> None:
        self.assertEqual(len(DEFAULT_REPLIES), 20)
        self.assertTrue(all(draft_reply(Comment("1", "hello"), use_ai=False) in DEFAULT_REPLIES for _ in range(5)))

    def test_comment_filter(self) -> None:
        self.assertFalse(should_process(Comment("", "hello"), set()))
        self.assertFalse(should_process(Comment("1", "hello", owner_has_replied=True), set()))
        self.assertFalse(should_process(Comment("1", "hello"), {"1"}))
        self.assertTrue(should_process(Comment("2", "hello"), set()))


if __name__ == "__main__":
    unittest.main()
