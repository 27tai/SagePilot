import type { Node, Edge } from 'reactflow'
import type { NodeConfig, EdgeConfig } from '@/types/workflow'

export interface RFNodeData {
  label: string
  config: Record<string, unknown>
  nodeType: string
}

const NODE_LABELS: Record<string, string> = {
  manual_trigger: 'Manual Trigger',
  transform_data: 'Transform Data',
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
