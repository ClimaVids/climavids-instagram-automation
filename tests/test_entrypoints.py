import os
import unittest
from contextlib import redirect_stdout
from io import StringIO

from src.main import run_comments, run_daily_content


class EntrypointTests(unittest.TestCase):
    def test_comment_entrypoint_is_dry_run(self):
        old = os.environ.get("DRY_RUN")
        os.environ["DRY_RUN"] = "true"
        try:
            output = StringIO()
            with redirect_stdout(output):
                self.assertEqual(run_comments(), 0)
            self.assertIn("dry-run", output.getvalue().lower())
        finally:
            if old is None:
                os.environ.pop("DRY_RUN", None)
            else:
                os.environ["DRY_RUN"] = old

    def test_daily_entrypoint_is_dry_run(self):
        old = os.environ.get("DRY_RUN")
        os.environ["DRY_RUN"] = "true"
        try:
            self.assertEqual(run_daily_content(), 0)
        finally:
            if old is None:
                os.environ.pop("DRY_RUN", None)
            else:
                os.environ["DRY_RUN"] = old


if __name__ == "__main__":
    unittest.main()
