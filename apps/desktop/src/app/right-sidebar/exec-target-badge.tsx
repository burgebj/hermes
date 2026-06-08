import { useStore } from '@nanostores/react'
import { useEffect, useState } from 'react'

import { Codicon } from '@/components/ui/codicon'
import { cn } from '@/lib/utils'
import type { DesktopHostInfo } from '@/global'
import { $connection, $currentCwd } from '@/store/session'

/**
 * Execution-target badge for the Terminal / File Explorer surfaces.
 *
 * Both surfaces run against the *local* machine — the desktop's Terminal spawns
 * a local PTY and the File Explorer reads the local filesystem (see the
 * `hermes:terminal:*` and `hermes:fs:*` handlers in electron/main.cjs). When the
 * chat session targets a remote gateway, that creates a split-brain where chat,
 * terminal, and files can appear to share one machine while actually targeting
 * different ones. This badge makes the local scope explicit, and warns loudly
 * when the chat backend is remote so commands/files here aren't mistaken for
 * remote ones (#38369).
 */

// Host identity never changes within a run, so fetch it once and share the
// promise across every mount instead of re-hitting IPC per badge.
let hostInfoPromise: Promise<DesktopHostInfo | null> | null = null

function loadHostInfo(): Promise<DesktopHostInfo | null> {
  if (!hostInfoPromise) {
    const getHostInfo = window.hermesDesktop?.getHostInfo
    hostInfoPromise = getHostInfo ? getHostInfo().catch(() => null) : Promise.resolve(null)
  }

  return hostInfoPromise
}

function remoteHostLabel(baseUrl: string | undefined): string {
  if (!baseUrl) {
    return 'remote backend'
  }

  try {
    return new URL(baseUrl).host || 'remote backend'
  } catch {
    return 'remote backend'
  }
}

export function ExecTargetBadge({ className }: { className?: string }) {
  const connection = useStore($connection)
  const cwd = useStore($currentCwd).trim()
  const [hostInfo, setHostInfo] = useState<DesktopHostInfo | null>(null)

  useEffect(() => {
    let active = true
    void loadHostInfo().then(info => {
      if (active) {
        setHostInfo(info)
      }
    })

    return () => {
      active = false
    }
  }, [])

  const isRemote = connection?.mode === 'remote'
  const hostname = hostInfo?.hostname?.trim() || 'this machine'
  const remoteHost = remoteHostLabel(connection?.baseUrl)

  // In remote mode the Terminal and File Explorer now route over SSH to the
  // machine the agent runs on, so they genuinely target the remote host — the
  // badge says so (green). In local mode they run on this machine (neutral).
  const title = isRemote
    ? `Terminal & file browser run on the remote backend (${remoteHost}) over SSH — ` +
      `the same machine the chat session targets.` +
      (cwd ? `\nWorking directory: ${cwd}` : '')
    : `Terminal & file browser run on this machine (${hostname}).` + (cwd ? `\nWorking directory: ${cwd}` : '')

  return (
    <span
      className={cn(
        'flex min-w-0 items-center gap-1 rounded px-1 text-[0.6875rem]',
        isRemote ? 'text-emerald-500' : 'text-(--ui-text-tertiary)',
        className
      )}
      title={title}
    >
      <Codicon className="shrink-0" name={isRemote ? 'remote' : 'device-desktop'} size="0.75rem" />
      <span className="truncate">{isRemote ? `Remote · ${remoteHost}` : 'Local'}</span>
    </span>
  )
}
