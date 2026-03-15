'use client'

import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import {
  applyNodeChanges,
  applyEdgeChanges,
  addEdge,
  type Node,
  type Edge,
  type OnNodesChange,
  type OnEdgesChange,
  type OnConnect,
  type XYPosition,
} from 'reactflow'
import type { WorkflowDefinition, WorkflowResult } from '@/types/workflow'
import {
  saveWorkflow as apiSave,
  runWorkflow as apiRun,
  listWorkflows as apiList,
  deleteWorkflow as apiDelete,
} from '@/lib/api'
import { fromRFNodes, fromRFEdges, toRFNodes, toRFEdges, type RFNodeData } from '@/lib/rfAdapters'

const DEFAULT_CONFIGS: Record<string, Record<string, unknown>> = {
  manual_trigger: { initial_payload: { message: 'hello', value: 42 } },
  webhook_trigger: {},
  transform_data: { transformation: 'uppercase', field: 'message', params: {} },
  http_request: { url: '', headers: {} },
  send_email: { to: '', subject: 'Workflow Notification' },
  wait: { duration: 5, unit: 'seconds' },
  decision: { field: '', operator: 'equals', value: '' },
  end: {},
}

const NODE_LABELS: Record<string, string> = {
  manual_trigger: 'Manual Trigger',
  webhook_trigger: 'Webhook Trigger',
  transform_data: 'Transform Data',
  http_request: 'HTTP Request',
  send_email: 'Send Email',
  wait: 'Wait',
  decision: 'Decision',
  end: 'End',
}

// Edge stroke colour based on which handle the connection came from
function edgeStyle(sourceHandle?: string | null): React.CSSProperties {
  if (sourceHandle === 'true')  return { stroke: '#22c55e', strokeWidth: 2 }
  if (sourceHandle === 'false') return { stroke: '#ef4444', strokeWidth: 2 }
  return { stroke: '#94a3b8', strokeWidth: 1.5 }
}

interface WorkflowStore {
  // React Flow state
  nodes: Node<RFNodeData>[]
  edges: Edge[]
  onNodesChange: OnNodesChange
  onEdgesChange: OnEdgesChange
  onConnect: OnConnect

  // Editor state
  workflowId: string | null
  workflowName: string
  selectedNodeId: string | null
  executionResult: WorkflowResult | null
  isRunning: boolean
  isSaving: boolean
  error: string | null

  // Workflows list state
  workflowsList: WorkflowDefinition[]
  isLoadingList: boolean
  showWorkflowsList: boolean

  // Editor actions
  addNode: (type: string, position: XYPosition) => void
  selectNode: (id: string | null) => void
  updateNodeConfig: (nodeId: string, config: Record<string, unknown>) => void
  setWorkflowName: (name: string) => void
  saveWorkflow: () => Promise<void>
  runWorkflow: () => Promise<void>
  clearError: () => void

  // Workflows list actions
  fetchWorkflows: () => Promise<void>
  loadWorkflow: (def: WorkflowDefinition) => void
  deleteWorkflow: (id: string) => Promise<void>
  newWorkflow: () => void
  toggleWorkflowsList: () => void
}

export const useWorkflowStore = create<WorkflowStore>()(
  persist(
    (set, get) => ({
      // ── Initial state ───────────────────────────────────────────────
      nodes: [],
      edges: [],
      workflowId: null,
      workflowName: 'Untitled Workflow',
      selectedNodeId: null,
      executionResult: null,
      isRunning: false,
      isSaving: false,
      error: null,
      workflowsList: [],
      isLoadingList: false,
      showWorkflowsList: false,

      // ── React Flow handlers ─────────────────────────────────────────
      onNodesChange: (changes) =>
        set({ nodes: applyNodeChanges(changes, get().nodes) as Node<RFNodeData>[] }),

      onEdgesChange: (changes) =>
        set({ edges: applyEdgeChanges(changes, get().edges) }),

      onConnect: (connection) =>
        set({
          edges: addEdge(
            { ...connection, style: edgeStyle(connection.sourceHandle) },
            get().edges,
          ),
        }),

      // ── Editor actions ──────────────────────────────────────────────
      addNode: (type, position) => {
        const id = crypto.randomUUID()
        const node: Node<RFNodeData> = {
          id,
          type,
          position,
          data: {
            label: NODE_LABELS[type] ?? type,
            config: structuredClone(DEFAULT_CONFIGS[type] ?? {}),
            nodeType: type,
          },
        }
        set({ nodes: [...get().nodes, node] })
      },

      selectNode: (id) => set({ selectedNodeId: id }),

      updateNodeConfig: (nodeId, config) =>
        set({
          nodes: get().nodes.map((n) =>
            n.id === nodeId ? { ...n, data: { ...n.data, config } } : n,
          ),
        }),

      setWorkflowName: (name) => set({ workflowName: name }),

      saveWorkflow: async () => {
        const { nodes, edges, workflowId, workflowName } = get()
        set({ isSaving: true, error: null })
        try {
          const definition = {
            id: workflowId ?? crypto.randomUUID(),
            name: workflowName,
            nodes: fromRFNodes(nodes),
            edges: fromRFEdges(edges),
          }
          const saved = await apiSave(definition)
          set({ workflowId: saved.id, isSaving: false })
        } catch (err) {
          set({ error: (err as Error).message, isSaving: false })
          throw err
        }
      },

      runWorkflow: async () => {
        set({ isRunning: true, error: null, executionResult: null, selectedNodeId: null })
        try {
          await get().saveWorkflow()
          const { workflowId } = get()
          const result = await apiRun(workflowId!, {})
          set({ executionResult: result, isRunning: false })
        } catch (err) {
          set({ error: (err as Error).message, isRunning: false })
        }
      },

      clearError: () => set({ error: null }),

      // ── Workflows list actions ──────────────────────────────────────
      fetchWorkflows: async () => {
        set({ isLoadingList: true })
        try {
          const list = await apiList()
          set({ workflowsList: list, isLoadingList: false })
        } catch (err) {
          set({ error: (err as Error).message, isLoadingList: false })
        }
      },

      loadWorkflow: (def) => {
        set({
          workflowId: def.id,
          workflowName: def.name,
          nodes: toRFNodes(def.nodes),
          edges: toRFEdges(def.edges),
          selectedNodeId: null,
          executionResult: null,
          showWorkflowsList: false,
        })
      },

      deleteWorkflow: async (id) => {
        try {
          await apiDelete(id)
          set({ workflowsList: get().workflowsList.filter((w) => w.id !== id) })
          if (get().workflowId === id) get().newWorkflow()
        } catch (err) {
          set({ error: (err as Error).message })
        }
      },

      newWorkflow: () =>
        set({
          nodes: [],
          edges: [],
          workflowId: null,
          workflowName: 'Untitled Workflow',
          selectedNodeId: null,
          executionResult: null,
          showWorkflowsList: false,
        }),

      toggleWorkflowsList: () => {
        const next = !get().showWorkflowsList
        set({ showWorkflowsList: next })
        if (next) get().fetchWorkflows()
      },
    }),
    {
      name: 'sagepilot-editor', // localStorage key
      // Only persist the canvas — skip transient run/UI state
      partialize: (state) => ({
        nodes: state.nodes,
        edges: state.edges,
        workflowId: state.workflowId,
        workflowName: state.workflowName,
      }),
    },
  ),
)
