import unittest

from src.comment_handler import Comment, should_process
from src.state_manager import BotState


class StateTests(unittest.TestCase):
    def test_state_round_trip(self):
        original = BotState(comment_ids={"1", "2"}, last_run_at="2026-08-23T12:00:00+00:00", metadata={"example": True})
        restored = BotState.from_dict(original.to_dict())
        self.assertEqual(restored.comment_ids, original.comment_ids)
        self.assertEqual(restored.last_run_at, original.last_run_at)
        self.assertEqual(restored.metadata, original.metadata)

    def test_processed_comment_is_skipped(self):
        self.assertFalse(should_process(Comment("1", "hello"), {"1"}))

    def test_owner_reply_is_skipped(self):
        self.assertFalse(should_process(Comment("2", "hello", owner_has_replied=True), set()))

    def test_blank_comment_is_skipped(self):
        self.assertFalse(should_process(Comment("3", "  "), set()))


if __name__ == "__main__":
    unittest.main()
