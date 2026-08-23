"""Safe, testable client for the Meta Instagram API.

Live writes remain disabled by DRY_RUN until explicitly approved.
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

import requests


class InstagramAPIError(RuntimeError):
    """Raised when Meta returns an API error."""


class TokenExpiryWarning(RuntimeError):
    """Raised when a token has less than the configured safe lifetime remaining."""


@dataclass(frozen=True)
class InstagramClient:
    access_token: str
    account_id: str
    api_version: str = "v23.0"
    graph_host: str = "https://graph.instagram.com"
    timeout: int = 30
    max_retries: int = 4

    @classmethod
    def from_env(cls) -> "InstagramClient":
        token = os.getenv("INSTAGRAM_ACCESS_TOKEN", "").strip()
        account_id = os.getenv("INSTAGRAM_BUSINESS_ACCOUNT_ID", "").strip()
        if not token:
            raise RuntimeError("INSTAGRAM_ACCESS_TOKEN is not configured")
        if not account_id:
            raise RuntimeError("INSTAGRAM_BUSINESS_ACCOUNT_ID is not configured")
        return cls(
            access_token=token,
            account_id=account_id,
            api_version=os.getenv("META_API_VERSION", "v23.0"),
            graph_host=os.getenv("META_GRAPH_HOST", "https://graph.instagram.com").rstrip("/"),
        )

    @property
    def base_url(self) -> str:
        return f"{self.graph_host}/{self.api_version}"

    def request(self, method: str, path: str, *, json_body: dict[str, Any] | None = None, **params: Any) -> dict[str, Any]:
        query = dict(params)
        query["access_token"] = self.access_token
        url = f"{self.base_url}/{path.lstrip('/')}"
        delay = 1.0

        for attempt in range(self.max_retries + 1):
            response = requests.request(
                method,
                url,
                params=query,
                json=json_body,
                timeout=self.timeout,
            )
            if response.ok:
                return response.json()

            try:
                payload = response.json()
            except ValueError:
                payload = {"raw": response.text}

            error_code = ((payload.get("error") or {}).get("code")) if isinstance(payload, dict) else None
            retryable = response.status_code in {408, 425, 429, 500, 502, 503, 504} or error_code == 4
            if not retryable or attempt >= self.max_retries:
                raise InstagramAPIError(f"Meta API {response.status_code}: {payload}")

            retry_after = response.headers.get("Retry-After")
            try:
                sleep_for = min(60.0, float(retry_after)) if retry_after else delay
            except ValueError:
                sleep_for = delay
            time.sleep(sleep_for)
            delay = min(60.0, delay * 2)

        raise AssertionError("unreachable")

    def get_page_id(self) -> str:
        """Validate and return the configured Professional Instagram account ID."""
        payload = self.request("GET", self.account_id, fields="id,username")
        returned_id = str(payload.get("id", "")).strip()
        if not returned_id:
            raise InstagramAPIError(f"Meta did not return an account id: {payload}")
        return returned_id

    def get_recent_comments(self, media_limit: int = 10, comments_per_media: int = 50) -> list[dict[str, Any]]:
        """Fetch recent comments from recent owned media.

        The API exposes comments from a media object. We therefore first fetch
        recent media IDs and then query each media's comments edge.
        """
        media = self.request(
            "GET",
            f"{self.account_id}/media",
            fields="id,timestamp,media_product_type",
            limit=media_limit,
        )
        comments: list[dict[str, Any]] = []
        for item in media.get("data", []):
            media_id = item.get("id")
            if not media_id:
                continue
            payload = self.request(
                "GET",
                f"{media_id}/comments",
                fields="id,text,from,timestamp,replies{id,from}",
                limit=comments_per_media,
            )
            for comment in payload.get("data", []):
                comment["media_id"] = media_id
                comment["owner_has_replied"] = self._owner_has_replied(comment)
                comments.append(comment)
        return comments

    def _owner_has_replied(self, comment: dict[str, Any]) -> bool:
        replies = (comment.get("replies") or {}).get("data", [])
        for reply in replies:
            author_id = str(((reply.get("from") or {}).get("id")) or "")
            if author_id and author_id == self.account_id:
                return True
        return False

    def send_private_reply(self, comment_id: str, message: str) -> dict[str, Any]:
        """Send one private reply to a comment.

        This endpoint is intentionally guarded by DRY_RUN in the caller. Meta
        documents the /messages endpoint with recipient.comment_id.
        """
        return self.request(
            "POST",
            f"{self.account_id}/messages",
            json_body={
                "recipient": {"comment_id": str(comment_id)},
                "message": {"text": message},
            },
        )

    def get_token_expiry(self) -> int | None:
        """Return the token expiry Unix timestamp when Meta can expose it.

        The Graph API debug_token endpoint requires an app access token. It is
        therefore optional in Phase 1; without it, this method returns None.
        """
        app_token = os.getenv("META_APP_ACCESS_TOKEN", "").strip()
        if not app_token:
            return None

        url = f"https://graph.facebook.com/{self.api_version}/debug_token"
        response = requests.get(
            url,
            params={"input_token": self.access_token, "access_token": app_token},
            timeout=self.timeout,
        )
        if not response.ok:
            raise InstagramAPIError(f"Token debug failed: {response.status_code}: {response.text}")
        payload = response.json().get("data", {})
        expiry = payload.get("expires_at")
        if expiry is None:
            expiry = payload.get("data_access_expiration_time")
        return int(expiry) if expiry is not None else None

    def check_and_warn_token(self, threshold_days: int = 7) -> int | None:
        """Fail the workflow when a known token expiry is within threshold_days."""
        expiry = self.get_token_expiry()
        if expiry is None:
            print("Token expiry could not be inspected because META_APP_ACCESS_TOKEN is not configured.")
            return None

        remaining = expiry - int(datetime.now(timezone.utc).timestamp())
        if remaining < 0:
            raise TokenExpiryWarning("Instagram/Meta access token has expired.")
        if remaining < threshold_days * 86400:
            raise TokenExpiryWarning(
                f"Instagram/Meta access token expires in {remaining / 86400:.2f} days; renew it now."
            )
        print(f"Token check OK: approximately {remaining / 86400:.1f} days remaining.")
        return expiry


def dry_run_enabled() -> bool:
    return os.getenv("DRY_RUN", "true").strip().lower() not in {"0", "false", "no"}
