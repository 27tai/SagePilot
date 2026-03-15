"""
Pydantic models for workflow definitions.

A workflow is a DAG of nodes connected by edges.
- NodeConfig: describes a single node (type, id, config, position)
- EdgeConfig: a directed connection from one node to another
- WorkflowDefinition: the full graph (nodes + edges + metadata)
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal, Optional
from uuid import uuid4

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Node types — extend this Literal when adding new node types
# ---------------------------------------------------------------------------
NodeType = Literal[
    "manual_trigger",
    "webhook_trigger",
    "transform_data",
    "http_request",
    "send_email",
    "wait",
    "decision",
    "end",
]


class Position(BaseModel):
    x: float = 0.0
    y: float = 0.0


class NodeConfig(BaseModel):
    """Represents a single node in the workflow graph."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    type: NodeType
    # Node-specific configuration dict (validated per-node at execution time)
    config: dict[str, Any] = Field(default_factory=dict)
    # Canvas position — stored but not used by the engine
    position: Position = Field(default_factory=Position)
    label: Optional[str] = None


class EdgeConfig(BaseModel):
    """A directed edge from source_node → target_node."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    source_node_id: str
    target_node_id: str
    # For Decision nodes: which output handle this edge originates from
    # e.g. "true" | "false" | None (for non-branching nodes)
    source_handle: Optional[str] = None


class WorkflowDefinition(BaseModel):
    """Complete workflow: nodes + edges + metadata."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str = "Untitled Workflow"
    nodes: list[NodeConfig] = Field(default_factory=list)
    edges: list[EdgeConfig] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


# ---------------------------------------------------------------------------
# API request / response models
# ---------------------------------------------------------------------------

class RunWorkflowRequest(BaseModel):
    """Sent by the client to trigger a workflow run."""
    workflow_id: str
    # Optionally override the trigger payload inline
    trigger_payload: dict[str, Any] = Field(default_factory=dict)


class RunWorkflowResponse(BaseModel):
    workflow_id: str
    run_id: str
    status: str = "started"


class ExecutionLog(BaseModel):
    step: int
    node_id: str
    node_type: str
    input_payload: dict[str, Any]
    output_payload: dict[str, Any]
    message: str = ""
    error: Optional[str] = None


class WorkflowResult(BaseModel):
    workflow_id: str
    run_id: str
    status: Literal["completed", "failed"]
    logs: list[ExecutionLog]
    final_output: Optional[dict[str, Any]] = None
    error: Optional[str] = None
