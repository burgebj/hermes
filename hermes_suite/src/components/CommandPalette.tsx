import { useEffect, useRef, useState } from 'react'
import { useNavigate } from '@tanstack/react-router'
import { Search, Bot, MessageSquare, Wrench, Brain, Clock, Terminal, FolderOpen, LayoutDashboard } from 'lucide-react'
import { useUIStore } from '@/stores/uiStore'
import { cn } from '@/lib/utils'

const commands = [
  { id: 'dashboard', label: 'Go to Dashboard', description: 'Home screen with widgets', Icon: LayoutDashboard, path: '/' },
  { id: 'chat', label: 'New Chat', description: 'Start a new chat session', Icon: MessageSquare, path: '/chat' },
  { id: 'agent-hub', label: 'Open Agent Hub', description: 'Manage and spawn agents', Icon: Bot, path: '/agent-hub' },
  { id: 'skills', label: 'Skills Browser', description: 'Browse installed skills', Icon: Wrench, path: '/skills' },
  { id: 'memory', label: 'Memory Browser', description: 'Browse and edit memory files', Icon: Brain, path: '/memory' },
  { id: 'cron', label: 'Cron Manager', description: 'Manage scheduled jobs', Icon: Clock, path: '/cron' },
  { id: 'terminal', label: 'Terminal', description: 'Open integrated terminal', Icon: Terminal, path: '/terminal' },
  { id: 'files', label: 'File Explorer', description: 'Browse project files', Icon: FolderOpen, path: '/files' },
]

export function CommandPalette() {
  const { commandPaletteOpen, closeCommandPalette } = useUIStore()
  const [query, setQuery] = useState('')
  const [selectedIndex, setSelectedIndex] = useState(0)
  const inputRef = useRef<HTMLInputElement>(null)
  const navigate = useNavigate()

  const filtered = commands.filter(
    (c) =>
      c.label.toLowerCase().includes(query.toLowerCase()) ||
      c.description.toLowerCase().includes(query.toLowerCase()),
  )

  useEffect(() => {
    if (commandPaletteOpen) {
      setQuery('')
      setSelectedIndex(0)
      setTimeout(() => inputRef.current?.focus(), 50)
    }
  }, [commandPaletteOpen])

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault()
        commandPaletteOpen ? closeCommandPalette() : useUIStore.getState().openCommandPalette()
      }
      if (!commandPaletteOpen) return
      if (e.key === 'Escape') closeCommandPalette()
      if (e.key === 'ArrowDown') setSelectedIndex((i) => Math.min(i + 1, filtered.length - 1))
      if (e.key === 'ArrowUp') setSelectedIndex((i) => Math.max(i - 1, 0))
      if (e.key === 'Enter' && filtered[selectedIndex]) {
        navigate({ to: filtered[selectedIndex].path })
        closeCommandPalette()
      }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [commandPaletteOpen, filtered, selectedIndex])

  if (!commandPaletteOpen) return null

  return (
    <div
      className="fixed inset-0 z-50 flex items-start justify-center pt-[15vh]"
      onClick={(e) => e.target === e.currentTarget && closeCommandPalette()}
    >
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" />

      {/* Modal */}
      <div className="relative w-full max-w-lg bg-surface border border-border rounded-xl shadow-2xl overflow-hidden animate-fade-in">
        {/* Search input */}
        <div className="flex items-center gap-3 px-4 py-3 border-b border-border">
          <Search size={16} className="text-text-muted shrink-0" />
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={(e) => { setQuery(e.target.value); setSelectedIndex(0) }}
            placeholder="Search commands..."
            className="flex-1 bg-transparent text-sm text-text placeholder:text-text-muted outline-none"
          />
          <kbd className="text-xs text-text-muted border border-border rounded px-1.5 py-0.5">ESC</kbd>
        </div>

        {/* Results */}
        <ul className="max-h-64 overflow-y-auto py-2">
          {filtered.length === 0 && (
            <li className="px-4 py-3 text-sm text-text-muted">No commands found</li>
          )}
          {filtered.map((cmd, i) => (
            <li key={cmd.id}>
              <button
                onClick={() => { navigate({ to: cmd.path }); closeCommandPalette() }}
                onMouseEnter={() => setSelectedIndex(i)}
                className={cn(
                  'w-full flex items-center gap-3 px-4 py-2.5 text-sm transition-colors',
                  i === selectedIndex ? 'bg-accent/10 text-accent' : 'text-text',
                )}
              >
                <cmd.Icon size={15} className="shrink-0" />
                <div className="flex flex-col items-start">
                  <span className="font-medium">{cmd.label}</span>
                  <span className="text-xs text-text-muted">{cmd.description}</span>
                </div>
                {i === selectedIndex && (
                  <kbd className="ml-auto text-xs text-text-muted border border-border rounded px-1.5">↵</kbd>
                )}
              </button>
            </li>
          ))}
        </ul>
      </div>
    </div>
  )
}
