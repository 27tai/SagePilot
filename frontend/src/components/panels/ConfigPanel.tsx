'use client'

import { useState } from 'react'
import { useWorkflowStore } from '@/store/workflowStore'
import type { TransformationType } from '@/types/workflow'

// ── WebhookTrigger config ─────────────────────────────────────────────────
function WebhookTriggerConfig({ workflowId }: { workflowId: string | null }) {
  const url = workflowId
    ? `${process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'}/api/webhooks/${workflowId}`
    : '(save workflow first to get URL)'

  return (
    <Field label="Webhook URL (read-only)">
      <div className="flex items-center gap-1">
        <input
          readOnly
          className={`${INPUT_CLS} flex-1 select-all bg-gray-100 text-gray-500`}
          value={url}
        />
        <button
          type="button"
          className="shrink-0 rounded border border-gray-200 bg-gray-50 px-2 py-1.5 text-xs text-gray-500 hover:bg-gray-100"
          onClick={() => navigator.clipboard.writeText(url)}
        >
          Copy
        </button>
      </div>
      <p className="text-xs text-gray-400">
        Send a POST request with a JSON body to trigger this workflow.
      </p>
    </Field>
  )
}

// ── HttpRequest config ────────────────────────────────────────────────────
function HttpRequestConfig({
  config,
  onChange,
}: {
  config: Record<string, unknown>
  onChange: (c: Record<string, unknown>) => void
}) {
  const [rawHeaders, setRawHeaders] = useState(
    JSON.stringify(config.headers ?? {}, null, 2),
  )
  const [headersError, setHeadersError] = useState('')

  function commitHeaders(value: string) {
    try {
      const parsed = JSON.parse(value || '{}')
      setHeadersError('')
      onChange({ ...config, headers: parsed })
    } catch {
      setHeadersError('Invalid JSON')
    }
  }

  return (
    <>
      <Field label="POST URL">
        <input
          className={INPUT_CLS}
          placeholder="https://api.example.com/endpoint"
          value={(config.url as string) ?? ''}
          onChange={(e) => onChange({ ...config, url: e.target.value })}
        />
      </Field>

      <Field label="Headers (JSON, optional)">
        <textarea
          className={`${INPUT_CLS} min-h-[72px] resize-y font-mono text-xs`}
          value={rawHeaders}
          onChange={(e) => setRawHeaders(e.target.value)}
          onBlur={(e) => commitHeaders(e.target.value)}
          spellCheck={false}
        />
        {headersError && <p className="text-xs text-red-500">{headersError}</p>}
      </Field>

      <div className="rounded-lg border border-dashed border-blue-200 p-2 text-xs text-blue-400">
        The entire incoming payload is forwarded as the POST body.
      </div>
    </>
  )
}

// ── SendEmail config ──────────────────────────────────────────────────────
function SendEmailConfig({
  config,
  onChange,
}: {
  config: Record<string, unknown>
  onChange: (c: Record<string, unknown>) => void
}) {
  return (
    <>
      <Field label="Recipient (To)">
        <input
          className={INPUT_CLS}
          type="email"
          placeholder="user@example.com"
          value={(config.to as string) ?? ''}
          onChange={(e) => onChange({ ...config, to: e.target.value })}
        />
      </Field>

      <Field label="Subject">
        <input
          className={INPUT_CLS}
          placeholder="Workflow Notification"
          value={(config.subject as string) ?? ''}
          onChange={(e) => onChange({ ...config, subject: e.target.value })}
        />
      </Field>

      <div className="rounded-lg border border-dashed border-pink-200 p-2 text-xs text-pink-400">
        The entire incoming payload is sent as the email body (formatted JSON).
        SMTP credentials are configured via server environment variables.
      </div>
    </>
  )
}

// ── Wait config ───────────────────────────────────────────────────────────
function WaitConfig({
  config,
  onChange,
}: {
  config: Record<string, unknown>
  onChange: (c: Record<string, unknown>) => void
}) {
  return (
    <>
      <Field label="Duration">
        <input
          type="number"
          min={1}
          className={INPUT_CLS}
          value={(config.duration as number) ?? 5}
          onChange={(e) => {
            const v = parseInt(e.target.value, 10)
            onChange({ ...config, duration: isNaN(v) || v < 1 ? 1 : v })
          }}
        />
      </Field>

      <Field label="Unit">
        <select
          className={INPUT_CLS}
          value={(config.unit as string) ?? 'seconds'}
          onChange={(e) => onChange({ ...config, unit: e.target.value })}
        >
          <option value="seconds">Seconds</option>
          <option value="minutes">Minutes</option>
        </select>
      </Field>

      <div className="rounded-lg border border-dashed border-orange-200 p-2 text-xs text-orange-400">
        Uses Temporal&apos;s durable timer — survives worker restarts.
      </div>
    </>
  )
}

