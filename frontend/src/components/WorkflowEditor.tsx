'use client'

import { useWorkflowStore } from '@/store/workflowStore'
import Toolbar from './Toolbar'
import NodePalette from './sidebar/NodePalette'
import FlowCanvas from './canvas/FlowCanvas'
import ConfigPanel from './panels/ConfigPanel'
import ExecutionPanel from './panels/ExecutionPanel'
import WorkflowsPanel from './panels/WorkflowsPanel'

export default function WorkflowEditor() {
  const { selectedNodeId, executionResult, isRunning, showWorkflowsList } = useWorkflowStore()

  const showConfig = selectedNodeId !== null
  const showExecution = !showConfig && (isRunning || executionResult !== null)

  return (
    <div className="relative flex h-full flex-col">
      <Toolbar />

      <div className="flex flex-1 overflow-hidden">
        <NodePalette />

        <div className="flex-1 overflow-hidden">
          <FlowCanvas />
        </div>

        {showConfig && <ConfigPanel />}
        {showExecution && <ExecutionPanel />}
      </div>

      {/* Modal overlay — sits on top of everything */}
      {showWorkflowsList && <WorkflowsPanel />}
    </div>
  )
}
