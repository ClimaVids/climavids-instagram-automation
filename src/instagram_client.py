"""Small, testable client for the Meta Instagram Graph API.

Production calls stay disabled until the required environment variables are set.
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass
from typing import Any

import requests


class InstagramAPIError(RuntimeError):
    """Raised when Meta returns an API error."""


@dataclass(frozen=True)
class InstagramClient:
    access_token: str
    api_version: str = "v23.0"
    timeout: int = 30
    max_retries: int = 3

    @classmethod
    def from_env(cls) -> "InstagramClient":
        token = os.getenv("INSTAGRAM_ACCESS_TOKEN", "").strip()
        if not token:
            raise RuntimeError("INSTAGRAM_ACCESS_TOKEN is not configured")
        return cls(access_token=token, api_version=os.getenv("META_API_VERSION", "v23.0"))

    @property
    def base_url(self) -> str:
        return f"https://graph.facebook.com/{self.api_version}"

    def request(self, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        params = dict(kwargs.pop("params", {}) or {})
        params["access_token"] = self.access_token
        url = f"{self.base_url}/{path.lstrip('/')}"

        delay = 1.0
        for attempt in range(self.max_retries + 1):
            response = requests.request(method, url, params=params, timeout=self.timeout, **kwargs)
            if response.ok:
                return response.json()

            retryable = response.status_code in {429, 500, 502, 503, 504}
            if not retryable or attempt >= self.max_retries:
                try:
                    payload = response.json()
                except ValueError:
                    payload = {"raw": response.text}
                raise InstagramAPIError(f"Meta API {response.status_code}: {payload}")

            retry_after = response.headers.get("Retry-After")
            try:
                sleep_for = min(60.0, float(retry_after)) if retry_after else delay
            except ValueError:
                sleep_for = delay
            time.sleep(sleep_for)
            delay = min(60.0, delay * 2)

        raise AssertionError("unreachable")

    def get(self, path: str, **params: Any) -> dict[str, Any]:
        return self.request("GET", path, params=params)

    def post(self, path: str, **data: Any) -> dict[str, Any]:
        return self.request("POST", path, data=data)


def dry_run_enabled() -> bool:
    return os.getenv("DRY_RUN", "true").strip().lower() not in {"0", "false", "no"}
