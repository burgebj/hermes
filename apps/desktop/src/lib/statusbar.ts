import { useEffect, useState } from 'react'

import type { UsageStats } from '@/types/hermes'

export function formatK(value: number): string {
  if (!Number.isFinite(value) || value <= 0) {
    return '0'
  }

  if (value >= 1_000_000) {
    return `${(value / 1_000_000).toFixed(1)}M`
  }

  if (value >= 1_000) {
    return `${(value / 1_000).toFixed(1)}k`
  }

  return `${Math.round(value)}`
}

export function formatDuration(elapsedMs: number): string {
  const totalSeconds = Math.max(0, Math.floor(elapsedMs / 1000))
  const seconds = totalSeconds % 60
  const minutes = Math.floor(totalSeconds / 60) % 60
  const hours = Math.floor(totalSeconds / 3600)
  const ss = String(seconds).padStart(2, '0')
  const mm = String(minutes).padStart(2, '0')

  return hours > 0 ? `${hours}:${mm}:${ss}` : `${minutes}:${ss}`
}

export function compactPath(path: string, max = 44): string {
  const trimmed = path.trim()

  if (trimmed.length <= max) {
    return trimmed
  }

  const segments = trimmed.split('/').filter(Boolean)

  if (segments.length < 2) {
    return `…${trimmed.slice(-(max - 1))}`
  }

  const tail = segments.slice(-2).join('/')

  return tail.length + 2 >= max ? `…${tail.slice(-(max - 1))}` : `…/${tail}`
}

export function contextBar(percent: number | undefined, width = 10): string {
  const bounded = Math.max(0, Math.min(100, percent ?? 0))
  const filled = Math.round((bounded / 100) * width)

  return `${'█'.repeat(filled)}${'░'.repeat(width - filled)}`
}

interface UsageCacheLabel {
  detail?: string
  label: string
  title: string
}

function usageCacheRatioPercent(usage: UsageStats, read: number, write: number): number {
  if (Number.isFinite(usage.cache_hit_ratio)) {
    const raw = usage.cache_hit_ratio ?? 0
    const percent = raw <= 1 ? raw * 100 : raw

    return Math.max(0, Math.min(100, Math.round(percent)))
  }

  const inputTotal = Math.max(0, usage.input || 0) + read + write

  if (inputTotal <= 0) {
    return 0
  }

  return Math.max(0, Math.min(100, Math.round((read / inputTotal) * 100)))
}

export function usageCacheLabel(usage: UsageStats): UsageCacheLabel | null {
  const read = Math.max(0, usage.cache_read ?? usage.cache_read_tokens ?? 0)
  const write = Math.max(0, usage.cache_write ?? usage.cache_write_tokens ?? 0)

  if (read <= 0 && write <= 0) {
    return null
  }

  const percent = usageCacheRatioPercent(usage, read, write)

  const detail = [
    read > 0 ? `${formatK(read)} read` : null,
    write > 0 ? `${formatK(write)} write` : null
  ]
    .filter(Boolean)
    .join(' / ')

  return {
    detail: detail || undefined,
    label: `cache ${percent}%`,
    title: `Cache hit ${percent}%; read ${formatK(read)} tokens; write ${formatK(write)} tokens`
  }
}

export function usageContextLabel(usage: UsageStats): string {
  if (usage.context_max) {
    return `${formatK(usage.context_used ?? 0)}/${formatK(usage.context_max)}`
  }

  return usage.total > 0 ? `${formatK(usage.total)} tok` : ''
}

export function contextBarLabel(usage: UsageStats): string {
  if (!usage.context_max) {
    return ''
  }

  const pct = Math.max(0, Math.min(100, Math.round(usage.context_percent ?? 0)))

  return `[${contextBar(usage.context_percent)}] ${pct}%`
}

export function LiveDuration({ since }: { since: number | null | undefined }) {
  const [now, setNow] = useState(() => Date.now())

  useEffect(() => {
    if (!since) {
      return
    }

    const tick = () => setNow(Date.now())
    tick()
    const timer = window.setInterval(tick, 1000)

    return () => window.clearInterval(timer)
  }, [since])

  return since ? formatDuration(now - since) : null
}
