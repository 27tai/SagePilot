import type { Node, Edge } from 'reactflow'
import type { NodeConfig, EdgeConfig } from '@/types/workflow'

export interface RFNodeData {
  label: string
  config: Record<string, unknown>
  nodeType: string
}

const NODE_LABELS: Record<string, string> = {
  manual_trigger: 'Manual Trigger',
  webhook_trigger: 'Webhook Trigger',
  transform_data: 'Transform Data',
  http_request: 'HTTP Request',
  wait: 'Wait',
  decision: 'Decision',
  end: 'End',
}

/** Convert backend NodeConfig[] → React Flow Node[] (for loading a saved workflow) */
export function toRFNodes(nodes: NodeConfig[]): Node<RFNodeData>[] {
  return nodes.map((n) => ({
    id: n.id,
    type: n.type,
    position: n.position,
    data: {
      label: n.label ?? NODE_LABELS[n.type] ?? n.type,
      config: n.config,
      nodeType: n.type,
    },
  }))
}

/** Convert backend EdgeConfig[] → React Flow Edge[] (for loading a saved workflow) */
export function toRFEdges(edges: EdgeConfig[]): Edge[] {
  return edges.map((e) => ({
    id: e.id,
    source: e.source_node_id,
    target: e.target_node_id,
    sourceHandle: e.source_handle ?? null,
    style:
      e.source_handle === 'true'  ? { stroke: '#22c55e', strokeWidth: 2 } :
      e.source_handle === 'false' ? { stroke: '#ef4444', strokeWidth: 2 } :
                                    { stroke: '#94a3b8', strokeWidth: 1.5 },
  }))
}

export function fromRFNodes(nodes: Node<RFNodeData>[]): NodeConfig[] {
  return nodes.map((n) => ({
    id: n.id,
    type: n.data.nodeType as NodeConfig['type'],
    config: n.data.config,
    position: n.position,
    label: n.data.label,
  }))
}

export function fromRFEdges(edges: Edge[]): EdgeConfig[] {
  return edges.map((e) => ({
    id: e.id,
    source_node_id: e.source,
    target_node_id: e.target,
    source_handle: e.sourceHandle ?? null,
  }))
}
