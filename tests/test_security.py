"""Security regression tests for configuration that carries access tokens."""

from __future__ import annotations

import unittest

from src.instagram_client import InstagramClient, validate_graph_host


class TestGraphHostValidation(unittest.TestCase):
    def test_allows_official_instagram_graph_host(self) -> None:
        self.assertEqual(
            validate_graph_host("https://graph.instagram.com"),
            "https://graph.instagram.com",
        )

    def test_allows_official_facebook_graph_host(self) -> None:
        self.assertEqual(
            validate_graph_host("https://graph.facebook.com/"),
            "https://graph.facebook.com",
        )

    def test_rejects_arbitrary_host(self) -> None:
        with self.assertRaises(ValueError):
            validate_graph_host("https://attacker.example.com")

    def test_rejects_host_with_path(self) -> None:
        with self.assertRaises(ValueError):
            validate_graph_host("https://graph.instagram.com/attacker")

    def test_rejects_credentials_in_url(self) -> None:
        with self.assertRaises(ValueError):
            validate_graph_host("https://token:secret@graph.instagram.com")

    def test_client_rejects_unsafe_host_at_construction(self) -> None:
        with self.assertRaises(ValueError):
            InstagramClient("token", "123", graph_host="https://attacker.example.com")


if __name__ == "__main__":
    unittest.main()
