'use client'

import { memo } from 'react'
import { Handle, Position, type NodeProps } from 'reactflow'
import type { RFNodeData } from '@/lib/rfAdapters'

function HttpRequestNode({ data, selected }: NodeProps<RFNodeData>) {
  const method = (data.config.method as string) || 'GET'
  const url = (data.config.url as string) || '(no URL set)'

  return (
    <div
      className={`min-w-[180px] rounded-lg border-2 bg-white shadow-md transition-shadow ${
        selected ? 'border-blue-500 shadow-blue-200 shadow-lg' : 'border-blue-300'
      }`}
    >
      {/* Header */}
      <div className="flex items-center gap-2 rounded-t-md bg-blue-500 px-3 py-1.5">
        <span className="text-xs font-bold uppercase tracking-wide text-white">HTTP Request</span>
      </div>

      {/* Body */}
      <div className="px-3 py-2">
        <p className="text-sm font-medium text-gray-800">{data.label}</p>
        <p className="mt-1 flex items-center gap-1.5">
          <span className="rounded bg-blue-100 px-1.5 py-0.5 font-mono text-xs font-bold text-blue-700">
            {method}
          </span>
          <span className="max-w-[120px] truncate font-mono text-xs text-gray-500">{url}</span>
        </p>
      </div>

      <Handle
        type="target"
        position={Position.Left}
        className="!h-3 !w-3 !border-2 !border-blue-500 !bg-white"
      />
      <Handle
        type="source"
        position={Position.Right}
        className="!h-3 !w-3 !border-2 !border-blue-500 !bg-white"
      />
    </div>
  )
}

export default memo(HttpRequestNode)
