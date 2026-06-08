import { atom } from 'nanostores'

/**
 * Federated Apps Wiring/Operator Topology — Slice 06: Normalized State Artifact
 *
 * This store manages the normalized state for federated applications and their
 * operator wiring topology. It tracks:
 * - Registered apps with their metadata and capabilities
 * - Operator nodes within each app
 * - Wiring connections (edges) between operators across apps
 * - Connection states and health status
 */

/** Connection state for an operator or wire */
export type ConnectionState =
  | 'available'      // Ready to accept work
  | 'busy'           // Currently processing
  | 'error'          // Error state (retryable)
  | 'unavailable'    // Unavailable (non-retryable)
  | 'connecting'     // Initial connection in progress
  | 'disconnecting'  // Graceful shutdown in progress

/** Wire protocol for operator communication */
export type WireProtocol = 'ipc' | 'ws' | 'http' | 'grpc' | 'internal'

/** Wire direction for data flow */
export type WireDirection = 'unidirectional' | 'bidirectional'

/** Capability flags for operators */
export interface OperatorCapabilities {
  canStream: boolean
  canBatch: boolean
  canDelegate: boolean
  supportsPriority: boolean
  maxConcurrent: number
}

/** A federated app registration */
export interface FederatedApp {
  id: string
  name: string
  version: string
  url?: string            // Optional remote URL for external apps
  protocol: WireProtocol
  capabilities: {
    canHostOperators: boolean
    canProxy: boolean
    maxOperators: number
  }
  state: ConnectionState
  registeredAt: number
  lastHeartbeatAt: number
  metadata: Record<string, unknown>
}

/** An operator node within a federated app */
export interface OperatorNode {
  id: string
  appId: string           // Reference to parent FederatedApp
  name: string
  type: string            // Operator type (e.g., 'llm', 'tool', 'gateway')
  capabilities: OperatorCapabilities
  state: ConnectionState
  currentLoad: number     // 0-100 percentage
  queueDepth: number      // Current queued items
  errorMessage?: string   // Present when state is 'error'
  lastActivityAt: number
  metadata: Record<string, unknown>
}

/** A wiring connection (edge) between operators */
export interface OperatorWire {
  id: string
  sourceAppId: string
  sourceOperatorId: string
  targetAppId: string
  targetOperatorId: string
  protocol: WireProtocol
  direction: WireDirection
  state: ConnectionState
  latencyMs?: number      // Last measured latency
  throughputBps?: number  // Last measured throughput
  establishedAt: number
  lastActivityAt: number
  metadata: Record<string, unknown>
}

/** Normalized state artifact for the entire topology */
export interface FederatedAppsState {
  apps: Record<string, FederatedApp>      // Keyed by app id
  operators: Record<string, OperatorNode>  // Keyed by operator id
  wires: Record<string, OperatorWire>     // Keyed by wire id
  version: number                          // State version for optimistic updates
}

/** Wire endpoint reference (for creating wires) */
export interface WireEndpoint {
  appId: string
  operatorId: string
}

/** Initial empty state */
const initialState: FederatedAppsState = {
  apps: {},
  operators: {},
  wires: {},
  version: 0
}

/** Main state atom */
export const $federatedApps = atom<FederatedAppsState>(initialState)

/** Get current state version (for conflict detection) */
export function getStateVersion(): number {
  return $federatedApps.get().version
}

/** Register a new federated app */
export function registerApp(app: Omit<FederatedApp, 'registeredAt' | 'lastHeartbeatAt'>): FederatedApp {
  const state = $federatedApps.get()
  const now = Date.now()

  const newApp: FederatedApp = {
    ...app,
    registeredAt: now,
    lastHeartbeatAt: now
  }

  $federatedApps.set({
    ...state,
    apps: { ...state.apps, [app.id]: newApp },
    version: state.version + 1
  })

  return newApp
}

