"""
Temporal Activities — one per node execution.

Each activity is a thin wrapper that:
  1. Instantiates the correct node class from the registry
  2. Calls node.execute(payload)
  3. Returns a structured result dict

Activities are the unit of retry in Temporal. Retry policies are set
at the workflow level when scheduling activities.
"""

from __future__ import annotations

from typing import Any

from temporalio import activity

from app.nodes.registry import get_node
from app.nodes.base import NodeExecutionError


@activity.defn(name="execute_node")
async def execute_node_activity(params: dict[str, Any]) -> dict[str, Any]:
    """
    Execute a single workflow node.

    Expected params keys:
      node_id   (str)
      node_type (str)
      config    (dict)
      payload   (dict)  — incoming data from the previous node

    Returns:
      {
        "node_id":        str,
        "node_type":      str,
        "output_payload": dict,
        "error":          str | None,
      }
    """
    node_id: str = params["node_id"]
    node_type: str = params["node_type"]
    config: dict = params.get("config", {})
    payload: dict = params.get("payload", {})

    logger = activity.logger
    logger.info("Executing node %s (type=%s)", node_id, node_type)

    try:
        node = get_node(node_type=node_type, node_id=node_id, config=config)
        output = node.execute(payload)
        logger.info("Node %s completed successfully", node_id)
        return {
            "node_id": node_id,
            "node_type": node_type,
            "output_payload": output,
            "error": None,
        }
    except NodeExecutionError as exc:
        logger.warning("Node %s execution error: %s", node_id, exc)
        return {
            "node_id": node_id,
            "node_type": node_type,
            "output_payload": payload,   # pass-through on error
            "error": str(exc),
        }
    except Exception as exc:
        logger.error("Node %s unexpected error: %s", node_id, exc, exc_info=True)
        raise  # Let Temporal handle retries for unexpected errors
