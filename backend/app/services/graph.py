"""
Graph validation and topological sort.

All workflow validation lives here — backend is the single source of truth.

validate_workflow() raises WorkflowValidationError with a list of human-readable
messages if the workflow is invalid.

topological_sort() returns node IDs in execution order.
"""

from __future__ import annotations

from collections import defaultdict, deque
from typing import Any

from app.models.workflow import WorkflowDefinition
from app.nodes.registry import NODE_REGISTRY, get_node

# Node types considered valid entry points
TRIGGER_TYPES = {"manual_trigger", "webhook_trigger"}
END_TYPES = {"end"}


class WorkflowValidationError(Exception):
    def __init__(self, errors: list[str]) -> None:
        self.errors = errors
        super().__init__("; ".join(errors))


def validate_workflow(workflow: WorkflowDefinition) -> None:
    """
    Validate the workflow graph.  Raises WorkflowValidationError if invalid.

    Rules enforced:
    - At least one trigger node
    - At least one end node
    - No cycles (must be a DAG)
    - No disconnected nodes (every non-trigger node reachable from trigger;
      every node with no outgoing edge is an end node)
    - All node types are registered
    - Decision nodes must have at least one branch connected
    - Each node's config must pass its own validate_config() check
    """
    errors: list[str] = []
    node_ids = {n.id for n in workflow.nodes}
    node_type_map = {n.id: n.type for n in workflow.nodes}

    # --- unknown node types ---
    for node in workflow.nodes:
        if node.type not in NODE_REGISTRY:
            errors.append(f"Unknown node type '{node.type}' on node '{node.id}'.")

    # --- trigger & end presence ---
    trigger_nodes = [n for n in workflow.nodes if n.type in TRIGGER_TYPES]
    end_nodes = [n for n in workflow.nodes if n.type in END_TYPES]

    if not trigger_nodes:
        errors.append("Workflow must have at least one trigger node (manual_trigger or webhook_trigger).")
    if not end_nodes:
        errors.append("Workflow must have at least one end node.")

    # --- edge validity ---
    for edge in workflow.edges:
        if edge.source_node_id not in node_ids:
            errors.append(f"Edge '{edge.id}' references unknown source node '{edge.source_node_id}'.")
        if edge.target_node_id not in node_ids:
            errors.append(f"Edge '{edge.id}' references unknown target node '{edge.target_node_id}'.")

    if errors:
        raise WorkflowValidationError(errors)

    # --- cycle detection (Kahn's algorithm) ---
    cycle_errors = _detect_cycles(workflow)
    if cycle_errors:
        errors.extend(cycle_errors)

    # --- disconnected nodes ---
    disconnected = _find_disconnected(workflow, trigger_nodes)
    for nid in disconnected:
        errors.append(
            f"Node '{nid}' (type: {node_type_map.get(nid)}) is disconnected — "
            "not reachable from any trigger node."
        )

    # --- decision nodes: at least one branch must be connected ---
    connected_handles = {(e.source_node_id, e.source_handle) for e in workflow.edges}
    for node in workflow.nodes:
        if node.type == "decision":
            true_connected  = (node.id, "true")  in connected_handles
            false_connected = (node.id, "false") in connected_handles
            if not true_connected and not false_connected:
                errors.append(
                    f"Decision node '{node.id}' has neither True nor False branch connected. "
                    "Connect at least one branch."
                )

    # --- per-node config validation ---
    for node in workflow.nodes:
        if node.type not in NODE_REGISTRY:
            continue  # already reported above
        try:
            get_node(node.type, node.id, node.config).validate_config()
        except (ValueError, TypeError) as exc:
            errors.append(f"Node '{node.id}' ({node.type}): invalid configuration — {exc}")

    if errors:
        raise WorkflowValidationError(errors)


def _detect_cycles(workflow: WorkflowDefinition) -> list[str]:
    """Return error messages if any cycles are found using Kahn's algorithm."""
    in_degree: dict[str, int] = {n.id: 0 for n in workflow.nodes}
    adj: dict[str, list[str]] = defaultdict(list)

    for edge in workflow.edges:
        adj[edge.source_node_id].append(edge.target_node_id)
        in_degree[edge.target_node_id] += 1

    queue = deque(nid for nid, deg in in_degree.items() if deg == 0)
    visited = 0

    while queue:
        node = queue.popleft()
        visited += 1
        for neighbor in adj[node]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)

    if visited != len(workflow.nodes):
        return ["Workflow contains a cycle. Only DAGs are supported."]
    return []


def _find_disconnected(workflow: WorkflowDefinition, trigger_nodes: list) -> list[str]:
    """Return node IDs not reachable from any trigger node via BFS."""
    adj: dict[str, list[str]] = defaultdict(list)
    for edge in workflow.edges:
        adj[edge.source_node_id].append(edge.target_node_id)

    visited: set[str] = set()
    queue = deque(n.id for n in trigger_nodes)
    while queue:
        nid = queue.popleft()
        if nid in visited:
            continue
        visited.add(nid)
        for neighbor in adj[nid]:
            queue.append(neighbor)

    all_ids = {n.id for n in workflow.nodes}
    return list(all_ids - visited)


def topological_sort(workflow: WorkflowDefinition) -> list[str]:
    """
    Return node IDs in topological (execution) order using Kahn's algorithm.
    Assumes the workflow has already been validated (no cycles).
    """
    in_degree: dict[str, int] = {n.id: 0 for n in workflow.nodes}
    adj: dict[str, list[str]] = defaultdict(list)

    for edge in workflow.edges:
        adj[edge.source_node_id].append(edge.target_node_id)
        in_degree[edge.target_node_id] += 1

    queue = deque(nid for nid, deg in in_degree.items() if deg == 0)
    order: list[str] = []

    while queue:
        nid = queue.popleft()
        order.append(nid)
        for neighbor in sorted(adj[nid]):  # sorted for determinism
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)

    return order


def build_adjacency(workflow: WorkflowDefinition) -> dict[str, list[dict]]:
    """
    Build an adjacency map: node_id → list of {target_node_id, source_handle}.
    Used by the workflow executor to route outputs correctly.
    """
    adj: dict[str, list[dict]] = defaultdict(list)
    for edge in workflow.edges:
        adj[edge.source_node_id].append({
            "target_node_id": edge.target_node_id,
            "source_handle": edge.source_handle,
        })
    return dict(adj)