// ── Decision config ───────────────────────────────────────────────────────

const OPERATORS = [
  { value: 'equals',       label: 'equals' },
  { value: 'not_equals',   label: 'not equals' },
  { value: 'greater_than', label: 'greater than' },
  { value: 'less_than',    label: 'less than' },
  { value: 'contains',     label: 'contains' },
  { value: 'is_empty',     label: 'is empty' },
]

function DecisionConfig({
  config,
  onChange,
}: {
  config: Record<string, unknown>
  onChange: (c: Record<string, unknown>) => void
}) {
  const operator = (config.operator as string) ?? 'equals'

  return (
    <>
      <Field label="Field to evaluate">
        <input
          className={INPUT_CLS}
          placeholder="e.g. status"
          value={(config.field as string) ?? ''}
          onChange={(e) => onChange({ ...config, field: e.target.value })}
        />
      </Field>

      <Field label="Operator">
        <select
          className={INPUT_CLS}
          value={operator}
          onChange={(e) => onChange({ ...config, operator: e.target.value })}
        >
          {OPERATORS.map((op) => (
            <option key={op.value} value={op.value}>{op.label}</option>
          ))}
        </select>
      </Field>

      {operator !== 'is_empty' && (
        <Field label="Compare value">
          <input
            className={INPUT_CLS}
            placeholder="e.g. active"
            value={(config.value as string) ?? ''}
            onChange={(e) => onChange({ ...config, value: e.target.value })}
          />
        </Field>
      )}

      {/* Branch hint */}
      <div className="rounded-lg border border-dashed border-gray-200 p-2 text-xs text-gray-400">
        <p className="font-semibold text-gray-500">How to connect branches</p>
        <p className="mt-1">Drag from the <span className="font-semibold text-emerald-600">✓ True</span> handle to connect the true path.</p>
        <p className="mt-0.5">Drag from the <span className="font-semibold text-red-500">✗ False</span> handle to connect the false path.</p>
      </div>
    </>
  )
}

const TRANSFORMATIONS: { value: TransformationType; label: string }[] = [
  { value: 'uppercase', label: 'Uppercase' },
  { value: 'append_text', label: 'Append text' },
  { value: 'prepend_text', label: 'Prepend text' },
  { value: 'multiply', label: 'Multiply' },
  { value: 'rename_key', label: 'Rename key' },
]

// ── Shared field wrapper ──────────────────────────────────────────────────
function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex flex-col gap-1">
      <label className="text-xs font-semibold text-gray-500">{label}</label>
      {children}
    </div>
  )
}

const INPUT_CLS =
  'w-full rounded border border-gray-200 bg-gray-50 px-2 py-1.5 text-sm text-gray-800 focus:border-gray-400 focus:outline-none'

// ── ManualTrigger config ──────────────────────────────────────────────────
function ManualTriggerConfig({
  config,
  onChange,
}: {
  config: Record<string, unknown>
  onChange: (c: Record<string, unknown>) => void
}) {
  const [raw, setRaw] = useState(JSON.stringify(config.initial_payload ?? {}, null, 2))
  const [error, setError] = useState('')

  function handleBlur() {
    try {
      const parsed = JSON.parse(raw)
      setError('')
      onChange({ ...config, initial_payload: parsed })
    } catch {
      setError('Invalid JSON')
    }
  }

  return (
    <Field label="Initial payload (JSON)">
      <textarea
        className={`${INPUT_CLS} min-h-[120px] resize-y font-mono text-xs`}
        value={raw}
        onChange={(e) => setRaw(e.target.value)}
        onBlur={handleBlur}
        spellCheck={false}
      />
      {error && <p className="text-xs text-red-500">{error}</p>}
    </Field>
  )
}

