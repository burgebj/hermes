export function CronScreen() {
  return (
    <div className="flex items-center justify-center flex-1 text-text-muted">
      <div className="text-center space-y-3">
        <svg width="48" height="48" viewBox="0 0 24 24" fill="none" className="mx-auto opacity-30">
          <circle cx="12" cy="12" r="9" stroke="currentColor" strokeWidth="1.5"/>
          <path d="M12 7v5l3 3" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
        </svg>
        <p className="text-sm">Cron Manager — coming soon</p>
        <p className="text-xs">Schedule and manage recurring Hermes tasks</p>
      </div>
    </div>
  )
}
