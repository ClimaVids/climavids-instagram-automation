import json
import unittest
from pathlib import Path


class ConfigTests(unittest.TestCase):
    def test_example_settings_are_valid_json(self):
        path = Path("config/settings.example.json")
        data = json.loads(path.read_text(encoding="utf-8"))
        self.assertTrue(data["dry_run"])
        self.assertEqual(data["comment_schedule_hours"], 4)
        self.assertEqual(data["token_expiry_warning_days"], 7)


if __name__ == "__main__":
    unittest.main()
