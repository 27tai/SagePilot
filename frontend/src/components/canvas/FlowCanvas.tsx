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
import WebhookTriggerNode from './nodes/WebhookTriggerNode'
import TransformDataNode from './nodes/TransformDataNode'
import HttpRequestNode from './nodes/HttpRequestNode'
import SendEmailNode from './nodes/SendEmailNode'
import WaitNode from './nodes/WaitNode'
import DecisionNode from './nodes/DecisionNode'
import EndNode from './nodes/EndNode'

const nodeTypes = {
  manual_trigger: ManualTriggerNode,
  webhook_trigger: WebhookTriggerNode,
  transform_data: TransformDataNode,
  http_request: HttpRequestNode,
  send_email: SendEmailNode,
  wait: WaitNode,
  decision: DecisionNode,
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
          if (n.type === 'webhook_trigger') return '#6366f1'
          if (n.type === 'transform_data') return '#06b6d4'
          if (n.type === 'http_request') return '#3b82f6'
          if (n.type === 'send_email') return '#ec4899'
          if (n.type === 'wait') return '#f97316'
          if (n.type === 'decision') return '#f59e0b'
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
