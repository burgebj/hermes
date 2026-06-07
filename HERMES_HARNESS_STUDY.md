# Hermes Agent Harness Study Notes

This note is a learning map for understanding Hermes Agent as an agent runtime,
not just as a chat wrapper around an LLM.

## 1. Core Mental Model

Hermes Agent is best understood as a harness around language models.

The model is the reasoning engine, but the harness provides the system behavior:

- Entry points: CLI, TUI, messaging gateway, batch runner, ACP/editor adapters.
- Runtime state: session ID, conversation history, memory, context compression.
- Model transport: OpenAI-compatible chat completions, Codex Responses,
  Anthropic Messages, Bedrock Converse, and provider-specific routing.
- Tool surface: schemas exposed to the model, toolset filtering, availability
  checks, and registry-based dispatch.
- Safety and recovery: interrupt, steer, checkpoints, guardrails, fallback
  providers, retries, malformed tool-call recovery.
- Observability: callbacks, logs, session DB, usage tracking, trajectories.

In short:

> Hermes is not a single model call. It is a stateful agent runtime that controls
> how model calls, tools, memory, context, platforms, and recovery mechanisms work
> together.

## 2. One Complete Runtime Call Chain

The most important path to understand is one user prompt going through the
system.

```text
User input
  -> CLI / TUI / Gateway entry point
  -> AIAgent(...)
  -> agent.agent_init.init_agent(...)
  -> AIAgent.run_conversation(...)
  -> agent.conversation_loop.run_conversation(...)
  -> model call through agent._interruptible_api_call(...)
  -> either final text or tool_calls
  -> if tool_calls:
       agent._execute_tool_calls(...)
       -> agent.tool_executor
       -> model_tools.handle_function_call(...)
       -> tools.registry.dispatch(...)
       -> concrete tools/*.py handler
       -> append role="tool" result to messages
       -> loop back to model call
  -> final_response
  -> session/log/callback/memory/compression bookkeeping
```

## 3. Key Source Files

### `run_agent.py`

Defines `AIAgent`, the public-facing agent class.

Important idea: `AIAgent` is now mostly a compatibility facade. The real work is
delegated into modules under `agent/`.

Key methods:

- `AIAgent.__init__`: forwards to `agent.agent_init.init_agent`.
- `AIAgent.run_conversation`: forwards to `agent.conversation_loop.run_conversation`.
- `AIAgent.chat`: simple wrapper that returns only `final_response`.

### `agent/agent_init.py`

Builds an agent instance into a runnable runtime.

It wires together:

- model/provider/base URL/API mode
- callbacks for CLI, TUI, and gateway display
- interrupt and steer state
- provider client construction
- fallback model chain
- tool definitions and valid tool names
- session ID and session DB state
- checkpoint manager
- memory store and memory provider plugins
- context compressor/context engine
- primary runtime snapshot for fallback recovery

### `agent/conversation_loop.py`

Runs one user turn.

This is the core model-tool loop:

```text
while iteration budget remains:
    call model
    if tool_calls:
        validate tool calls
        execute tools
        append tool results
        continue
    else:
        return final text
```

The real implementation also handles retries, provider failures, context
compression, empty responses, malformed tool calls, interrupted turns, fallback
providers, and post-turn hooks.

### `model_tools.py`

Bridges model tool calls to the tool registry.

Important functions:

- `get_tool_definitions(...)`: decides which tool schemas the model sees.
- `handle_function_call(...)`: dispatches a model-requested tool call.

### `tools/registry.py`

Central registry for tool schemas and handlers.

Each tool registers:

- name
- toolset
- schema
- handler
- availability check
- metadata

The registry makes tool execution structured and auditable instead of scattered
across random conditionals.

### `toolsets.py`

Defines capability groups.

Toolsets are the permission/capability boundary for the model. The model only
sees tools that are included by enabled toolsets and not removed by disabled
toolsets.

### `agent/tool_executor.py`

Executes tool calls safely.

It handles:

- sequential or concurrent tool execution
- preserving tool result order
- `tool_call_id` matching
- interrupt propagation
- guardrails
- checkpointing before risky operations
- callbacks and progress events
- large tool result persistence
- appending tool results back to the message list

## 4. Harness Engineering Principles in Hermes

### 4.1 The Model Is Not the Runtime

Hermes separates the model from the runtime around it.

The model proposes text or tool calls. The runtime decides:

- which tools are visible
- whether a tool call is valid
- whether execution is allowed
- how results are represented
- whether to retry, compress, fallback, or stop

### 4.2 Tool Calls Are Production Tasks

In a demo agent, a tool call may be just:

```python
result = tool(**args)
```

In Hermes, tool calls pass through:

```text
schema exposure
  -> model tool call
  -> tool name validation
  -> JSON argument validation
  -> guardrail / plugin hook
  -> checkpoint if needed
  -> dispatch
  -> result classification
  -> result size management
  -> callback/logging
  -> message append
```

This is one of the clearest examples of harness engineering in the project.

### 4.3 Capabilities Are Explicitly Gated

The model does not automatically get every tool.

Tool availability is controlled by:

- registered tools
- toolsets
- enabled/disabled toolset config
- check functions
- plugin registration
- dynamic schema adjustments

This is why `agent.tools` and `agent.valid_tool_names` are created during
initialization.

### 4.4 State Is First-Class

Hermes tracks much more than messages:

- `session_id`
- session DB rows
- cached system prompt
- memory store
- context compressor state
- token usage
- rate limit state
- active tool
- iteration budget
- fallback runtime

This lets the agent survive long conversations and multi-platform usage.

### 4.5 Recovery Paths Are Designed In

Hermes expects real model/provider behavior to be messy.

It includes recovery logic for:

- unknown tool names
- invalid JSON tool arguments
- truncated tool calls
- empty responses
- context length pressure
- rate limits
- provider overload
- interrupted turns
- failed tools

This is a major difference between a toy agent and a production agent runtime.

## 5. Recommended Reading Path

Read the code in this order:

1. `run_agent.py`
   - Understand `AIAgent` as the public facade.
2. `agent/agent_init.py`
   - Understand how an agent instance is assembled.
3. `agent/conversation_loop.py`
   - Follow one user turn through the model-tool loop.
4. `model_tools.py`
   - Understand how tool schemas are selected and tool calls are dispatched.
5. `tools/registry.py`
   - Understand how tools self-register and execute.
6. `toolsets.py`
   - Understand capability grouping and exposure.
7. `agent/tool_executor.py`
   - Understand safe tool execution and result handling.
8. `cli.py`, `tui_gateway/server.py`, `gateway/run.py`
   - Understand how multiple entry points share the same runtime.

## 6. One-Sentence Summary

Hermes Agent is a stateful, multi-entrypoint agent runtime where the LLM is
wrapped by a harness for model routing, tool governance, session memory, context
management, safety, recovery, observability, and extensibility.
