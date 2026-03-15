"""
Temporal Worker process.

Run this alongside the FastAPI server:
    python -m app.temporal.worker

The worker polls the task queue and executes workflow + activity code.
"""

from __future__ import annotations

import asyncio
import logging
import os

from temporalio.client import Client
from temporalio.worker import Worker

from app.temporal.workflows import WorkflowOrchestrator
from app.temporal.activities import execute_node_activity

logger = logging.getLogger(__name__)


async def run_worker() -> None:
    temporal_host = os.getenv("TEMPORAL_HOST", "localhost:7233")
    temporal_namespace = os.getenv("TEMPORAL_NAMESPACE", "default")
    task_queue = os.getenv("TEMPORAL_TASK_QUEUE", "workflow-engine")

    logger.info("Connecting to Temporal at %s (namespace=%s)", temporal_host, temporal_namespace)

    client = await Client.connect(temporal_host, namespace=temporal_namespace)

    worker = Worker(
        client,
        task_queue=task_queue,
        workflows=[WorkflowOrchestrator],
        activities=[execute_node_activity],
    )

    logger.info("Worker started — task queue: %s", task_queue)
    await worker.run()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run_worker())
