export function AgentHubScreen() {
  return (
    <div className="flex items-center justify-center flex-1 text-text-muted">
      <div className="text-center space-y-3">
        <svg width="48" height="48" viewBox="0 0 24 24" fill="none" className="mx-auto opacity-30">
          <rect x="3" y="3" width="7" height="7" rx="1" stroke="currentColor" strokeWidth="1.5"/>
          <rect x="14" y="3" width="7" height="7" rx="1" stroke="currentColor" strokeWidth="1.5"/>
          <rect x="3" y="14" width="7" height="7" rx="1" stroke="currentColor" strokeWidth="1.5"/>
          <rect x="14" y="14" width="7" height="7" rx="1" stroke="currentColor" strokeWidth="1.5"/>
        </svg>
        <p className="text-sm">Agent Hub — coming soon</p>
        <p className="text-xs">Spawn, monitor, and orchestrate sub-agents</p>
      </div>
    </div>
  )
}
