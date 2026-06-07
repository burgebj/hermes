/**
 * Hermes Gateway API client.
 * All calls are proxied through Vite dev server (/api/gateway/* → :8642)
 */

const BASE = '/api/gateway'
const GATEWAY_TOKEN = import.meta.env.VITE_HERMES_GATEWAY_TOKEN as string | undefined

function headers(): HeadersInit {
  const h: HeadersInit = { 'Content-Type': 'application/json' }
  if (GATEWAY_TOKEN) h['Authorization'] = `Bearer ${GATEWAY_TOKEN}`
  return h
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, { ...init, headers: { ...headers(), ...init?.headers } })
  if (!res.ok) throw new Error(`Gateway ${res.status}: ${await res.text()}`)
  return res.json() as Promise<T>
}

// ─── Agent types ──────────────────────────────────────────────

export interface Agent {
  id: string
  name: string
  status: 'idle' | 'running' | 'paused' | 'stopped'
  model?: string
  startedAt?: string
  lastSeen?: string
  behaviours?: string[]
  parentId?: string
}

export interface ListAgentsResponse {
  agents: Agent[]
}

export interface SpawnAgentRequest {
  name: string
  model?: string
  behaviours?: string[]
  prompt?: string
}

export const gateway = {
  // Agents
  listAgents: () => request<ListAgentsResponse>('/agents'),
  spawnAgent: (body: SpawnAgentRequest) =>
    request<Agent>('/agents', { method: 'POST', body: JSON.stringify(body) }),
  pauseAgent: (id: string) =>
    request<Agent>(`/agents/${id}/pause`, { method: 'POST' }),
  resumeAgent: (id: string) =>
    request<Agent>(`/agents/${id}/resume`, { method: 'POST' }),
  abortAgent: (id: string) =>
    request<void>(`/agents/${id}/abort`, { method: 'POST' }),

  // Chat completions (proxied to upstream LLM API)
  chat: (body: object) =>
    request<unknown>('/chat', { method: 'POST', body: JSON.stringify(body) }),

  // MCP tools
  listTools: () => request<unknown>('/mcp/tools'),
  callTool: (name: string, args: Record<string, unknown>) =>
    request<unknown>('/mcp/call', {
      method: 'POST',
      body: JSON.stringify({ name, args }),
    }),

  // Gateway info
  info: () => request<{ version: string; uptime: number }>('/info'),
}
