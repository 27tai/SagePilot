'use client'

const PALETTE_NODES = [
  {
    type: 'manual_trigger',
    label: 'Manual Trigger',
    description: 'Starts the workflow with a JSON payload',
    color: 'bg-violet-500',
    border: 'border-violet-300 hover:border-violet-500',
    text: 'text-violet-700',
  },
  {
    type: 'transform_data',
    label: 'Transform Data',
    description: 'Applies a transformation to a payload field',
    color: 'bg-cyan-500',
    border: 'border-cyan-300 hover:border-cyan-500',
    text: 'text-cyan-700',
  },
  {
    type: 'end',
    label: 'End',
    description: 'Terminal node — stores final output',
    color: 'bg-emerald-500',
    border: 'border-emerald-300 hover:border-emerald-500',
    text: 'text-emerald-700',
  },
]

export default function NodePalette() {
  function onDragStart(e: React.DragEvent, type: string) {
    e.dataTransfer.setData('nodeType', type)
    e.dataTransfer.effectAllowed = 'move'
  }

  return (
    <aside className="flex w-52 shrink-0 flex-col gap-3 overflow-y-auto border-r border-gray-200 bg-white p-3">
      <p className="text-xs font-semibold uppercase tracking-widest text-gray-400">Nodes</p>
      <p className="text-xs text-gray-400">Drag a node onto the canvas</p>

      {PALETTE_NODES.map((node) => (
        <div
          key={node.type}
          draggable
          onDragStart={(e) => onDragStart(e, node.type)}
          className={`cursor-grab rounded-lg border-2 bg-white p-3 transition-colors select-none active:cursor-grabbing ${node.border}`}
        >
          <div className="flex items-center gap-2">
            <span className={`h-2.5 w-2.5 rounded-full ${node.color}`} />
            <span className={`text-sm font-semibold ${node.text}`}>{node.label}</span>
          </div>
          <p className="mt-1 text-xs text-gray-400">{node.description}</p>
        </div>
      ))}
    </aside>
  )
}
