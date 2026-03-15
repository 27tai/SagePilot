"""
Wait node.

Pauses workflow execution for a configurable duration.

IMPORTANT: The actual sleep is implemented via Temporal's workflow.sleep() primitive
inside WorkflowOrchestrator — NOT time.sleep() or any in-process delay.
This ensures the pause is durable and survives worker restarts.

This node's execute() is a simple pass-through and is never called as a
Temporal activity; the workflow handles the sleep directly.

Config keys:
  duration (int):  how long to wait (default: 5)
  unit     (str):  "seconds" | "minutes" (default: "seconds")
"""

from __future__ import annotations

from typing import Any

from .base import BaseNode


class WaitNode(BaseNode):
    node_type = "wait"

    def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        # Pass-through. Real durable sleep is workflow.sleep() in WorkflowOrchestrator.
        return payload
