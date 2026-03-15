"""
Manual Trigger node.

Entry point of a workflow. Accepts an initial JSON payload from the user
and passes it downstream unchanged. The actual payload is injected at
execution time via the trigger_payload field on the run request —
this node simply passes it through.

Config keys:
  initial_payload (dict, optional): default payload used if no trigger_payload
                                    is provided at runtime.
"""

from __future__ import annotations

from typing import Any

from .base import BaseNode


class ManualTriggerNode(BaseNode):
    node_type = "manual_trigger"

    def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        # The payload is already set by the caller (trigger_payload from run request).
        # If payload is empty, fall back to the configured initial_payload.
        if not payload:
            return dict(self.config.get("initial_payload", {}))
        return payload
