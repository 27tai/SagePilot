"""
Webhook Trigger node.

Entry point activated by an incoming HTTP POST to /api/webhooks/{workflow_id}.
Passes the request body payload downstream unchanged.

Config keys:
  (none required — the webhook URL is derived from the workflow_id at runtime)
"""

from __future__ import annotations

from typing import Any

from .base import BaseNode


class WebhookTriggerNode(BaseNode):
    node_type = "webhook_trigger"

    def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        # Payload is injected by the webhook endpoint at runtime — pass it through.
        return payload
