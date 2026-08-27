import unittest
from datetime import datetime
from unittest.mock import patch

from src import story_publisher


class TestStoryScheduling(unittest.TestCase):
    @patch("src.story_publisher.datetime")
    @patch("src.story_publisher.load_state")
    @patch("src.story_publisher.prepare_story")
    def test_story_is_skipped_after_recording(self, prepare_story, load_state, mocked_datetime):
        mocked_datetime.now.return_value = datetime(2026, 8, 23, 12, 0, tzinfo=story_publisher.IRAN_TZ)
        state = type("State", (), {"metadata": {"last_story_date": "2026-08-23"}})()
        load_state.return_value = state
        result = story_publisher.publish_daily_story()
        self.assertEqual(result, 0)
        prepare_story.assert_not_called()


if __name__ == "__main__":
    unittest.main()
