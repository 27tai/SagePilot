"""
Test script: run a workflow through Temporal and print full execution.

Workflow:  ManualTrigger → TransformData (uppercase) → TransformData (multiply) → End

Requirements before running:
  1. Temporal dev server running  (see instructions below)
  2. Worker running               (python -m app.temporal.worker)

Run:
  cd e:/Coding/SagePilot/backend
  python run_test_workflow.py
"""

from __future__ import annotations

import asyncio
import json
import os
import sys

# Make sure `app` package is importable when run from /backend
sys.path.insert(0, os.path.dirname(__file__))

from app.models.workflow import WorkflowDefinition, NodeConfig, EdgeConfig, Position
from app.services.execution import run_workflow

# ── ANSI colours ────────────────────────────────────────────────────────────
GREEN  = "\033[92m"
CYAN   = "\033[96m"
YELLOW = "\033[93m"
RED    = "\033[91m"
BOLD   = "\033[1m"
RESET  = "\033[0m"

NODE_COLOURS = {
    "manual_trigger": "\033[95m",   # magenta
    "transform_data": "\033[96m",   # cyan
    "end":            "\033[92m",   # green
}


def _pp(payload: dict) -> str:
    return json.dumps(payload, indent=2)


def print_header(title: str) -> None:
    bar = "─" * 60
    print(f"\n{BOLD}{bar}{RESET}")
    print(f"{BOLD}  {title}{RESET}")
    print(f"{BOLD}{bar}{RESET}\n")


def print_log(log: dict, index: int) -> None:
    node_type  = log["node_type"]
    node_id    = log["node_id"]
    colour     = NODE_COLOURS.get(node_type, CYAN)
    step       = log["step"]
    message    = log["message"]
    error      = log.get("error")
    inp        = log["input_payload"]
    out        = log["output_payload"]

    print(f"{BOLD}Step {step}{RESET}  {colour}[{node_type}]{RESET}  {YELLOW}{node_id[:8]}…{RESET}")
    print(f"  Message : {message}")
    if error:
        print(f"  {RED}Error   : {error}{RESET}")
    print(f"  Input  ↓")
    for line in _pp(inp).splitlines():
        print(f"    {line}")
    print(f"  Output ↑")
    for line in _pp(out).splitlines():
        print(f"    {line}")
    print()


def print_result(result) -> None:
    status_colour = GREEN if result.status == "completed" else RED
    print_header("Execution complete")
    print(f"  Workflow ID : {result.workflow_id}")
    print(f"  Run ID      : {result.run_id}")
    print(f"  Status      : {status_colour}{BOLD}{result.status.upper()}{RESET}")
    if result.error:
        print(f"  Error       : {RED}{result.error}{RESET}")

    print(f"\n{BOLD}Final output:{RESET}")
    if result.final_output:
        for line in _pp(result.final_output).splitlines():
            print(f"  {line}")
    else:
        print("  (none)")

    print(f"\n{BOLD}Full execution log:{RESET}\n")
    for log in result.logs:
        print_log(log if isinstance(log, dict) else log.model_dump(), log["step"] if isinstance(log, dict) else log.step)


# ── Build workflow ────────────────────────────────────────────────────────────

def build_workflow() -> WorkflowDefinition:
    trigger = NodeConfig(
        type="manual_trigger",
        config={
            "initial_payload": {"message": "hello world", "value": 5}
        },
        position=Position(x=100, y=200),
        label="Start",
    )

    transform_upper = NodeConfig(
        type="transform_data",
        config={
            "transformation": "uppercase",
            "field": "message",
        },
        position=Position(x=350, y=200),
        label="Uppercase message",
    )

    transform_multiply = NodeConfig(
        type="transform_data",
        config={
            "transformation": "multiply",
            "field": "value",
            "params": {"factor": 10},
        },
        position=Position(x=600, y=200),
        label="Multiply value ×10",
    )

    end = NodeConfig(
        type="end",
        config={},
        position=Position(x=850, y=200),
        label="End",
    )

    edges = [
        EdgeConfig(source_node_id=trigger.id,           target_node_id=transform_upper.id),
        EdgeConfig(source_node_id=transform_upper.id,   target_node_id=transform_multiply.id),
        EdgeConfig(source_node_id=transform_multiply.id, target_node_id=end.id),
    ]

    return WorkflowDefinition(
        name="Test Workflow",
        nodes=[trigger, transform_upper, transform_multiply, end],
        edges=edges,
    )


# ── Main ─────────────────────────────────────────────────────────────────────

async def main() -> None:
    workflow = build_workflow()
    trigger_payload = {"message": "hello world", "value": 5}

    print_header(f"Running workflow: {workflow.name}")
    print(f"  Nodes : {' → '.join(n.label or n.type for n in workflow.nodes)}")
    print(f"  Trigger payload : {trigger_payload}\n")

    try:
        result = await run_workflow(workflow, trigger_payload=trigger_payload)
    except Exception as exc:
        print(f"{RED}{BOLD}Failed to run workflow:{RESET} {exc}")
        sys.exit(1)

    print_result(result)


if __name__ == "__main__":
    asyncio.run(main())
