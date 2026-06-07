import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface GatewayConfig {
  url: string
  token: string
  studioPassword: string
  isConfigured: boolean
  isAuthenticated: boolean
}

interface GatewayState extends GatewayConfig {
  setConfig: (config: Partial<GatewayConfig>) => void
  logout: () => void
  login: (password: string) => boolean
}

const STUDIO_PASSWORD = import.meta.env.VITE_STUDIO_PASSWORD as string | undefined

export const useGatewayStore = create<GatewayState>()(
  persist(
    (set, get) => ({
      url: (import.meta.env.VITE_HERMES_GATEWAY_URL as string | undefined) ?? 'http://localhost:8642',
      token: (import.meta.env.VITE_HERMES_GATEWAY_TOKEN as string | undefined) ?? '',
      studioPassword: STUDIO_PASSWORD ?? '',
      isConfigured: Boolean(STUDIO_PASSWORD || import.meta.env.VITE_STUDIO_PASSWORD),
      isAuthenticated: false,

      setConfig: (config) =>
        set((s) => ({
          ...s,
          ...config,
          isConfigured: Boolean(config.token || s.token),
        })),

      login: (password: string) => {
        const expected = get().studioPassword
        if (!expected || password === expected) {
          set({ isAuthenticated: true })
          return true
        }
        return false
      },

      logout: () => set({ isAuthenticated: false }),
    }),
    { name: 'hermes-suite-gateway' },
  ),
)
