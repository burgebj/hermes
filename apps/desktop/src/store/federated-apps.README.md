# Federated Apps Wiring/Operator Topology

## Slice 06: Normalized State Artifact

This module implements the normalized state artifact for federated applications
and their operator wiring topology in the Hermes desktop app.

## Overview

The federated apps system enables distributed applications to register themselves,
expose operators (capabilities), and establish wiring connections between operators
across app boundaries.

## State Structure

```typescript
interface FederatedAppsState {
  apps: Record<string, FederatedApp>      // Registered applications
  operators: Record<string, OperatorNode>  // Operator nodes within apps
  wires: Record<string, OperatorWire>     // Connections between operators
  version: number                          // State version for optimistic updates
}
```

## Key Concepts

### FederatedApp

Represents a registered application in the federation:
- **id**: Unique identifier
- **name**: Human-readable name
- **version**: App version
- **protocol**: Communication protocol (ipc, ws, http, grpc, internal)
- **capabilities**: What the app can do (host operators, proxy, etc.)
- **state**: Connection state (available, busy, error, etc.)

### OperatorNode

Represents a capability/provider within an app:
- **id**: Unique identifier
- **appId**: Parent app reference
- **type**: Operator type (llm, tool, gateway, etc.)
- **capabilities**: Feature flags (streaming, batching, etc.)
- **state**: Current operational state
- **load metrics**: currentLoad, queueDepth

### OperatorWire

Represents a connection between two operators:
- **source/target**: References to connected operators
- **protocol**: Wire protocol
- **direction**: unidirectional or bidirectional
- **state**: Connection health
- **metrics**: latencyMs, throughputBps

## API

### App Management

```typescript
registerApp(app: Omit<FederatedApp, 'registeredAt'>): FederatedApp
unregisterApp(appId: string): boolean
updateAppState(appId: string, state: ConnectionState): boolean
```

### Operator Management

```typescript
registerOperator(operator: Omit<OperatorNode, 'lastActivityAt'>): OperatorNode
unregisterOperator(operatorId: string): boolean
updateOperatorState(operatorId: string, updates): boolean
```

### Wire Management

```typescript
createWire(id, source, target, protocol, direction): OperatorWire
removeWire(wireId: string): boolean
updateWireState(wireId: string, updates): boolean
```

### Queries

```typescript
getAppOperators(appId: string): OperatorNode[]
getOperatorWires(operatorId: string): OperatorWire[]
getTopologyGraph(): { nodes, edges }
getAvailableOperators(): OperatorNode[]
hasPath(sourceId: string, targetId: string): boolean
getRoutingPath(sourceId: string, targetId: string): string[] | null
```

## State Persistence

```typescript
exportState(): FederatedAppsState
importState(state: FederatedAppsState): void
```

## Testing

Run tests with:
```bash
npm run test:ui -- src/store/federated-apps.test.ts
```

## Integration

The store is integrated into the desktop app via nanostores, following the same
pattern as `subagents.ts`. Components can subscribe to `$federatedApps` atom
for reactive updates.

## Design Notes

1. **Normalized State**: All entities are stored in flat maps (by ID) for O(1)
   lookups and to prevent duplication.

2. **Immutable Updates**: All mutations create new state objects to work well
   with React and nanostores.

3. **Version Tracking**: State version increments on every mutation for
   optimistic concurrency control.

4. **Automatic Cleanup**: Unregistering apps/operators automatically removes
   their associated wires to maintain referential integrity.

5. **Path Finding**: Built-in BFS-based routing for finding paths between
   operators in the topology graph.
