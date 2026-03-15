'use client'

import { useWorkflowStore } from '@/store/workflowStore'
import type { WorkflowDefinition } from '@/types/workflow'

function formatDate(iso?: string) {
  if (!iso) return '—'
  return new Date(iso).toLocaleString(undefined, {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

function WorkflowRow({ wf }: { wf: WorkflowDefinition }) {
  const { loadWorkflow, deleteWorkflow, workflowId } = useWorkflowStore()
  const isActive = wf.id === workflowId

  return (
    <div
      className={`group rounded-lg border p-3 transition-colors ${
        isActive
          ? 'border-violet-300 bg-violet-50'
          : 'border-gray-100 bg-white hover:border-gray-200 hover:bg-gray-50'
      }`}
    >
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <p className="truncate text-sm font-semibold text-gray-800">{wf.name}</p>
          <p className="mt-0.5 text-xs text-gray-400">
            {wf.nodes.length} node{wf.nodes.length !== 1 ? 's' : ''} ·{' '}
            {wf.edges.length} edge{wf.edges.length !== 1 ? 's' : ''}
          </p>
          <p className="mt-0.5 text-xs text-gray-300">Updated {formatDate(wf.updated_at)}</p>
        </div>

        {isActive && (
          <span className="shrink-0 rounded-full bg-violet-100 px-2 py-0.5 text-xs font-semibold text-violet-600">
            open
          </span>
        )}
      </div>

      {/* Action buttons — visible on hover */}
      <div className="mt-2 flex gap-2">
        <button
          onClick={() => loadWorkflow(wf)}
          disabled={isActive}
          className="flex-1 rounded bg-violet-600 px-2 py-1 text-xs font-semibold text-white transition hover:bg-violet-700 disabled:cursor-default disabled:opacity-40"
        >
          {isActive ? 'Current' : 'Open'}
        </button>
        <button
          onClick={() => {
            if (confirm(`Delete "${wf.name}"?`)) deleteWorkflow(wf.id)
          }}
          className="rounded border border-red-200 px-2 py-1 text-xs font-semibold text-red-500 transition hover:bg-red-50"
        >
          Delete
        </button>
      </div>
    </div>
  )
}

export default function WorkflowsPanel() {
  const { workflowsList, isLoadingList, fetchWorkflows, newWorkflow } = useWorkflowStore()

  return (
    <div className="absolute inset-0 z-20 flex items-start justify-center bg-black/20 pt-16"
      onClick={(e) => { if (e.target === e.currentTarget) useWorkflowStore.getState().toggleWorkflowsList() }}
    >
      <div className="mx-4 w-full max-w-md rounded-xl border border-gray-200 bg-white shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-gray-100 px-4 py-3">
          <div>
            <h2 className="text-base font-bold text-gray-800">Saved Workflows</h2>
            <p className="text-xs text-gray-400">Stored in sagepilot.db (SQLite)</p>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={newWorkflow}
              className="rounded bg-violet-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-violet-700"
            >
              + New
            </button>
            <button
              onClick={() => useWorkflowStore.getState().toggleWorkflowsList()}
              className="rounded p-1 text-gray-400 hover:bg-gray-100 hover:text-gray-600"
            >
              ✕
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="max-h-[60vh] overflow-y-auto p-3">
          {isLoadingList ? (
            <div className="flex items-center justify-center py-12">
              <div className="h-6 w-6 animate-spin rounded-full border-2 border-gray-200 border-t-violet-500" />
            </div>
          ) : workflowsList.length === 0 ? (
            <div className="py-12 text-center">
              <p className="text-sm text-gray-400">No saved workflows yet.</p>
              <p className="mt-1 text-xs text-gray-300">
                Build a workflow and click Save.
              </p>
            </div>
          ) : (
            <div className="flex flex-col gap-2">
              {workflowsList.map((wf) => (
                <WorkflowRow key={wf.id} wf={wf} />
              ))}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between border-t border-gray-100 px-4 py-2">
          <span className="text-xs text-gray-400">{workflowsList.length} workflow{workflowsList.length !== 1 ? 's' : ''}</span>
          <button onClick={fetchWorkflows} className="text-xs text-violet-500 hover:underline">
            Refresh
          </button>
        </div>
      </div>
    </div>
  )
}
