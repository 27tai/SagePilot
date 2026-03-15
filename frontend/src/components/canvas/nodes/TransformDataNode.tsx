'use client'

import { memo } from 'react'
import { Handle, Position, type NodeProps } from 'reactflow'
import type { RFNodeData } from '@/lib/rfAdapters'

function TransformDataNode({ data, selected }: NodeProps<RFNodeData>) {
  const transformation = (data.config.transformation as string) ?? '—'
  const field = (data.config.field as string) ?? '—'

  return (
    <div
      className={`min-w-[160px] rounded-lg border-2 bg-white shadow-md transition-shadow ${
        selected ? 'border-cyan-500 shadow-cyan-200 shadow-lg' : 'border-cyan-300'
      }`}
    >
      {/* Header */}
      <div className="flex items-center gap-2 rounded-t-md bg-cyan-500 px-3 py-1.5">
        <span className="text-xs font-bold uppercase tracking-wide text-white">Transform</span>
      </div>

      {/* Body */}
      <div className="px-3 py-2">
        <p className="text-sm font-medium text-gray-800">{data.label}</p>
        <p className="mt-0.5 text-xs text-gray-400">
          {transformation} · <span className="font-mono">{field}</span>
        </p>
      </div>

      <Handle
        type="target"
        position={Position.Left}
        className="!h-3 !w-3 !border-2 !border-cyan-500 !bg-white"
      />
      <Handle
        type="source"
        position={Position.Right}
        className="!h-3 !w-3 !border-2 !border-cyan-500 !bg-white"
      />
    </div>
  )
}

export default memo(TransformDataNode)
