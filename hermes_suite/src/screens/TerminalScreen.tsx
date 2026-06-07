export function TerminalScreen() {
  return (
    <div className="flex items-center justify-center flex-1 text-text-muted">
      <div className="text-center space-y-3">
        <svg width="48" height="48" viewBox="0 0 24 24" fill="none" className="mx-auto opacity-30">
          <rect x="2" y="4" width="20" height="16" rx="2" stroke="currentColor" strokeWidth="1.5"/>
          <path d="M6 9l3 3-3 3M12 15h5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
        </svg>
        <p className="text-sm">Terminal — coming soon</p>
        <p className="text-xs">Integrated terminal with xterm.js</p>
      </div>
    </div>
  )
}
