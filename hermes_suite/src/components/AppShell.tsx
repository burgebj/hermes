import { useUIStore } from '@/stores/uiStore'
import { Header } from './Header'
import { Sidebar } from './Sidebar'
import { CommandPalette } from './CommandPalette'
import { cn } from '@/lib/utils'

export function AppShell({ children }: { children: React.ReactNode }) {
  useUIStore()

  return (
    <div
      className={cn(
        'flex flex-col h-screen overflow-hidden bg-bg text-text transition-colors duration-200',
      )}
    >
      <Header />
      <div className="flex flex-1 overflow-hidden">
        <Sidebar />
        <main className="flex-1 overflow-auto" id="main-content">
          {children}
        </main>
      </div>
      <CommandPalette />
    </div>
  )
}
