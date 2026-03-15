"""
Workflow API routes.

Endpoints:
  POST   /api/workflows                 — create workflow
  GET    /api/workflows                 — list all workflows
  GET    /api/workflows/{id}            — get workflow
  PUT    /api/workflows/{id}            — update workflow
  DELETE /api/workflows/{id}            — delete workflow
  GET    /api/workflows/{id}/export     — export as portable JSON
  POST   /api/workflows/import          — import from JSON
  POST   /api/workflows/{id}/run        — execute workflow via Temporal
  GET    /api/workflows/{id}/runs       — list execution history
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, status

from app.models.workflow import (
    WorkflowDefinition,
    RunWorkflowRequest,
    RunWorkflowResponse,
    WorkflowResult,
)
from app.services.graph import WorkflowValidationError
from app.services.execution import run_workflow
from app.storage.repository import workflow_repo

router = APIRouter(prefix="/api/workflows", tags=["workflows"])


# ---------------------------------------------------------------------------
# CRUD
# ---------------------------------------------------------------------------

@router.post("", response_model=WorkflowDefinition, status_code=status.HTTP_201_CREATED)
async def create_workflow(workflow: WorkflowDefinition) -> WorkflowDefinition:
    return workflow_repo.save(workflow)


@router.get("", response_model=list[WorkflowDefinition])
async def list_workflows() -> list[WorkflowDefinition]:
    return workflow_repo.list_all()


@router.get("/import", include_in_schema=False)
async def import_placeholder() -> dict:
    # Documented below — defined after to avoid route shadowing
    raise HTTPException(status_code=405, detail="Use POST /api/workflows/import")


@router.get("/{workflow_id}", response_model=WorkflowDefinition)
async def get_workflow(workflow_id: str) -> WorkflowDefinition:
    wf = workflow_repo.get(workflow_id)
    if not wf:
        raise HTTPException(status_code=404, detail=f"Workflow '{workflow_id}' not found.")
    return wf


@router.put("/{workflow_id}", response_model=WorkflowDefinition)
async def update_workflow(workflow_id: str, workflow: WorkflowDefinition) -> WorkflowDefinition:
    existing = workflow_repo.get(workflow_id)
    if not existing:
        raise HTTPException(status_code=404, detail=f"Workflow '{workflow_id}' not found.")
    workflow.id = workflow_id  # ensure ID consistency
    return workflow_repo.save(workflow)


@router.delete("/{workflow_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_workflow(workflow_id: str) -> None:
    if not workflow_repo.delete(workflow_id):
        raise HTTPException(status_code=404, detail=f"Workflow '{workflow_id}' not found.")


# ---------------------------------------------------------------------------
# Export / Import
# ---------------------------------------------------------------------------

@router.get("/{workflow_id}/export")
async def export_workflow(workflow_id: str) -> dict[str, Any]:
    wf = workflow_repo.get(workflow_id)
    if not wf:
        raise HTTPException(status_code=404, detail=f"Workflow '{workflow_id}' not found.")
    return wf.model_dump(mode="json")


@router.post("/import", response_model=WorkflowDefinition, status_code=status.HTTP_201_CREATED)
async def import_workflow(data: dict[str, Any]) -> WorkflowDefinition:
    """Import a previously exported workflow JSON."""
    try:
        wf = WorkflowDefinition(**data)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Invalid workflow JSON: {exc}")
    return workflow_repo.save(wf)


# ---------------------------------------------------------------------------
# Execution
# ---------------------------------------------------------------------------

@router.post("/{workflow_id}/run", response_model=WorkflowResult)
async def run_workflow_endpoint(workflow_id: str, body: RunWorkflowRequest) -> WorkflowResult:
    """
    Validate and execute a workflow via Temporal.
    Blocks until the workflow completes and returns the full execution log.
    """
    wf = workflow_repo.get(workflow_id)
    if not wf:
        raise HTTPException(status_code=404, detail=f"Workflow '{workflow_id}' not found.")

    try:
        result = await run_workflow(wf, trigger_payload=body.trigger_payload)
    except WorkflowValidationError as exc:
        raise HTTPException(
            status_code=422,
            detail={"message": "Workflow validation failed.", "errors": exc.errors},
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Execution error: {exc}")

    return result


@router.get("/{workflow_id}/runs", response_model=list[WorkflowResult])
async def list_runs(workflow_id: str) -> list[WorkflowResult]:
    """Return execution history for a workflow."""
    return workflow_repo.get_results(workflow_id)
