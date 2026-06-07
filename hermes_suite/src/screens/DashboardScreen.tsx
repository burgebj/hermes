import { useQuery } from '@tanstack/react-query'
import { gateway } from '@/lib/gateway'
import { Bot, Clock, AlertCircle } from 'lucide-react'

const DEFAULT_WIDGETS = [
  { id: 'hermes-status', title: 'Hermes Status', x: 0, y: 0, w: 4, h: 3 },
  { id: 'active-agents', title: 'Active Agents', x: 4, y: 0, w: 4, h: 3 },
  { id: 'cron-summary', title: 'Cron Jobs', x: 8, y: 0, w: 4, h: 3 },
  { id: 'quick-actions', title: 'Quick Actions', x: 0, y: 3, w: 6, h: 4 },
  { id: 'quick-notes', title: 'Quick Notes', x: 6, y: 3, w: 6, h: 4 },
]

export function DashboardScreen() {
  const { data: info } = useQuery({
    queryKey: ['gateway-info'],
    queryFn: () => gateway.info(),
    refetchInterval: 30_000,
  })

  return (
    <div className="p-6 space-y-6">
      {/* Page header */}
      <div>
        <h1 className="text-xl font-semibold">Dashboard</h1>
        <p className="text-sm text-text-muted mt-1">HermesSuite command centre overview</p>
      </div>

      {/* Status strip */}
      <div className="grid grid-cols-3 gap-4">
        <div className="flex items-center gap-3 p-4 rounded-xl border border-border bg-surface">
          <div className="p-2 rounded-lg bg-accent/10 text-accent">
            <Bot size={20} />
          </div>
          <div>
            <p className="text-xs text-text-muted">Gateway Status</p>
            <p className="text-sm font-medium text-success">Connected</p>
          </div>
        </div>

        <div className="flex items-center gap-3 p-4 rounded-xl border border-border bg-surface">
          <div className="p-2 rounded-lg bg-accent-secondary/10 text-accent-secondary">
            <Clock size={20} />
          </div>
          <div>
            <p className="text-xs text-text-muted">Uptime</p>
            <p className="text-sm font-medium">
              {info?.uptime ? `${Math.floor(info.uptime / 3600)}h ${Math.floor((info.uptime % 3600) / 60)}m` : '—'}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3 p-4 rounded-xl border border-border bg-surface">
          <div className="p-2 rounded-lg bg-warning/10 text-warning">
            <AlertCircle size={20} />
          </div>
          <div>
            <p className="text-xs text-text-muted">Version</p>
            <p className="text-sm font-medium">{info?.version ?? 'v0.1.0'}</p>
          </div>
        </div>
      </div>

      {/* Widget grid — placeholder layout */}
      <div className="grid grid-cols-2 gap-4">
        {DEFAULT_WIDGETS.map((widget) => (
          <div
            key={widget.id}
            className="p-4 rounded-xl border border-border bg-surface min-h-[120px]"
          >
            <h3 className="text-xs font-medium text-text-muted uppercase tracking-wider mb-3">
              {widget.title}
            </h3>
            <div className="text-sm text-text-muted italic">
              Widget content coming soon
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
