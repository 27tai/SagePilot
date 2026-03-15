'use client'

import { memo } from 'react'
import { Handle, Position, type NodeProps } from 'reactflow'
import type { RFNodeData } from '@/lib/rfAdapters'

function EndNode({ data, selected }: NodeProps<RFNodeData>) {
  return (
    <div
      className={`min-w-[160px] rounded-lg border-2 bg-white shadow-md transition-shadow ${
        selected ? 'border-emerald-500 shadow-emerald-200 shadow-lg' : 'border-emerald-300'
      }`}
    >
      {/* Header */}
      <div className="flex items-center gap-2 rounded-t-md bg-emerald-500 px-3 py-1.5">
        <span className="text-xs font-bold uppercase tracking-wide text-white">End</span>
      </div>

      {/* Body */}
      <div className="px-3 py-2">
        <p className="text-sm font-medium text-gray-800">{data.label}</p>
        <p className="mt-0.5 text-xs text-gray-400">terminal</p>
      </div>

      {/* Only a target handle — end node has no output */}
      <Handle
        type="target"
        position={Position.Left}
        className="!h-3 !w-3 !border-2 !border-emerald-500 !bg-white"
      />
    </div>
  )
}

export default memo(EndNode)
