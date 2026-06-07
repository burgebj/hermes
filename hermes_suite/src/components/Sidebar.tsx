import { Link, useRouterState } from '@tanstack/react-router'
import {
  LayoutDashboard,
  MessageSquare,
  Bot,
  Wrench,
  Brain,
  Clock,
  Terminal,
  FolderOpen,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react'
import { useUIStore } from '@/stores/uiStore'
import { cn } from '@/lib/utils'

const navItems = [
  { to: '/', Icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/chat', Icon: MessageSquare, label: 'Chat' },
  { to: '/agent-hub', Icon: Bot, label: 'Agent Hub' },
  { to: '/skills', Icon: Wrench, label: 'Skills' },
  { to: '/memory', Icon: Brain, label: 'Memory' },
  { to: '/cron', Icon: Clock, label: 'Cron' },
  { to: '/terminal', Icon: Terminal, label: 'Terminal' },
  { to: '/files', Icon: FolderOpen, label: 'Files' },
]

export function Sidebar() {
  const { sidebarCollapsed, toggleSidebar } = useUIStore()
  const routerState = useRouterState()
  const currentPath = routerState.location.pathname

  return (
    <aside
      className={cn(
        'flex flex-col border-r border-border bg-surface shrink-0 transition-all duration-200 relative',
        sidebarCollapsed ? 'w-14' : 'w-48',
      )}
    >
      {/* Nav items */}
      <nav className="flex flex-col gap-0.5 p-2 flex-1">
        {navItems.map(({ to, Icon, label }) => {
          const isActive = to === '/' ? currentPath === '/' : currentPath.startsWith(to)
          return (
            <Link
              key={to}
              to={to}
              title={sidebarCollapsed ? label : undefined}
              className={cn(
                'flex items-center gap-3 px-2.5 py-2 rounded-lg text-sm transition-colors',
                isActive
                  ? 'bg-accent/15 text-accent font-medium'
                  : 'text-text-muted hover:text-text hover:bg-surface-raised',
              )}
            >
              <Icon size={16} className="shrink-0" />
              {!sidebarCollapsed && <span>{label}</span>}
              {isActive && !sidebarCollapsed && (
                <span className="ml-auto w-1.5 h-1.5 rounded-full bg-accent" />
              )}
            </Link>
          )
        })}
      </nav>

      {/* Collapse toggle */}
      <button
        onClick={toggleSidebar}
        className="flex items-center justify-center h-10 border-t border-border text-text-muted hover:text-text transition-colors"
      >
        {sidebarCollapsed ? <ChevronRight size={14} /> : <ChevronLeft size={14} />}
      </button>
    </aside>
  )
}
