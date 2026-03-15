"""
SQLite-backed workflow repository.

Workflows are persisted to `sagepilot.db` in the backend directory so they
survive server restarts. Execution results are kept in-memory only (they are
transient run logs, not user data worth persisting right now).

The public interface (save / get / list_all / delete / save_result / get_results)
is identical to the old in-memory version — nothing else in the codebase changes.
"""

from __future__ import annotations

import json
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from typing import Optional

from app.models.workflow import WorkflowDefinition, WorkflowResult

# Database file sits next to this file's package, one level up
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "sagepilot.db")


@contextmanager
def _conn():
    """Yield a sqlite3 connection with row_factory set."""
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    try:
        yield con
        con.commit()
    finally:
        con.close()


def _init_db() -> None:
    with _conn() as con:
        con.execute("""
            CREATE TABLE IF NOT EXISTS workflows (
                id         TEXT PRIMARY KEY,
                name       TEXT NOT NULL,
                data       TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)


class WorkflowRepository:
    """SQLite-backed store for workflows; in-memory store for run results."""

    def __init__(self) -> None:
        _init_db()
        self._results: dict[str, list[WorkflowResult]] = {}

    # ------------------------------------------------------------------
    # Workflows
    # ------------------------------------------------------------------

    def save(self, workflow: WorkflowDefinition) -> WorkflowDefinition:
        workflow.updated_at = datetime.utcnow()
        data = workflow.model_dump(mode="json")
        with _conn() as con:
            con.execute(
                """
                INSERT INTO workflows (id, name, data, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    name       = excluded.name,
                    data       = excluded.data,
                    updated_at = excluded.updated_at
                """,
                (
                    workflow.id,
                    workflow.name,
                    json.dumps(data),
                    workflow.created_at.isoformat(),
                    workflow.updated_at.isoformat(),
                ),
            )
        return workflow

    def get(self, workflow_id: str) -> Optional[WorkflowDefinition]:
        with _conn() as con:
            row = con.execute(
                "SELECT data FROM workflows WHERE id = ?", (workflow_id,)
            ).fetchone()
        if row is None:
            return None
        return WorkflowDefinition(**json.loads(row["data"]))

    def list_all(self) -> list[WorkflowDefinition]:
        with _conn() as con:
            rows = con.execute(
                "SELECT data FROM workflows ORDER BY updated_at DESC"
            ).fetchall()
        return [WorkflowDefinition(**json.loads(r["data"])) for r in rows]

    def delete(self, workflow_id: str) -> bool:
        with _conn() as con:
            cur = con.execute(
                "DELETE FROM workflows WHERE id = ?", (workflow_id,)
            )
        return cur.rowcount > 0

    # ------------------------------------------------------------------
    # Execution results (transient — in-memory only)
    # ------------------------------------------------------------------

    def save_result(self, result: WorkflowResult) -> None:
        self._results.setdefault(result.workflow_id, []).append(result)

    def get_results(self, workflow_id: str) -> list[WorkflowResult]:
        return self._results.get(workflow_id, [])


# Module-level singleton
workflow_repo = WorkflowRepository()
