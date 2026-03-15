import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'SagePilot — Workflow Engine',
  description: 'Visual workflow automation engine',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="h-full">
      <body className="h-full font-sans antialiased">{children}</body>
    </html>
  )
}
