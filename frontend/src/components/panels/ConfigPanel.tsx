'use client'

import { useState, useEffect } from 'react'
import { useWorkflowStore } from '@/store/workflowStore'
import type { TransformationType } from '@/types/workflow'

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
  const { nodes, selectedNodeId, updateNodeConfig } = useWorkflowStore()

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
      {nodeType === 'transform_data' && (
        <TransformDataConfig config={config} onChange={handleChange} />
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
