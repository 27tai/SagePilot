"""
Temporal Workflow — WorkflowOrchestrator.

Branch routing for Decision nodes:
  After a decision activity returns, `result["branch"]` is "true" or "false".
  We collect all descendants reachable only via the non-taken handle and add
  them to `skip_set`. Nodes in `skip_set` are logged as SKIPPED but not
  executed, so the payload flows only down the matching branch.
"""

from __future__ import annotations

from collections import deque
from datetime import timedelta
from typing import Any

from temporalio import workflow
from temporalio.common import RetryPolicy

with workflow.unsafe.imports_passed_through():
    from app.models.workflow import WorkflowDefinition
    from app.services.graph import topological_sort, build_adjacency
    from app.temporal.activities import execute_node_activity

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
        run_id: str = params.get("run_id", str(workflow.uuid4()))
        trigger_payload: dict = params.get("trigger_payload", {})
        wf_dict: dict = params["workflow_definition"]

        workflow.logger.info("WorkflowOrchestrator started — run_id=%s", run_id)

        wf = WorkflowDefinition(**wf_dict)

        exec_order: list[str] = topological_sort(wf)
        adjacency: dict[str, list[dict]] = build_adjacency(wf)
        node_map: dict[str, Any] = {n.id: n for n in wf.nodes}

        payload_store: dict[str, dict] = {}
        skip_set: set[str] = set()   # nodes on the non-taken decision branch
        logs: list[dict] = []
        step = 1

        for node_id in exec_order:
            node = node_map[node_id]

            # ── Skipped node (non-taken decision branch) ──────────────
            if node_id in skip_set:
                logs.append({
                    "step": step,
                    "node_id": node_id,
                    "node_type": node.type,
                    "input_payload": {},
                    "output_payload": {},
                    "message": "SKIPPED (non-taken branch)",
                    "error": None,
                })
                step += 1
                continue

            # ── Resolve input payload ──────────────────────────────────
            incoming = _resolve_input(node_id, adjacency, payload_store, trigger_payload, node.type)

            # ── Wait node: durable sleep via Temporal timer ────────────
            if node.type == "wait":
                duration: int = int(node.config.get("duration", 5))
                unit: str = node.config.get("unit", "seconds")
                duration_seconds = duration * 60 if unit == "minutes" else duration
                wait_msg = f"Waiting {duration} {unit}…"
                workflow.logger.info("Step %d — %s (wait) sleeping %ds", step, node_id, duration_seconds)
                await workflow.sleep(timedelta(seconds=duration_seconds))
                payload_store[node_id] = incoming
                logs.append({
                    "step": step,
                    "node_id": node_id,
                    "node_type": node.type,
                    "input_payload": incoming,
                    "output_payload": incoming,
                    "message": wait_msg,
                    "error": None,
                })
                step += 1
                continue

            # ── Execute as Temporal activity ───────────────────────────
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
            branch: str | None = result.get("branch")   # "true" | "false" | None
            payload_store[node_id] = output_payload

            # ── Branch routing for Decision nodes ──────────────────────
            if node.type == "decision" and branch:
                for edge_info in adjacency.get(node_id, []):
                    handle = edge_info.get("source_handle")
                    if handle and handle != branch:
                        # This edge leads to the non-taken branch — skip descendants
                        skip_set.update(
                            _collect_descendants(edge_info["target_node_id"], adjacency)
                        )

            logs.append({
                "step": step,
                "node_id": node_id,
                "node_type": node.type,
                "input_payload": incoming,
                "output_payload": output_payload,
                "message": _format_log_message(node.type, result.get("error"), branch),
                "error": result.get("error"),
            })
            workflow.logger.info("Step %d — %s (%s) done%s", step, node_id, node.type,
                                  f" [branch={branch}]" if branch else "")
            step += 1

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
# Helpers
# ---------------------------------------------------------------------------

def _collect_descendants(start_id: str, adjacency: dict[str, list[dict]]) -> set[str]:
    """
    BFS from start_id over adjacency — returns all reachable node IDs
    (including start_id). Used to mark the non-taken decision branch.
    """
    visited: set[str] = set()
    queue: deque[str] = deque([start_id])
    while queue:
        nid = queue.popleft()
        if nid in visited:
            continue
        visited.add(nid)
        for edge in adjacency.get(nid, []):
            queue.append(edge["target_node_id"])
    return visited


def _resolve_input(
    node_id: str,
    adjacency: dict[str, list[dict]],
    payload_store: dict[str, dict],
    trigger_payload: dict,
    node_type: str,
) -> dict:
    if node_type in ("manual_trigger", "webhook_trigger"):
        return trigger_payload

    parents = [
        src for src, targets in adjacency.items()
        if any(t["target_node_id"] == node_id for t in targets)
    ]
    if not parents:
        return trigger_payload

    for parent_id in reversed(parents):
        if parent_id in payload_store:
            return payload_store[parent_id]

    return trigger_payload


def _find_final_output(wf: WorkflowDefinition, payload_store: dict[str, dict]) -> dict | None:
    for node in wf.nodes:
        if node.type == "end" and node.id in payload_store:
            return payload_store[node.id]
    return None


def _format_log_message(
    node_type: str, error: str | None, branch: str | None = None
) -> str:
    if error:
        return f"ERROR: {error}"
    if node_type == "decision" and branch:
        return f"Condition evaluated → taking {branch.upper()} branch"
    labels = {
        "manual_trigger": "Trigger fired",
        "webhook_trigger": "Webhook trigger fired",
        "transform_data": "Transformation applied",
        "http_request": "HTTP request completed",
        "end": "Workflow completed",
    }
    return labels.get(node_type, f"Node '{node_type}' executed")
