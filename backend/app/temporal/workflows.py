"""
Temporal Workflow — WorkflowOrchestrator.

This is the main durable execution unit. It:
  1. Receives the full workflow definition + trigger payload
  2. Performs topological sort on the DAG
  3. Executes each node sequentially as a Temporal Activity
  4. Collects execution logs
  5. Returns a WorkflowResult

Design note: all graph logic runs inside the workflow function using
deterministic helpers (topological_sort, build_adjacency). No I/O here —
only activity scheduling and pure computation.

Extending for new node types (e.g. Decision, Wait):
  - Decision: after executing a node, check the output's branch choice
    and skip nodes not on the selected path.
  - Wait:  use `await asyncio.sleep()` — Temporal makes this durable.
  - This scaffold already passes `source_handle` through adjacency so
    branching support is wired in but not yet enforced.
"""

from __future__ import annotations

from datetime import timedelta
from typing import Any

from temporalio import workflow
from temporalio.common import RetryPolicy

with workflow.unsafe.imports_passed_through():
    # These imports run outside the sandbox — safe for pure Python modules
    from app.models.workflow import WorkflowDefinition, ExecutionLog
    from app.services.graph import topological_sort, build_adjacency, validate_workflow
    from app.temporal.activities import execute_node_activity

# Default retry policy applied to all node activities
DEFAULT_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)


@workflow.defn(name="WorkflowOrchestrator")
class WorkflowOrchestrator:
    """Durable workflow that executes a node DAG via Temporal activities."""

    @workflow.run
    async def run(self, params: dict[str, Any]) -> dict[str, Any]:
        """
        params keys:
          workflow_definition (dict): serialised WorkflowDefinition
          trigger_payload     (dict): initial data injected at the trigger node
          run_id              (str):  caller-generated run identifier
        """
        run_id: str = params.get("run_id", str(workflow.uuid4()))
        trigger_payload: dict = params.get("trigger_payload", {})
        wf_dict: dict = params["workflow_definition"]

        workflow.logger.info("WorkflowOrchestrator started — run_id=%s", run_id)

        # Reconstruct WorkflowDefinition inside the workflow
        wf = WorkflowDefinition(**wf_dict)

        # Build execution structures (pure, deterministic)
        exec_order: list[str] = topological_sort(wf)
        adjacency: dict[str, list[dict]] = build_adjacency(wf)
        node_map: dict[str, Any] = {n.id: n for n in wf.nodes}

        # payload_store[node_id] = the output payload produced by that node
        payload_store: dict[str, dict] = {}

        logs: list[dict] = []
        step = 1

        for node_id in exec_order:
            node = node_map[node_id]

            # Determine input payload for this node
            incoming = _resolve_input(node_id, adjacency, payload_store, trigger_payload, node.type)

            # Schedule the activity
            result: dict = await workflow.execute_activity(
                execute_node_activity,
                args=[{
                    "node_id": node_id,
                    "node_type": node.type,
                    "config": node.config,
                    "payload": incoming,
                }],
                start_to_close_timeout=timedelta(minutes=5),
                retry_policy=DEFAULT_RETRY_POLICY,
            )

            output_payload: dict = result["output_payload"]
            payload_store[node_id] = output_payload

            log_entry = {
                "step": step,
                "node_id": node_id,
                "node_type": node.type,
                "input_payload": incoming,
                "output_payload": output_payload,
                "message": _format_log_message(node.type, output_payload, result.get("error")),
                "error": result.get("error"),
            }
            logs.append(log_entry)
            workflow.logger.info("Step %d — %s (%s) done", step, node_id, node.type)
            step += 1

        # Final output is the payload from the last end node
        final_output = _find_final_output(wf, payload_store)

        return {
            "workflow_id": wf.id,
            "run_id": run_id,
            "status": "completed",
            "logs": logs,
            "final_output": final_output,
            "error": None,
        }


# ---------------------------------------------------------------------------
# Helpers (pure functions — safe inside Temporal workflow sandbox)
# ---------------------------------------------------------------------------

def _resolve_input(
    node_id: str,
    adjacency: dict[str, list[dict]],
    payload_store: dict[str, dict],
    trigger_payload: dict,
    node_type: str,
) -> dict:
    """
    Determine what payload a node receives.

    - Trigger nodes receive the trigger_payload directly.
    - Other nodes receive the output of their (first) parent node.
      For nodes with multiple parents (fan-in), the last written payload wins;
      this can be refined later if fan-in merge semantics are required.
    """
    if node_type in ("manual_trigger", "webhook_trigger"):
        return trigger_payload

    # Find parents: nodes that have an edge pointing to node_id
    parents = [
        src for src, targets in adjacency.items()
        if any(t["target_node_id"] == node_id for t in targets)
    ]

    if not parents:
        return trigger_payload  # fallback for disconnected nodes

    # Use the last available parent output
    for parent_id in reversed(parents):
        if parent_id in payload_store:
            return payload_store[parent_id]

    return trigger_payload


def _find_final_output(wf: WorkflowDefinition, payload_store: dict[str, dict]) -> dict | None:
    """Return the output payload from the first end node found."""
    for node in wf.nodes:
        if node.type == "end" and node.id in payload_store:
            return payload_store[node.id]
    return None


def _format_log_message(node_type: str, output: dict, error: str | None) -> str:
    if error:
        return f"ERROR: {error}"
    labels = {
        "manual_trigger": "Trigger fired",
        "transform_data": "Transformation applied",
        "end": "Workflow completed",
    }
    return labels.get(node_type, f"Node '{node_type}' executed")
