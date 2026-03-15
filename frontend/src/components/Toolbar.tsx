'use client'

import { useWorkflowStore } from '@/store/workflowStore'

export default function Toolbar() {
  const { workflowName, setWorkflowName, saveWorkflow, runWorkflow, isSaving, isRunning, error, clearError, toggleWorkflowsList, newWorkflow } =
    useWorkflowStore()

  return (
    <header className="flex h-14 shrink-0 items-center gap-3 border-b border-gray-200 bg-white px-4 shadow-sm">
      {/* Logo / brand */}
      <span className="text-lg font-bold text-violet-600">SagePilot</span>

      <div className="mx-2 h-6 w-px bg-gray-200" />

      {/* Workflow name */}
      <input
        className="w-56 rounded border border-transparent bg-gray-50 px-2 py-1 text-sm font-medium text-gray-800 focus:border-gray-300 focus:outline-none"
        value={workflowName}
        onChange={(e) => setWorkflowName(e.target.value)}
        placeholder="Workflow name"
      />

      <div className="ml-auto flex items-center gap-2">
        {/* New */}
        <button
          onClick={newWorkflow}
          disabled={isRunning}
          className="rounded border border-gray-200 bg-white px-3 py-1.5 text-sm font-medium text-gray-600 transition hover:bg-gray-50 disabled:opacity-50"
        >
          New
        </button>

        {/* Workflows list */}
        <button
          onClick={toggleWorkflowsList}
          disabled={isRunning}
          className="rounded border border-gray-200 bg-white px-3 py-1.5 text-sm font-medium text-gray-600 transition hover:bg-gray-50 disabled:opacity-50"
        >
          My Workflows
        </button>
        {/* Error banner */}
        {error && (
          <div className="flex max-w-xs items-center gap-2 rounded border border-red-200 bg-red-50 px-3 py-1 text-xs text-red-600">
            <span className="truncate">{error}</span>
            <button onClick={clearError} className="shrink-0 font-bold hover:text-red-800">
              ×
            </button>
          </div>
        )}

        {/* Save */}
        <button
          onClick={saveWorkflow}
          disabled={isSaving || isRunning}
          className="rounded border border-gray-200 bg-white px-3 py-1.5 text-sm font-medium text-gray-700 transition hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {isSaving ? 'Saving…' : 'Save'}
        </button>

        {/* Run */}
        <button
          onClick={runWorkflow}
          disabled={isRunning || isSaving}
          className="flex items-center gap-2 rounded bg-violet-600 px-4 py-1.5 text-sm font-semibold text-white transition hover:bg-violet-700 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {isRunning ? (
            <>
              <span className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-white/30 border-t-white" />
              Running…
            </>
          ) : (
            <>▶ Run</>
          )}
        </button>
      </div>
    </header>
  )
}
