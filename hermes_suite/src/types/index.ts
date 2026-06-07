// ─── Agent ────────────────────────────────────────────────────

export type AgentStatus = 'idle' | 'running' | 'paused' | 'stopped'

export interface Agent {
  id: string
  name: string
  status: AgentStatus
  model?: string
  startedAt?: string
  lastSeen?: string
  behaviours?: string[]
  parentId?: string
}

// ─── Cron ─────────────────────────────────────────────────────

export type CronStatus = 'active' | 'paused'

export interface CronJob {
  id: string
  name: string
  schedule: string
  prompt: string
  deliver: string
  status: CronStatus
  lastRun?: string
  nextRun?: string
  repeat?: number
}

// ─── Skill ────────────────────────────────────────────────────

export interface Skill {
  name: string
  description: string
  triggers: string[]
  enabled: boolean
  path: string
  configSchema?: Record<string, unknown>
}

// ─── Memory ───────────────────────────────────────────────────

export interface MemoryFile {
  name: string
  path: string
  size: number
  modified: string
  content?: string
}

// ─── Chat ─────────────────────────────────────────────────────

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant' | 'system' | 'tool'
  content: string
  toolCall?: {
    name: string
    args: Record<string, unknown>
  }
  timestamp: string
}

// ─── Widget ────────────────────────────────────────────────────

export type WidgetId =
  | 'system-metrics'
  | 'linear-issues'
  | 'active-agents'
  | 'cron-summary'
  | 'quick-actions'
  | 'quick-notes'
  | 'usage-trends'
  | 'hermes-status'

export interface Widget {
  id: WidgetId
  title: string
  w: number
  h: number
  x: number
  y: number
}
