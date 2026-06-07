import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export type Theme = 'ops-dark' | 'paper-light' | 'premium-dark'

interface UIState {
  theme: Theme
  sidebarCollapsed: boolean
  commandPaletteOpen: boolean
  activePanel: string | null
  setTheme: (theme: Theme) => void
  toggleSidebar: () => void
  openCommandPalette: () => void
  closeCommandPalette: () => void
  setActivePanel: (panel: string | null) => void
}

export const useUIStore = create<UIState>()(
  persist(
    (set) => ({
      theme: 'ops-dark',
      sidebarCollapsed: false,
      commandPaletteOpen: false,
      activePanel: null,

      setTheme: (theme) => {
        document.documentElement.className = theme
        set({ theme })
      },
      toggleSidebar: () => set((s) => ({ sidebarCollapsed: !s.sidebarCollapsed })),
      openCommandPalette: () => set({ commandPaletteOpen: true }),
      closeCommandPalette: () => set({ commandPaletteOpen: false }),
      setActivePanel: (panel) => set({ activePanel: panel }),
    }),
    {
      name: 'hermes-suite-ui',
      partialize: (s) => ({
        theme: s.theme,
        sidebarCollapsed: s.sidebarCollapsed,
      }),
    },
  ),
)
