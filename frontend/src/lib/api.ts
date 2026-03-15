import type { WorkflowDefinition, WorkflowResult } from '@/types/workflow'

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  let res: Response
  try {
    res = await fetch(`${API_BASE}${path}`, {
      headers: { 'Content-Type': 'application/json' },
      ...options,
    })
  } catch {
    throw new Error(`Cannot reach backend at ${API_BASE}. Is the server running?`)
  }
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    const msg = typeof err.detail === 'string' ? err.detail : JSON.stringify(err.detail)
    throw new Error(msg)
  }
  return res.json() as Promise<T>
}

export async function saveWorkflow(wf: WorkflowDefinition): Promise<WorkflowDefinition> {
  // PUT if we already have a persisted ID, POST otherwise
  if (wf.id) {
    return request<WorkflowDefinition>(`/api/workflows/${wf.id}`, {
      method: 'PUT',
      body: JSON.stringify(wf),
    })
  }
  return request<WorkflowDefinition>('/api/workflows', {
    method: 'POST',
    body: JSON.stringify(wf),
  })
}

export async function listWorkflows(): Promise<WorkflowDefinition[]> {
  return request<WorkflowDefinition[]>('/api/workflows')
}

export async function getWorkflow(id: string): Promise<WorkflowDefinition> {
  return request<WorkflowDefinition>(`/api/workflows/${id}`)
}

export async function deleteWorkflow(id: string): Promise<void> {
  await request<void>(`/api/workflows/${id}`, { method: 'DELETE' })
}

export async function runWorkflow(
  workflowId: string,
  triggerPayload: Record<string, unknown> = {},
): Promise<WorkflowResult> {
  return request<WorkflowResult>(`/api/workflows/${workflowId}/run`, {
    method: 'POST',
    body: JSON.stringify({ workflow_id: workflowId, trigger_payload: triggerPayload }),
  })
}
