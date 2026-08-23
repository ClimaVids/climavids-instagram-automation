import unittest

from src.state_manager import BotState, dump_state, load_state
from src.comment_handler import Comment, should_process


class StateTests(unittest.TestCase):
    def test_state_round_trip(self):
        original = BotState(processed_comments={"1", "2"}, token_expiry_unix=123)
        restored = load_state(dump_state(original))
        self.assertEqual(restored.processed_comments, original.processed_comments)
        self.assertEqual(restored.token_expiry_unix, 123)

    def test_processed_comment_is_skipped(self):
        self.assertFalse(should_process(Comment("1", "hello"), {"1"}))

    def test_owner_reply_is_skipped(self):
        self.assertFalse(should_process(Comment("2", "hello", owner_has_replied=True), set()))

    def test_blank_comment_is_skipped(self):
        self.assertFalse(should_process(Comment("3", "  "), set()))


if __name__ == "__main__":
    unittest.main()