/** Unregister an app and all its operators/wires */
export function unregisterApp(appId: string): boolean {
  const state = $federatedApps.get()

  if (!state.apps[appId]) {
    return false
  }

  // Remove all operators belonging to this app
  const operators = { ...state.operators }

  for (const [id, op] of Object.entries(operators)) {
    if (op.appId === appId) {
      delete operators[id]
    }
  }

  // Remove all wires connected to this app's operators
  const wires = { ...state.wires }

  for (const [id, wire] of Object.entries(wires)) {
    if (wire.sourceAppId === appId || wire.targetAppId === appId) {
      delete wires[id]
    }
  }

  // Remove the app itself
  const apps = { ...state.apps }
  delete apps[appId]

  $federatedApps.set({
    apps,
    operators,
    wires,
    version: state.version + 1
  })

  return true
}

/** Update app state and heartbeat */
export function updateAppState(appId: string, state: ConnectionState, metadata?: Record<string, unknown>): boolean {
  const current = $federatedApps.get()
  const app = current.apps[appId]

  if (!app) {
    return false
  }

  $federatedApps.set({
    ...current,
    apps: {
      ...current.apps,
      [appId]: {
        ...app,
        state,
        lastHeartbeatAt: Date.now(),
        metadata: metadata ? { ...app.metadata, ...metadata } : app.metadata
      }
    },
    version: current.version + 1
  })

  return true
}

/** Register an operator node */
export function registerOperator(operator: Omit<OperatorNode, 'lastActivityAt'>): OperatorNode {
  const state = $federatedApps.get()
  const now = Date.now()

  const newOperator: OperatorNode = {
    ...operator,
    lastActivityAt: now
  }

  $federatedApps.set({
    ...state,
    operators: { ...state.operators, [operator.id]: newOperator },
    version: state.version + 1
  })

  return newOperator
}

/** Unregister an operator and its connected wires */
export function unregisterOperator(operatorId: string): boolean {
  const state = $federatedApps.get()

  if (!state.operators[operatorId]) {
    return false
  }

  const operators = { ...state.operators }
  delete operators[operatorId]

  // Remove all wires connected to this operator
  const wires = { ...state.wires }

  for (const [id, wire] of Object.entries(wires)) {
    if (wire.sourceOperatorId === operatorId || wire.targetOperatorId === operatorId) {
      delete wires[id]
    }
  }

  $federatedApps.set({
    ...state,
    operators,
    wires,
    version: state.version + 1
  })

  return true
}

/** Update operator state and metrics */
export function updateOperatorState(
  operatorId: string,
  updates: Partial<Pick<OperatorNode, 'state' | 'currentLoad' | 'queueDepth' | 'errorMessage'>>
): boolean {
  const state = $federatedApps.get()
  const operator = state.operators[operatorId]

  if (!operator) {
    return false
  }

  $federatedApps.set({
    ...state,
    operators: {
      ...state.operators,
      [operatorId]: {
        ...operator,
        ...updates,
        lastActivityAt: Date.now()
      }
    },
    version: state.version + 1
  })

  return true
}

/** Create a wire between two operators */
export function createWire(
  id: string,
  source: WireEndpoint,
  target: WireEndpoint,
  protocol: WireProtocol,
  direction: WireDirection = 'bidirectional'
): OperatorWire {
  const state = $federatedApps.get()
  const now = Date.now()

  const wire: OperatorWire = {
    id,
    sourceAppId: source.appId,
    sourceOperatorId: source.operatorId,
    targetAppId: target.appId,
    targetOperatorId: target.operatorId,
    protocol,
    direction,
    state: 'connecting',
    establishedAt: now,
    lastActivityAt: now,
    metadata: {}
  }

  $federatedApps.set({
    ...state,
    wires: { ...state.wires, [id]: wire },
    version: state.version + 1
  })

  return wire
}

/** Remove a wire */
export function removeWire(wireId: string): boolean {
  const state = $federatedApps.get()

  if (!state.wires[wireId]) {
    return false
  }

  const wires = { ...state.wires }
  delete wires[wireId]

  $federatedApps.set({
    ...state,
    wires,
    version: state.version + 1
  })

  return true
}

/** Update wire state and metrics */
export function updateWireState(
  wireId: string,
  updates: Partial<Pick<OperatorWire, 'state' | 'latencyMs' | 'throughputBps'>>
): boolean {
  const state = $federatedApps.get()
  const wire = state.wires[wireId]

  if (!wire) {
    return false
  }

  $federatedApps.set({
    ...state,
    wires: {
      ...state.wires,
      [wireId]: {
        ...wire,
        ...updates,
        lastActivityAt: Date.now()
      }
    },
    version: state.version + 1
  })

  return true
}

