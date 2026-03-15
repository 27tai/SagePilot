'use client'

import { memo } from 'react'
import { Handle, Position, type NodeProps } from 'reactflow'
import type { RFNodeData } from '@/lib/rfAdapters'

function SendEmailNode({ data, selected }: NodeProps<RFNodeData>) {
  const to = (data.config.to as string) || '(no recipient set)'

  return (
    <div
      className={`min-w-[180px] rounded-lg border-2 bg-white shadow-md transition-shadow ${
        selected ? 'border-pink-500 shadow-pink-200 shadow-lg' : 'border-pink-300'
      }`}
    >
      <div className="flex items-center gap-2 rounded-t-md bg-pink-500 px-3 py-1.5">
        <span className="text-xs font-bold uppercase tracking-wide text-white">Send Email</span>
      </div>

      <div className="px-3 py-2">
        <p className="text-sm font-medium text-gray-800">{data.label}</p>
        <p className="mt-0.5 max-w-[160px] truncate text-xs text-gray-400">{to}</p>
      </div>

      <Handle
        type="target"
        position={Position.Left}
        className="!h-3 !w-3 !border-2 !border-pink-500 !bg-white"
      />
      <Handle
        type="source"
        position={Position.Right}
        className="!h-3 !w-3 !border-2 !border-pink-500 !bg-white"
      />
    </div>
  )
}

export default memo(SendEmailNode)
