"""
Execution service — bridges the API layer and Temporal.

Responsibilities:
  1. Validate the workflow graph
  2. Start a Temporal workflow execution
  3. Wait for (or poll) the result and persist it
"""

from __future__ import annotations

import os
import uuid
from typing import Any

from temporalio.client import Client

from app.models.workflow import WorkflowDefinition, WorkflowResult, ExecutionLog
from app.services.graph import validate_workflow, WorkflowValidationError
from app.storage.repository import workflow_repo
from app.temporal.workflows import WorkflowOrchestrator


async def _get_temporal_client() -> Client:
    host = os.getenv("TEMPORAL_HOST", "localhost:7233")
    namespace = os.getenv("TEMPORAL_NAMESPACE", "default")
    return await Client.connect(host, namespace=namespace)


async def run_workflow(
    workflow: WorkflowDefinition,
    trigger_payload: dict[str, Any],
    run_id: str | None = None,
) -> WorkflowResult:
    """
    Validate, submit to Temporal, await result, persist and return it.

    Raises WorkflowValidationError if the graph is invalid.
    """
    # 1. Validate
    validate_workflow(workflow)

    run_id = run_id or str(uuid.uuid4())
    task_queue = os.getenv("TEMPORAL_TASK_QUEUE", "workflow-engine")

    # 2. Connect and start workflow
    client = await _get_temporal_client()

    handle = await client.start_workflow(
        WorkflowOrchestrator.run,
        args=[{
            "workflow_definition": workflow.model_dump(mode="json"),
            "trigger_payload": trigger_payload,
            "run_id": run_id,
        }],
        id=f"wf-{workflow.id}-{run_id}",
        task_queue=task_queue,
    )

    # 3. Await result (blocks until the workflow completes)
    raw: dict = await handle.result()

    # 4. Parse into typed result
    result = WorkflowResult(
        workflow_id=raw["workflow_id"],
        run_id=raw["run_id"],
        status=raw["status"],
        logs=[ExecutionLog(**log) for log in raw["logs"]],
        final_output=raw.get("final_output"),
        error=raw.get("error"),
    )

    # 5. Persist
    workflow_repo.save_result(result)

    return result