/** Get operators for a specific app */
export function getAppOperators(appId: string): OperatorNode[] {
  const state = $federatedApps.get()

  return Object.values(state.operators).filter(op => op.appId === appId)
}

/** Get wires for a specific operator (both source and target) */
export function getOperatorWires(operatorId: string): OperatorWire[] {
  const state = $federatedApps.get()

  return Object.values(state.wires).filter(
    wire => wire.sourceOperatorId === operatorId || wire.targetOperatorId === operatorId
  )
}

/** Get the topology graph for visualization (nodes + edges) */
export function getTopologyGraph(): {
  nodes: Array<{ id: string; type: 'app' | 'operator'; data: FederatedApp | OperatorNode }>
  edges: Array<{ id: string; source: string; target: string; data: OperatorWire }>
} {
  const state = $federatedApps.get()

  const nodes: Array<{ id: string; type: 'app' | 'operator'; data: FederatedApp | OperatorNode }> = [
    ...Object.values(state.apps).map(app => ({ id: app.id, type: 'app' as const, data: app })),
    ...Object.values(state.operators).map(op => ({ id: op.id, type: 'operator' as const, data: op }))
  ]

  const edges = Object.values(state.wires).map(wire => ({
    id: wire.id,
    source: wire.sourceOperatorId,
    target: wire.targetOperatorId,
    data: wire
  }))

  return { nodes, edges }
}

/** Get available operators (ready to accept work) */
export function getAvailableOperators(): OperatorNode[] {
  const state = $federatedApps.get()

  return Object.values(state.operators).filter(
    op => op.state === 'available' && op.currentLoad < 90
  )
}

/** Check if a path exists between two operators (for routing decisions) */
export function hasPath(sourceId: string, targetId: string): boolean {
  const state = $federatedApps.get()

  if (sourceId === targetId) {return true}

  const visited = new Set<string>()
  const queue = [sourceId]

  while (queue.length > 0) {
    const current = queue.shift()!

    if (visited.has(current)) {continue}
    visited.add(current)

    // Find all wires from current operator
    const wires = Object.values(state.wires).filter(
      wire => wire.sourceOperatorId === current && wire.state === 'available'
    )

    for (const wire of wires) {
      if (wire.targetOperatorId === targetId) {
        return true
      }

      if (!visited.has(wire.targetOperatorId)) {
        queue.push(wire.targetOperatorId)
      }
    }
  }

  return false
}

/** Get routing path from source to target (if exists) */
export function getRoutingPath(sourceId: string, targetId: string): string[] | null {
  const state = $federatedApps.get()

  if (sourceId === targetId) {return [sourceId]}

  const visited = new Set<string>()
  const parent = new Map<string, string>()
  const queue = [sourceId]

  while (queue.length > 0) {
    const current = queue.shift()!

    if (visited.has(current)) {continue}
    visited.add(current)

    const wires = Object.values(state.wires).filter(
      wire => wire.sourceOperatorId === current && wire.state === 'available'
    )

    for (const wire of wires) {
      if (!visited.has(wire.targetOperatorId)) {
        parent.set(wire.targetOperatorId, current)
        queue.push(wire.targetOperatorId)

        if (wire.targetOperatorId === targetId) {
          // Reconstruct path
          const path: string[] = [targetId]
          let node = targetId

          while (parent.has(node)) {
            node = parent.get(node)!
            path.unshift(node)
          }

          return path
        }
      }
    }
  }

  return null
}

/** Clear all federated apps state (for testing/reset) */
export function clearFederatedApps(): void {
  $federatedApps.set(initialState)
}

/** Export state as JSON-serializable artifact */
export function exportState(): FederatedAppsState {
  return $federatedApps.get()
}

/** Import state from JSON artifact */
export function importState(state: FederatedAppsState): void {
  $federatedApps.set({
    ...state,
    version: (state.version || 0) + 1 // Bump version on import
  })
}
