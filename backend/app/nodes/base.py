"""
BaseNode — all node types inherit from this.

To add a new node type:
  1. Create a file in app/nodes/ (e.g. http_request.py)
  2. Subclass BaseNode and implement `execute()`
  3. Register it in app/nodes/registry.py with one line
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseNode(ABC):
    """
    Abstract base for every node type.

    `config` is the raw dict from NodeConfig.config — each subclass is
    responsible for reading/validating its own keys.
    """

    # Subclasses declare their node type string here (must match NodeType literal)
    node_type: str = ""

    def __init__(self, node_id: str, config: dict[str, Any]) -> None:
        self.node_id = node_id
        self.config = config

    @abstractmethod
    def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        """
        Process the incoming payload and return the output payload.

        Raise NodeExecutionError on unrecoverable failures.
        The activity layer catches it and records it in the execution log.
        """
        ...

    def validate_config(self) -> None:
        """
        Optional hook: validate self.config before execution.
        Raise ValueError with a human-readable message if invalid.
        """


class NodeExecutionError(Exception):
    """Raised by a node when it cannot complete its work."""
