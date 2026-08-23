"""Non-destructive Meta connectivity test.

The test is skipped when credentials are not present, so CI never requires
live credentials during normal development or forked pull requests.
"""

from __future__ import annotations

import os
import unittest

from src.instagram_client import InstagramClient


class TestMetaConnection(unittest.TestCase):
    def test_configured_connection_without_writes(self) -> None:
        token = os.getenv("INSTAGRAM_ACCESS_TOKEN", "").strip()
        account_id = os.getenv("INSTAGRAM_BUSINESS_ACCOUNT_ID", "").strip()
        if not token or not account_id:
            self.skipTest("Instagram credentials are not configured")

        client = InstagramClient.from_env()
        # Read-only validation: no comment retrieval, message sending, or publishing.
        returned_id = client.get_page_id()
        self.assertEqual(returned_id, account_id)


if __name__ == "__main__":
    unittest.main()
