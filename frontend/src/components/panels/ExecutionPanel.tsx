'use client'

import { useWorkflowStore } from '@/store/workflowStore'
import type { ExecutionLog } from '@/types/workflow'

const NODE_TYPE_COLOURS: Record<string, string> = {
  manual_trigger: 'bg-violet-100 text-violet-700',
  transform_data: 'bg-cyan-100 text-cyan-700',
  end: 'bg-emerald-100 text-emerald-700',
}

function JsonBlock({ value }: { value: Record<string, unknown> }) {
  return (
    <pre className="mt-1 overflow-x-auto rounded bg-gray-50 p-2 text-xs text-gray-600">
      {JSON.stringify(value, null, 2)}
    </pre>
  )
}

function LogRow({ log }: { log: ExecutionLog }) {
  const badgeCls = NODE_TYPE_COLOURS[log.node_type] ?? 'bg-gray-100 text-gray-600'

  return (
    <div className={`rounded-lg border p-3 ${log.error ? 'border-red-200 bg-red-50' : 'border-gray-100 bg-white'}`}>
      <div className="flex items-center gap-2">
        <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-gray-200 text-xs font-bold text-gray-600">
          {log.step}
        </span>
        <span className={`rounded px-1.5 py-0.5 text-xs font-semibold ${badgeCls}`}>
          {log.node_type}
        </span>
        <span className="truncate text-xs text-gray-500">{log.message}</span>
      </div>

      {log.error && (
        <p className="mt-2 text-xs font-medium text-red-600">Error: {log.error}</p>
      )}

      <div className="mt-2 grid grid-cols-2 gap-2">
        <div>
          <p className="text-xs font-semibold text-gray-400">Input</p>
          <JsonBlock value={log.input_payload} />
        </div>
        <div>
          <p className="text-xs font-semibold text-gray-400">Output</p>
          <JsonBlock value={log.output_payload} />
        </div>
      </div>
    </div>
  )
}

export default function ExecutionPanel() {
  const { executionResult, isRunning } = useWorkflowStore()

  if (isRunning) {
    return (
      <aside className="flex w-72 shrink-0 flex-col items-center justify-center gap-3 border-l border-gray-200 bg-white p-4">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-gray-200 border-t-violet-500" />
        <p className="text-sm text-gray-500">Running workflow…</p>
        <p className="text-xs text-gray-400">Executing via Temporal</p>
      </aside>
    )
  }

  if (!executionResult) return null

  const isSuccess = executionResult.status === 'completed'

  return (
    <aside className="flex w-72 shrink-0 flex-col gap-3 overflow-y-auto border-l border-gray-200 bg-white p-4">
      {/* Header */}
      <div>
        <p className="text-xs font-semibold uppercase tracking-widest text-gray-400">
          Execution result
        </p>
        <div className="mt-1 flex items-center gap-2">
          <span
            className={`rounded-full px-2 py-0.5 text-xs font-bold uppercase ${
              isSuccess ? 'bg-emerald-100 text-emerald-700' : 'bg-red-100 text-red-700'
            }`}
          >
            {executionResult.status}
          </span>
          <span className="truncate font-mono text-xs text-gray-400">
            {executionResult.run_id.slice(0, 8)}…
          </span>
        </div>
      </div>

      {executionResult.error && (
        <div className="rounded border border-red-200 bg-red-50 p-2 text-xs text-red-600">
          {executionResult.error}
        </div>
      )}

      {/* Final output */}
      {executionResult.final_output && (
        <div>
          <p className="text-xs font-semibold text-gray-500">Final output</p>
          <JsonBlock value={executionResult.final_output} />
        </div>
      )}

      <hr className="border-gray-100" />

      {/* Step logs */}
      <p className="text-xs font-semibold text-gray-500">
        Execution log ({executionResult.logs.length} steps)
      </p>
      <div className="flex flex-col gap-2">
        {executionResult.logs.map((log) => (
          <LogRow key={log.step} log={log} />
        ))}
      </div>
    </aside>
  )
}