// ── TransformData config ──────────────────────────────────────────────────
function TransformDataConfig({
  config,
  onChange,
}: {
  config: Record<string, unknown>
  onChange: (c: Record<string, unknown>) => void
}) {
  const transformation = (config.transformation as TransformationType) ?? 'uppercase'
  const field = (config.field as string) ?? ''
  const params = (config.params as Record<string, unknown>) ?? {}

  function update(patch: Record<string, unknown>) {
    onChange({ ...config, ...patch })
  }

  function updateParam(key: string, value: unknown) {
    onChange({ ...config, params: { ...params, [key]: value } })
  }

  return (
    <>
      <Field label="Transformation">
        <select
          className={INPUT_CLS}
          value={transformation}
          onChange={(e) => {
            update({ transformation: e.target.value, params: {} })
          }}
        >
          {TRANSFORMATIONS.map((t) => (
            <option key={t.value} value={t.value}>
              {t.label}
            </option>
          ))}
        </select>
      </Field>

      <Field label="Target field">
        <input
          className={INPUT_CLS}
          placeholder="e.g. message"
          value={field}
          onChange={(e) => update({ field: e.target.value })}
        />
      </Field>

      {/* Dynamic params based on transformation type */}
      {(transformation === 'append_text' || transformation === 'prepend_text') && (
        <Field label="Text">
          <input
            className={INPUT_CLS}
            placeholder="Text to append/prepend"
            value={(params.text as string) ?? ''}
            onChange={(e) => updateParam('text', e.target.value)}
          />
        </Field>
      )}

      {transformation === 'multiply' && (
        <Field label="Factor">
          <input
            type="number"
            className={INPUT_CLS}
            value={typeof params.factor === 'number' && !isNaN(params.factor as number) ? (params.factor as number) : 1}
            onChange={(e) => {
              const v = e.target.valueAsNumber
              updateParam('factor', isNaN(v) ? 1 : v)
            }}
          />
        </Field>
      )}

      {transformation === 'rename_key' && (
        <Field label="New key name">
          <input
            className={INPUT_CLS}
            placeholder="e.g. new_message"
            value={(params.new_key as string) ?? ''}
            onChange={(e) => updateParam('new_key', e.target.value)}
          />
        </Field>
      )}
    </>
  )
}

// ── Main ConfigPanel ──────────────────────────────────────────────────────
export default function ConfigPanel() {
  const { nodes, selectedNodeId, updateNodeConfig, workflowId } = useWorkflowStore()

  const node = nodes.find((n) => n.id === selectedNodeId)
  if (!node) return null

  const { nodeType, config, label } = node.data

  function handleChange(newConfig: Record<string, unknown>) {
    updateNodeConfig(node!.id, newConfig)
  }

  return (
    <aside className="flex w-72 shrink-0 flex-col gap-4 overflow-y-auto border-l border-gray-200 bg-white p-4">
      {/* Header */}
      <div>
        <p className="text-xs font-semibold uppercase tracking-widest text-gray-400">
          Node config
        </p>
        <p className="mt-0.5 text-base font-semibold text-gray-800">{label}</p>
        <p className="text-xs text-gray-400">{nodeType}</p>
      </div>

      <hr className="border-gray-100" />

      {/* Per-type form */}
      {nodeType === 'manual_trigger' && (
        <ManualTriggerConfig config={config} onChange={handleChange} />
      )}
      {nodeType === 'webhook_trigger' && (
        <WebhookTriggerConfig workflowId={workflowId} />
      )}
      {nodeType === 'transform_data' && (
        <TransformDataConfig config={config} onChange={handleChange} />
      )}
      {nodeType === 'http_request' && (
        <HttpRequestConfig config={config} onChange={handleChange} />
      )}
      {nodeType === 'send_email' && (
        <SendEmailConfig config={config} onChange={handleChange} />
      )}
      {nodeType === 'wait' && (
        <WaitConfig config={config} onChange={handleChange} />
      )}
      {nodeType === 'decision' && (
        <DecisionConfig config={config} onChange={handleChange} />
      )}
      {nodeType === 'end' && (
        <p className="text-sm text-gray-400">
          Terminal node — no configuration needed. Receives and stores the final payload.
        </p>
      )}

      <p className="mt-auto text-xs text-gray-300">
        Press <kbd className="rounded bg-gray-100 px-1 py-0.5 text-gray-500">Delete</kbd> to remove
        a selected node
      </p>
    </aside>
  )
}
