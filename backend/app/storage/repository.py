"""
In-memory workflow repository.

Swap this for a SQLite/Postgres implementation without touching any other layer —
the rest of the app depends only on the WorkflowRepository interface (get/save/list/delete).
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from app.models.workflow import WorkflowDefinition, WorkflowResult


class WorkflowRepository:
    """Thread-safe in-memory store for workflows and execution results."""

    def __init__(self) -> None:
        self._workflows: dict[str, WorkflowDefinition] = {}
        self._results: dict[str, list[WorkflowResult]] = {}  # workflow_id → runs

    # ------------------------------------------------------------------
    # Workflows
    # ------------------------------------------------------------------

    def save(self, workflow: WorkflowDefinition) -> WorkflowDefinition:
        workflow.updated_at = datetime.utcnow()
        self._workflows[workflow.id] = workflow
        return workflow

    def get(self, workflow_id: str) -> Optional[WorkflowDefinition]:
        return self._workflows.get(workflow_id)

    def list_all(self) -> list[WorkflowDefinition]:
        return list(self._workflows.values())

    def delete(self, workflow_id: str) -> bool:
        if workflow_id in self._workflows:
            del self._workflows[workflow_id]
            return True
        return False

    # ------------------------------------------------------------------
    # Execution results
    # ------------------------------------------------------------------

    def save_result(self, result: WorkflowResult) -> None:
        self._results.setdefault(result.workflow_id, []).append(result)

    def get_results(self, workflow_id: str) -> list[WorkflowResult]:
        return self._results.get(workflow_id, [])


# Module-level singleton — imported by the FastAPI app and the execution service
workflow_repo = WorkflowRepository()
