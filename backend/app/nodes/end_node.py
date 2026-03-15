"""
End node.

Terminal node — receives the final processed payload and stores it.
Returns the payload unchanged so the workflow engine can record it.

Config keys: (none required)
"""

from __future__ import annotations

from typing import Any

from .base import BaseNode


class EndNode(BaseNode):
    node_type = "end"

    def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        # Pass-through: the engine marks this as the final output.
        return payload
