'use client'

import dynamic from 'next/dynamic'

// Disable SSR for the editor — React Flow requires browser APIs
const WorkflowEditor = dynamic(() => import('@/components/WorkflowEditor'), { ssr: false })

export default function Page() {
  return <WorkflowEditor />
}
