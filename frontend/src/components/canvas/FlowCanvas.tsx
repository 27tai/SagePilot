'use client'

import { useCallback } from 'react'
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  ReactFlowProvider,
  useReactFlow,
} from 'reactflow'
import 'reactflow/dist/style.css'
import { useWorkflowStore } from '@/store/workflowStore'
import ManualTriggerNode from './nodes/ManualTriggerNode'
import TransformDataNode from './nodes/TransformDataNode'
import EndNode from './nodes/EndNode'

const nodeTypes = {
  manual_trigger: ManualTriggerNode,
  transform_data: TransformDataNode,
  end: EndNode,
}

// Inner component — must be inside ReactFlowProvider to use useReactFlow()
function FlowCanvasInner() {
  const {
    nodes,
    edges,
    onNodesChange,
    onEdgesChange,
    onConnect,
    addNode,
    selectNode,
  } = useWorkflowStore()

  const { screenToFlowPosition } = useReactFlow()

  const onDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.dataTransfer.dropEffect = 'move'
  }, [])

  const onDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault()
      const type = e.dataTransfer.getData('nodeType')
      if (!type) return
      const position = screenToFlowPosition({ x: e.clientX, y: e.clientY })
      addNode(type, position)
    },
    [addNode, screenToFlowPosition],
  )

  return (
    <ReactFlow
      nodes={nodes}
      edges={edges}
      onNodesChange={onNodesChange}
      onEdgesChange={onEdgesChange}
      onConnect={onConnect}
      onNodeClick={(_, node) => selectNode(node.id)}
      onPaneClick={() => selectNode(null)}
      onDrop={onDrop}
      onDragOver={onDragOver}
      nodeTypes={nodeTypes}
      deleteKeyCode="Delete"
      fitView
      className="bg-gray-50"
    >
      <Background color="#d1d5db" gap={20} />
      <Controls />
      <MiniMap
        nodeColor={(n) => {
          if (n.type === 'manual_trigger') return '#8b5cf6'
          if (n.type === 'transform_data') return '#06b6d4'
          if (n.type === 'end') return '#10b981'
          return '#94a3b8'
        }}
        maskColor="rgba(255,255,255,0.6)"
      />
    </ReactFlow>
  )
}

export default function FlowCanvas() {
  return (
    <ReactFlowProvider>
      <FlowCanvasInner />
    </ReactFlowProvider>
  )
}
