export type NodeType =
  | 'manual_trigger'
  | 'webhook_trigger'
  | 'transform_data'
  | 'http_request'
  | 'wait'
  | 'decision'
  | 'end'

export type TransformationType =
  | 'uppercase'
  | 'append_text'
  | 'prepend_text'
  | 'multiply'
  | 'rename_key'

export interface NodePosition {
  x: number
  y: number
}

export interface NodeConfig {
  id: string
  type: NodeType
  config: Record<string, unknown>
  position: NodePosition
  label?: string
}

export interface EdgeConfig {
  id: string
  source_node_id: string
  target_node_id: string
  source_handle?: string | null
}

export interface WorkflowDefinition {
  id: string
  name: string
  nodes: NodeConfig[]
  edges: EdgeConfig[]
  created_at?: string
  updated_at?: string
}

export interface ExecutionLog {
  step: number
  node_id: string
  node_type: string
  input_payload: Record<string, unknown>
  output_payload: Record<string, unknown>
  message: string
  error?: string | null
}

export interface WorkflowResult {
  workflow_id: string
  run_id: string
  status: 'completed' | 'failed'
  logs: ExecutionLog[]
  final_output?: Record<string, unknown> | null
  error?: string | null
}
