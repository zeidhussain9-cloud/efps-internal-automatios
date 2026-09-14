"""Reusable Slack transport for EFPS.

Business modules decide what to send and why. This module only handles Slack
transport and request primitives.
"""
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any

API_BASE = os.getenv("EFPS_SLACK_API_BASE", "https://slack.com/api")


class SlackError(RuntimeError):
    """A Slack transport or API error."""


@dataclass(frozen=True)
class SlackConfig:
    bot_token: str

    @classmethod
    def from_env(cls) -> "SlackConfig":
        token = os.getenv("SLACK_BOT_TOKEN", "").strip()
        if not token:
            raise SlackError("SLACK_BOT_TOKEN is not configured")
        return cls(bot_token=token)


class SlackClient:
    """Small dependency-free Slack Web API client.

    No EFPS business rules live here. Callers provide Slack method names and
    payloads, or use the small convenience methods below.
    """

    def __init__(self, config: SlackConfig | None = None, *, timeout: float = 15.0):
        self.config = config or SlackConfig.from_env()
        self.timeout = timeout

    def call(self, method: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        body = json.dumps(payload or {}).encode("utf-8")
        request = urllib.request.Request(
            f"{API_BASE.rstrip('/')}/{method}",
            data=body,
            headers={
                "Authorization": f"Bearer {self.config.bot_token}",
                "Content-Type": "application/json; charset=utf-8",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                data = json.loads(response.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise SlackError(f"Slack transport failed for {method}: {exc}") from exc
        if not data.get("ok"):
            raise SlackError(f"Slack API {method} failed: {data.get('error', 'unknown_error')}")
        return data

    def auth_test(self) -> dict[str, Any]:
        return self.call("auth.test")

    def post_message(self, channel: str, text: str, *, thread_ts: str | None = None,
                     blocks: list[dict[str, Any]] | None = None) -> str:
        payload: dict[str, Any] = {"channel": channel, "text": text}
        if thread_ts:
            payload["thread_ts"] = thread_ts
        if blocks:
            payload["blocks"] = blocks
        return str(self.call("chat.postMessage", payload)["ts"])

    def update_message(self, channel: str, ts: str, text: str,
                       *, blocks: list[dict[str, Any]] | None = None) -> None:
        payload: dict[str, Any] = {"channel": channel, "ts": ts, "text": text}
        if blocks:
            payload["blocks"] = blocks
        self.call("chat.update", payload)

    def replies(self, channel: str, ts: str) -> list[dict[str, Any]]:
        return list(self.call("conversations.replies", {"channel": channel, "ts": ts}).get("messages", []))

    def history(self, channel: str, *, limit: int = 100) -> list[dict[str, Any]]:
        return list(self.call("conversations.history", {"channel": channel, "limit": limit}).get("messages", []))

    def files_info(self, file_id: str) -> dict[str, Any]:
        return self.call("files.info", {"file": file_id})

    def conversations_info(self, channel: str) -> dict[str, Any]:
        return self.call("conversations.info", {"channel": channel})

    def users_info(self, user: str) -> dict[str, Any]:
        return self.call("users.info", {"user": user})

    def add_reaction(self, channel: str, timestamp: str, name: str = "white_check_mark") -> None:
        self.call("reactions.add", {"channel": channel, "timestamp": timestamp, "name": name})

    def pin(self, channel: str, timestamp: str) -> None:
        self.call("pins.add", {"channel": channel, "timestamp": timestamp})


def api_healthcheck() -> bool:
    """Return False rather than raising for an operational health probe."""
    try:
        SlackClient().auth_test()
    except SlackError:
        return False
    return True
