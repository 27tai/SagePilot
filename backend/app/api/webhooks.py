"""
Webhook trigger endpoint.

POST /api/webhooks/{workflow_id}
  - Accepts any JSON body as the trigger payload
  - Starts a Temporal workflow execution asynchronously
  - Returns 202 Accepted with a run_id for polling

The workflow must contain a webhook_trigger node to be activated this way.
"""

from __future__ import annotations

import asyncio
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import JSONResponse

from app.models.workflow import WorkflowResult
from app.services.execution import run_workflow
from app.services.graph import WorkflowValidationError
from app.storage.repository import workflow_repo

router = APIRouter(prefix="/api/webhooks", tags=["webhooks"])


@router.post("/{workflow_id}", status_code=status.HTTP_202_ACCEPTED)
async def webhook_trigger(workflow_id: str, request: Request) -> JSONResponse:
    """
    Trigger a workflow via an incoming HTTP webhook.

    The request body (JSON) is passed as the trigger_payload.
    Execution runs asynchronously — returns a run_id immediately.
    """
    wf = workflow_repo.get(workflow_id)
    if not wf:
        raise HTTPException(status_code=404, detail=f"Workflow '{workflow_id}' not found.")

    # Ensure the workflow has a webhook_trigger node
    has_webhook = any(n.type == "webhook_trigger" for n in wf.nodes)
    if not has_webhook:
        raise HTTPException(
            status_code=422,
            detail="This workflow does not contain a webhook_trigger node.",
        )

    try:
        body: dict[str, Any] = await request.json()
    except Exception:
        body = {}

    run_id = str(uuid4())

    # Fire-and-forget: run in background so we can return 202 immediately
    asyncio.create_task(_run_and_store(wf, body, run_id))

    return JSONResponse(
        status_code=status.HTTP_202_ACCEPTED,
        content={"run_id": run_id, "workflow_id": workflow_id, "status": "accepted"},
    )


async def _run_and_store(wf: Any, payload: dict, run_id: str) -> None:
    """Background task: executes the workflow and persists the result."""
    try:
        await run_workflow(wf, trigger_payload=payload, run_id=run_id)
    except WorkflowValidationError:
        pass  # logged by the execution service
    except Exception:
        pass  # unexpected errors — Temporal will have its own logs
