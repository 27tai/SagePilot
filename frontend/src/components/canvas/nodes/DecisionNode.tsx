'use client'

import { memo } from 'react'
import { Handle, Position, type NodeProps } from 'reactflow'
import type { RFNodeData } from '@/lib/rfAdapters'

const OPERATOR_LABELS: Record<string, string> = {
  equals: '=',
  not_equals: '≠',
  greater_than: '>',
  less_than: '<',
  contains: '∋',
  is_empty: 'empty?',
}

function DecisionNode({ data, selected }: NodeProps<RFNodeData>) {
  const field = (data.config.field as string) || '?'
  const operator = (data.config.operator as string) || 'equals'
  const value = data.config.operator === 'is_empty' ? '' : String(data.config.value ?? '?')
  const opLabel = OPERATOR_LABELS[operator] ?? operator

  return (
    <div
      className={`min-w-[180px] rounded-lg border-2 bg-white shadow-md transition-shadow ${
        selected ? 'border-amber-500 shadow-amber-200 shadow-lg' : 'border-amber-300'
      }`}
    >
      {/* Header */}
      <div className="flex items-center gap-2 rounded-t-md bg-amber-500 px-3 py-1.5">
        <span className="text-xs font-bold uppercase tracking-wide text-white">Decision</span>
      </div>

      {/* Condition summary */}
      <div className="px-3 py-2">
        <p className="text-sm font-medium text-gray-800">{data.label}</p>
        <p className="mt-1 rounded bg-gray-50 px-2 py-1 font-mono text-xs text-gray-600">
          <span className="text-amber-600">{field}</span>
          {' '}<span className="text-gray-400">{opLabel}</span>
          {value && <> <span className="text-blue-600">{value}</span></>}
        </p>
      </div>

      {/* Branch output rows — each has its own labeled handle */}
      <div className="border-t border-gray-100">
        {/* True branch */}
        <div className="relative flex items-center justify-between px-3 py-1.5">
          <span className="text-xs font-semibold text-emerald-600">✓ True</span>
          <Handle
            id="true"
            type="source"
            position={Position.Right}
            className="!relative !right-auto !top-auto !h-3 !w-3 !translate-y-0 !border-2 !border-emerald-500 !bg-white"
          />
        </div>

        <div className="mx-3 border-t border-dashed border-gray-100" />

        {/* False branch */}
        <div className="relative flex items-center justify-between px-3 py-1.5">
          <span className="text-xs font-semibold text-red-500">✗ False</span>
          <Handle
            id="false"
            type="source"
            position={Position.Right}
            className="!relative !right-auto !top-auto !h-3 !w-3 !translate-y-0 !border-2 !border-red-400 !bg-white"
          />
        </div>
      </div>

      {/* Target (input) handle */}
      <Handle
        type="target"
        position={Position.Left}
        className="!h-3 !w-3 !border-2 !border-amber-500 !bg-white"
      />
    </div>
  )
}

export default memo(DecisionNode)
