import { Sun, Moon, Sparkles } from 'lucide-react'
import { useUIStore, type Theme } from '@/stores/uiStore'
import { cn } from '@/lib/utils'

const themes: { id: Theme; label: string; Icon: React.FC<{ size: number }> }[] = [
  { id: 'ops-dark', label: 'Ops Dark', Icon: (p) => <Moon {...p} /> },
  { id: 'paper-light', label: 'Paper Light', Icon: (p) => <Sun {...p} /> },
  { id: 'premium-dark', label: 'Premium Dark', Icon: (p) => <Sparkles {...p} /> },
]

export function ThemeToggle() {
  const { theme, setTheme } = useUIStore()

  return (
    <div className="flex items-center gap-1 p-0.5 rounded-lg border border-border bg-surface-raised">
      {themes.map(({ id, label, Icon }) => (
        <button
          key={id}
          onClick={() => setTheme(id)}
          title={label}
          className={cn(
            'p-1.5 rounded-md transition-all duration-150',
            theme === id
              ? 'bg-accent text-bg shadow-sm'
              : 'text-text-muted hover:text-text',
          )}
        >
          <Icon size={13} />
        </button>
      ))}
    </div>
  )
}
