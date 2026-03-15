# SagePilot — Workflow Automation Engine

A full-stack, visual workflow automation engine inspired by n8n and Zapier. Users drag and connect nodes onto a canvas to build multi-step automation pipelines. Every workflow is executed durably through Temporal — surviving worker restarts, supporting long waits, and guaranteeing at-least-once delivery for every step.

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Tech Stack](#tech-stack)
3. [Project Structure](#project-structure)
4. [Node Types](#node-types)
5. [Setup & Running Locally](#setup--running-locally)
6. [Environment Variables](#environment-variables)
7. [API Documentation](#api-documentation)
8. [Workflow Execution — How Temporal Is Used](#workflow-execution--how-temporal-is-used)
9. [DAG Validation Rules](#dag-validation-rules)
10. [Design Decisions & Trade-offs](#design-decisions--trade-offs)

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        Browser (Next.js)                        │
│                                                                 │
│  ┌──────────┐  ┌─────────────┐  ┌───────────┐  ┌───────────┐  │
│  │  Node    │  │  React Flow │  │  Config   │  │Execution  │  │
│  │ Palette  │  │   Canvas    │  │  Panel    │  │  Panel    │  │
│  └──────────┘  └─────────────┘  └───────────┘  └───────────┘  │
│                      Zustand Store                              │
└───────────────────────────┬─────────────────────────────────────┘
                            │ REST (JSON)
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    FastAPI Backend (:8000)                       │
│                                                                 │
│  POST /api/workflows/{id}/run                                   │
│  POST /api/webhooks/{id}          validate_workflow()           │
│  GET/POST /api/workflows/…        graph.py (DAG checks)         │
│                                                                 │
│  WorkflowRepository (in-memory)                                 │
└───────────────────────────┬─────────────────────────────────────┘
                            │ Temporal SDK (gRPC :7233)
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Temporal Server (:7233)                       │
│                                                                 │
│   Durable task queue — persists workflow state, timers,         │
│   retries, and activity results across worker restarts.         │
└───────────────────────────┬─────────────────────────────────────┘
                            │ polls task queue
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│              Temporal Worker (Python process)                   │
│                                                                 │
│  WorkflowOrchestrator          execute_node_activity            │
│  ├── topological sort          ├── ManualTriggerNode            │
│  ├── asyncio.sleep() for Wait  ├── WebhookTriggerNode           │
│  └── branch routing for        ├── TransformDataNode            │
│       Decision nodes           ├── HttpRequestNode              │
│                                ├── SendEmailNode                │
│                                ├── WaitNode (pass-through)      │
│                                ├── DecisionNode                 │
│                                └── EndNode                      │
└─────────────────────────────────────────────────────────────────┘
```

### Key architectural principle

The **frontend is a pure presentation layer** — it only renders state and sends REST requests. All workflow logic (graph traversal, validation, execution ordering, branching, waiting) lives exclusively in the Python backend and Temporal worker.

### Request flow for a manual run

1. User clicks **Run** in the browser
2. Frontend `POST /api/workflows/{id}/run` with `trigger_payload`
3. FastAPI validates the DAG (`validate_workflow`)
4. FastAPI calls `client.start_workflow(WorkflowOrchestrator.run, ...)` — hands off to Temporal
5. Temporal durably records the workflow start and schedules activities on the task queue
6. The worker polls, picks up activities, executes each node in topological order
7. Each node's output becomes the next node's input
8. The final result is returned to FastAPI, which returns it to the browser

### Request flow for a webhook trigger

1. External system sends `POST /api/webhooks/{workflow_id}` with a JSON body
2. FastAPI returns **202 Accepted** immediately with a `run_id`
3. Workflow executes asynchronously in the background via Temporal
4. Results can be polled via `GET /api/workflows/{id}/runs`

---

## Tech Stack

| Layer | Technology | Why |
|---|---|---|
| **Frontend framework** | Next.js 14 (App Router) | SSR support, file-based routing, fast DX |
| **Styling** | Tailwind CSS | Utility-first, no runtime cost, consistent design |
| **Canvas** | React Flow v11 | Purpose-built for node graphs; handles drag, connect, zoom |
| **State management** | Zustand | Minimal boilerplate, works naturally with React Flow's mutable state |
| **Backend framework** | FastAPI | Async-first, automatic OpenAPI docs, Pydantic integration |
| **Orchestration** | Temporal (Python SDK `temporalio`) | Durable execution — workflows survive crashes, support long timers, automatic retries |
| **Data validation** | Pydantic v2 | Strict schema enforcement on all API boundaries |
| **HTTP client** | httpx | Async-compatible, clean API for outbound requests |
| **Email** | Python `smtplib` (stdlib) | No extra dependency; supports any SMTP provider |
| **Persistence** | In-memory (Python dict) | Sufficient for the scope; swap for SQLite/Postgres trivially |

---

## Project Structure

```
SagePilot/
├── backend/
│   ├── app/
│   │   ├── main.py                  # FastAPI app, CORS, router registration
│   │   ├── models/
│   │   │   └── workflow.py          # Pydantic models: NodeConfig, EdgeConfig, WorkflowDefinition
│   │   ├── nodes/
│   │   │   ├── base.py              # BaseNode ABC — all nodes inherit this
│   │   │   ├── registry.py          # NODE_REGISTRY dict + get_node() factory
│   │   │   ├── manual_trigger.py
│   │   │   ├── webhook_trigger.py
│   │   │   ├── transform_data.py
│   │   │   ├── http_request.py
│   │   │   ├── send_email.py
│   │   │   ├── wait_node.py
│   │   │   ├── decision.py
│   │   │   └── end_node.py
│   │   ├── services/
│   │   │   ├── graph.py             # DAG validation + topological sort
│   │   │   └── execution.py         # Connects to Temporal, starts workflow, awaits result
│   │   ├── temporal/
│   │   │   ├── workflows.py         # WorkflowOrchestrator — DAG traversal, branching, wait
│   │   │   ├── activities.py        # execute_node_activity — calls node.execute()
│   │   │   └── worker.py            # Worker process entry point
│   │   ├── storage/
│   │   │   └── repository.py        # In-memory WorkflowRepository
│   │   └── api/
│   │       ├── workflows.py         # CRUD + run + export/import endpoints
│   │       └── webhooks.py          # POST /api/webhooks/{workflow_id}
│   ├── requirements.txt
│   └── .env
│
└── frontend/
    └── src/
        ├── app/
        │   └── page.tsx             # Dynamic import of WorkflowEditor (SSR disabled)
        ├── types/
        │   └── workflow.ts          # TypeScript types mirroring backend Pydantic models
        ├── lib/
        │   ├── api.ts               # saveWorkflow, runWorkflow, listWorkflows, deleteWorkflow
        │   └── rfAdapters.ts        # Convert between React Flow format ↔ backend format
        ├── store/
        │   └── workflowStore.ts     # Zustand store — all editor state + actions
        └── components/
            ├── WorkflowEditor.tsx   # Top-level layout shell
            ├── Toolbar.tsx          # Workflow name, Save, Run buttons
            ├── sidebar/
            │   └── NodePalette.tsx  # Draggable node type chips
            ├── canvas/
            │   ├── FlowCanvas.tsx   # ReactFlow canvas + drop handler
            │   └── nodes/           # One component per node type
            └── panels/
                ├── ConfigPanel.tsx  # Per-node config forms (right sidebar)
                └── ExecutionPanel.tsx # Execution logs display
```

---

## Node Types

| Node | Type string | Role | Config fields |
|---|---|---|---|
| Manual Trigger | `manual_trigger` | Entry point — user clicks Run | `initial_payload` (JSON) |
| Webhook Trigger | `webhook_trigger` | Entry point — incoming HTTP POST | *(none — URL shown read-only)* |
| Transform Data | `transform_data` | Mutates a field in the payload | `transformation`, `field`, `params` |
| HTTP Request | `http_request` | POSTs payload to an external URL | `url`, `headers` |
| Send Email | `send_email` | Emails payload as JSON to a recipient | `to`, `subject` |
| Wait | `wait` | Pauses execution (Temporal durable timer) | `duration`, `unit` |
| Decision | `decision` | Routes to True or False branch | `field`, `operator`, `value` |
| End | `end` | Terminal node — stores final output | *(none)* |

### Decision operators

`equals` · `not_equals` · `greater_than` · `less_than` · `contains` · `is_empty`

### Transform types

`uppercase` · `append_text` · `prepend_text` · `multiply` · `rename_key`

---

## Setup & Running Locally

### Prerequisites

- Python 3.11+
- Node.js 18+
- [Temporal CLI](https://docs.temporal.io/cli) (for the local Temporal server)

### 1. Start the Temporal server

```bash
temporal server start-dev
```

This starts Temporal on `localhost:7233` and the Web UI on `localhost:8233`.

### 2. Backend

```bash
cd backend

# Create and activate virtual environment
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS / Linux

# Install dependencies
pip install -r requirements.txt

# Copy and configure environment variables
copy .env.example .env        # Windows
# cp .env.example .env        # macOS / Linux
# Edit .env with your SMTP credentials (or leave SMTP_MOCK=true for dev)

# Terminal 1 — Temporal worker
python -m app.temporal.worker

# Terminal 2 — FastAPI server
uvicorn app.main:app --reload --port 8000
```

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

### Running order summary

```
Terminal 1:  temporal server start-dev
Terminal 2:  python -m app.temporal.worker      (from backend/)
Terminal 3:  uvicorn app.main:app --reload       (from backend/)
Terminal 4:  npm run dev                         (from frontend/)
```

---

## Environment Variables

All variables live in `backend/.env` (copy from `.env.example`):

| Variable | Default | Description |
|---|---|---|
| `TEMPORAL_HOST` | `localhost:7233` | Temporal server address |
| `TEMPORAL_NAMESPACE` | `default` | Temporal namespace |
| `TEMPORAL_TASK_QUEUE` | `workflow-engine` | Task queue name shared by worker and API |
| `API_HOST` | `0.0.0.0` | FastAPI bind host |
| `API_PORT` | `8000` | FastAPI bind port |
| `SMTP_MOCK` | `false` | `true` = log email to stdout, skip real send |
| `SMTP_HOST` | `localhost` | SMTP server hostname |
| `SMTP_PORT` | `587` | SMTP server port |
| `SMTP_USER` | *(empty)* | SMTP login username / sender address |
| `SMTP_PASSWORD` | *(empty)* | SMTP login password (use App Password for Gmail) |
| `SMTP_FROM` | same as `SMTP_USER` | Envelope From address |
| `SMTP_USE_TLS` | `true` | Enable STARTTLS |

---

## API Documentation

Full interactive docs available at `http://localhost:8000/docs` (Swagger UI).

### Workflow CRUD

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/workflows` | Create a new workflow |
| `GET` | `/api/workflows` | List all saved workflows |
| `GET` | `/api/workflows/{id}` | Get a single workflow by ID |
| `PUT` | `/api/workflows/{id}` | Update (or upsert) a workflow |
| `DELETE` | `/api/workflows/{id}` | Delete a workflow |

### Export / Import

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/workflows/{id}/export` | Export workflow as portable JSON |
| `POST` | `/api/workflows/import` | Import a previously exported JSON |

### Execution

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/workflows/{id}/run` | Run workflow via Temporal (blocks until complete) |
| `GET` | `/api/workflows/{id}/runs` | List past execution results |
| `POST` | `/api/webhooks/{id}` | Trigger via webhook (returns 202 immediately) |

### Utility

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Health check |
| `GET` | `/api/node-types` | List all registered node types |

### Example: run a workflow

```bash
POST /api/workflows/{id}/run
Content-Type: application/json

{
  "workflow_id": "abc-123",
  "trigger_payload": { "message": "hello", "value": 42 }
}
```

```json
{
  "workflow_id": "abc-123",
  "run_id": "run-xyz",
  "status": "completed",
  "logs": [
    { "step": 1, "node_type": "manual_trigger", "message": "Trigger fired", ... },
    { "step": 2, "node_type": "transform_data", "message": "Transformation applied", ... },
    { "step": 3, "node_type": "end", "message": "Workflow completed", ... }
  ],
  "final_output": { "message": "HELLO", "value": 42 }
}
```

### Example: webhook trigger

```bash
POST /api/webhooks/{workflow_id}
Content-Type: application/json

{ "event": "user_signup", "email": "user@example.com" }
```

```json
{ "run_id": "run-xyz", "workflow_id": "abc-123", "status": "accepted" }
```

---

## Workflow Execution — How Temporal Is Used

### Why Temporal?

A naive Python `asyncio` executor would lose all execution state if the process crashed mid-run. Temporal solves this with **event sourcing** — every step is recorded to a durable log. If the worker restarts, Temporal replays the history and resumes from exactly where it stopped.

### Execution pipeline

```
FastAPI  ──start_workflow()──►  Temporal Server
                                     │
                                     ▼
                            WorkflowOrchestrator.run()
                                     │
                         1. topological_sort(workflow)
                            → deterministic execution order
                                     │
                         2. for each node in order:
                            │
                            ├── SKIP?  (non-taken decision branch)
                            │
                            ├── WAIT?  (node.type == "wait")
                            │    └── await asyncio.sleep(duration)
                            │         ← intercepted by Temporal SDK
                            │         ← becomes a durable server-side timer
                            │         ← survives worker restart
                            │
                            └── EXECUTE  (all other nodes)
                                 └── workflow.execute_activity(
                                       execute_node_activity, ...)
                                       ← runs in worker thread
                                       ← retried up to 3× on failure
                                       ← result recorded in Temporal history
```

### Key Temporal concepts used

| Concept | Where | Purpose |
|---|---|---|
| **Workflow** | `WorkflowOrchestrator` | Durable coordinator — orchestrates the DAG |
| **Activity** | `execute_node_activity` | Unit of work — one activity per node execution |
| **Durable timer** | `asyncio.sleep()` inside workflow | Wait node — survives restarts, no polling loop |
| **Retry policy** | `DEFAULT_RETRY_POLICY` | 3 attempts with exponential backoff for every activity |
| **Task queue** | `workflow-engine` | Channel connecting the API to the worker |

### Decision node branching

After a Decision node's activity completes, `_branch` (`"true"` or `"false"`) is extracted from the output. The orchestrator then collects all nodes reachable exclusively via the **non-taken** handle and adds them to `skip_set`. Those nodes are logged as `SKIPPED` and never executed — the payload flows only down the matching path.

### Data propagation

Each node receives the **output of its nearest executed parent** as its input. This is resolved by `_resolve_input()`, which walks backwards through the adjacency map to find the most recent payload in `payload_store`. Trigger nodes always receive the original `trigger_payload`.

---

## DAG Validation Rules

All validation runs server-side in `services/graph.py` before any Temporal workflow is started. The client receives a structured `422` response listing **all** errors at once.

| Rule | How it is checked |
|---|---|
| At least one trigger node | Filter by `TRIGGER_TYPES` |
| At least one End node | Filter by `END_TYPES` |
| No unknown node types | `NODE_REGISTRY` lookup |
| No dangling edge references | Set membership check on node IDs |
| No cycles | Kahn's algorithm (in-degree counting) |
| No disconnected nodes | Forward BFS from all trigger nodes |
| Decision node has ≥ 1 branch connected | Check `source_handle` on outgoing edges |
| Valid node configuration | `node.validate_config()` called for every node |

---

## Design Decisions & Trade-offs

### In-memory persistence
The `WorkflowRepository` stores everything in a Python dict. This is intentionally simple — workflows and run history vanish on server restart. Replacing it with SQLite or Postgres requires implementing the same `save / get / list / delete` interface in `storage/repository.py`; no other code needs to change.

### Synchronous run endpoint
`POST /api/workflows/{id}/run` blocks until the Temporal workflow completes and returns the full execution log in one response. This is simple for the frontend (no polling needed) but impractical for workflows with long Wait nodes. The webhook endpoint (`POST /api/webhooks/{id}`) uses the correct async pattern — returns 202 immediately, runs in the background.

### Wait node as workflow-level code, not an activity
The Wait node does not run as a Temporal activity. Instead, the orchestrator calls `await asyncio.sleep(seconds)` directly inside the `@workflow.defn` function. The Temporal Python SDK intercepts this call and converts it into a server-side durable timer. This means:
- No worker thread is held during the wait
- The wait survives a complete worker process restart
- Temporal's Web UI shows the workflow as "sleeping" with a resume time

### SMTP credentials in environment variables
Email recipients and subjects are stored in workflow config (and therefore in the database). SMTP credentials (host, port, user, password) are **never** stored in workflow config — they live only in environment variables. This prevents credentials from appearing in workflow exports or API responses.

### Node extensibility pattern
Adding a new node type requires exactly three changes:
1. Create `app/nodes/your_node.py`, subclass `BaseNode`, implement `execute()` and optionally `validate_config()`
2. Add one line to `app/nodes/registry.py`
3. Add the type string to the `NodeType` Literal in `app/models/workflow.py`

The graph validator, Temporal activity, and execution log all pick up new nodes automatically.
