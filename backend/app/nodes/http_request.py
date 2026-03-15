"""
HTTP Request node.

Makes an outbound HTTP GET or POST request to a user-configured URL.

Config keys:
  url     (str):          destination URL (required)
  method  (str):          "GET" | "POST" (default: "GET")
  headers (dict):         extra request headers (optional)
  body    (dict):         JSON body for POST requests (optional)

The incoming payload is merged with the response so downstream nodes can
access both the original data and the HTTP response.

Output merges the incoming payload with:
  http_status (int):  response status code
  http_body   (any):  parsed JSON response body, or raw text on parse failure
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
        method = self.config.get("method", "GET").upper()
        if method not in ("GET", "POST"):
            raise ValueError(
                f"HttpRequestNode: unsupported method '{method}'. Use GET or POST."
            )

    def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        self.validate_config()

        url: str = self.config["url"]
        method: str = self.config.get("method", "GET").upper()
        headers: dict = self.config.get("headers") or {}
        body: Any = self.config.get("body") or None

        try:
            with httpx.Client(timeout=30.0) as client:
                if method == "GET":
                    response = client.get(url, headers=headers)
                else:
                    response = client.post(url, json=body, headers=headers)

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
