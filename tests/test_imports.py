import unittest


class ImportTests(unittest.TestCase):
    def test_core_modules_import(self):
        from src.instagram_client import InstagramClient
        from src.state_manager import BotState
        from src.comment_handler import Comment
        from src.content_publisher import publish_daily_content

        self.assertTrue(InstagramClient)
        self.assertTrue(BotState)
        self.assertTrue(Comment)
        self.assertTrue(publish_daily_content)


if __name__ == "__main__":
    unittest.main()
