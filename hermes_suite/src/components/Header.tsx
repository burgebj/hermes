import { Link } from '@tanstack/react-router'
import { Settings, Bell, Wifi, WifiOff } from 'lucide-react'
import { useUIStore } from '@/stores/uiStore'
import { useGatewayStore } from '@/stores/gatewayStore'
import { cn } from '@/lib/utils'
import { ThemeToggle } from './ThemeToggle'

export function Header() {
  const { openCommandPalette } = useUIStore()
  const { isConfigured } = useGatewayStore()

  return (
    <header className="flex items-center justify-between h-12 px-4 border-b border-border bg-surface shrink-0">
      {/* Left: logo + brand */}
      <div className="flex items-center gap-3">
        <Link to="/" className="flex items-center gap-2 font-semibold text-accent hover:text-accent/80 transition-colors">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M12 2L3 7v10l9 5 9-5V7L12 2z" stroke="currentColor" strokeWidth="2" strokeLinejoin="round"/>
            <path d="M12 2v20M3 7l9 5 9-5" stroke="currentColor" strokeWidth="2" strokeLinejoin="round"/>
          </svg>
          <span className="text-sm tracking-wide">HermesSuite</span>
        </Link>

        {/* Gateway status */}
        <div className={cn(
          'flex items-center gap-1.5 text-xs px-2 py-0.5 rounded-full border',
          isConfigured
            ? 'border-success/30 text-success bg-success/10'
            : 'border-danger/30 text-danger bg-danger/10',
        )}>
          {isConfigured ? <Wifi size={10} /> : <WifiOff size={10} />}
          <span>{isConfigured ? 'Gateway connected' : 'No gateway'}</span>
        </div>
      </div>

      {/* Right: actions */}
      <div className="flex items-center gap-2">
        <button
          onClick={openCommandPalette}
          className="flex items-center gap-1.5 text-xs text-text-muted hover:text-text px-2 py-1 rounded border border-border hover:border-accent/50 transition-colors"
        >
          <span>⌘K</span>
        </button>

        <ThemeToggle />

        <button className="relative p-1.5 rounded text-text-muted hover:text-text hover:bg-surface-raised transition-colors">
          <Bell size={16} />
          {/* Notification dot */}
          <span className="absolute top-1 right-1 w-1.5 h-1.5 rounded-full bg-accent" />
        </button>

        <button className="p-1.5 rounded text-text-muted hover:text-text hover:bg-surface-raised transition-colors">
          <Settings size={16} />
        </button>
      </div>
    </header>
  )
}
