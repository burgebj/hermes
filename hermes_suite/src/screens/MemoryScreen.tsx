export function MemoryScreen() {
  return (
    <div className="flex items-center justify-center flex-1 text-text-muted">
      <div className="text-center space-y-3">
        <svg width="48" height="48" viewBox="0 0 24 24" fill="none" className="mx-auto opacity-30">
          <path d="M12 2a9 9 0 00-9 9c0 3.1 1.6 5.8 4 7.4V22l4.5-2.5 4.5 2.5v-3.6a9 9 0 000-18z" stroke="currentColor" strokeWidth="1.5"/>
        </svg>
        <p className="text-sm">Memory Browser — coming soon</p>
        <p className="text-xs">Browse, search, and edit Hermes memory files</p>
      </div>
    </div>
  )
}
