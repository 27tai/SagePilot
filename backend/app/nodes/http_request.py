"""
HTTP Request node.

POSTs the entire incoming payload as a JSON body to a configured URL.

Config keys:
  url     (str):            destination URL (required)
  headers (dict, optional): extra request headers

Output: incoming payload merged with:
  http_status (int)  — response status code
  http_body   (any)  — parsed JSON response body, or raw text on parse failure
"""

from __future__ import annotations

from typing import Any

import httpx

from .base import BaseNode, NodeExecutionError


class HttpRequestNode(BaseNode):
    node_type = "http_request"

    def validate_config(self) -> None:
        if not self.config.get("url"):
            raise ValueError("HttpRequestNode: 'url' is required.")

    def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        self.validate_config()

        url: str = self.config["url"]
        headers: dict = self.config.get("headers") or {}

        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.post(url, json=payload, headers=headers)

            try:
                response_body = response.json()
            except Exception:
                response_body = response.text

            return {
                **payload,
                "http_status": response.status_code,
                "http_body": response_body,
            }

        except httpx.TimeoutException as exc:
            raise NodeExecutionError(
                f"HttpRequestNode: request to '{url}' timed out: {exc}"
            )
        except httpx.RequestError as exc:
            raise NodeExecutionError(
                f"HttpRequestNode: request to '{url}' failed: {exc}"
            )
