import {
  createRouter,
  createRootRoute,
  createRoute,
  Outlet,
} from '@tanstack/react-router'
import { AppShell } from '@/components/AppShell'
import { DashboardScreen } from '@/screens/DashboardScreen'
import { ChatScreen } from '@/screens/ChatScreen'
import { AgentHubScreen } from '@/screens/AgentHubScreen'
import { SkillsScreen } from '@/screens/SkillsScreen'
import { MemoryScreen } from '@/screens/MemoryScreen'
import { CronScreen } from '@/screens/CronScreen'
import { TerminalScreen } from '@/screens/TerminalScreen'
import { FilesScreen } from '@/screens/FilesScreen'

// Root route renders AppShell with an Outlet for child routes
const rootRoute = createRootRoute({
  component: () => (
    <AppShell>
      <Outlet />
    </AppShell>
  ),
})

// ─── Child routes ───────────────────────────────────────────────
const indexRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/',
  component: DashboardScreen,
})

const dashboardRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/dashboard',
  component: DashboardScreen,
})

const chatRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/chat',
  component: ChatScreen,
})

const agentHubRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/agent-hub',
  component: AgentHubScreen,
})

const skillsRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/skills',
  component: SkillsScreen,
})

const memoryRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/memory',
  component: MemoryScreen,
})

const cronRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/cron',
  component: CronScreen,
})

const terminalRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/terminal',
  component: TerminalScreen,
})

const filesRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/files',
  component: FilesScreen,
})

// ─── Build route tree ───────────────────────────────────────────
const routeTree = rootRoute.addChildren([
  indexRoute,
  dashboardRoute,
  chatRoute,
  agentHubRoute,
  skillsRoute,
  memoryRoute,
  cronRoute,
  terminalRoute,
  filesRoute,
])

export const router = createRouter({ routeTree })

declare module '@tanstack/react-router' {
  interface Register {
    router: typeof router
  }
}
