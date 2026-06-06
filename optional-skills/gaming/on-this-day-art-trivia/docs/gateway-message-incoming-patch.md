# Optional gateway patch — `message:incoming` hook event

**You probably do not need this patch.** The shipped `plugin/on_this_day_art_trivia/`
already intercepts inbound messages via the existing `pre_gateway_dispatch`
hook (declared in `hermes-agent/hermes_cli/plugins.py`'s `VALID_HOOKS` set,
fired in `hermes-agent/gateway/run.py:_handle_message`). That gives us a
return-value-driven `{"action": "skip", ...}` interception with zero core
changes.

This document is provided only for deployments that want a *pure HOOK.yaml*
intercept path (i.e., a hook directory with a `HOOK.yaml` and a `handler.py`,
no plugin) for inbound messages. In that case, add a `message:incoming` event
to the `HookRegistry` so the same `decision: handled` contract used for slash
commands also applies to inbound text.

## Patch

```diff
--- a/hermes-agent/gateway/run.py
+++ b/hermes-agent/gateway/run.py
@@ -3597,6 +3597,40 @@ class GatewayRunner:
                 if _action == "allow":
                     break

+        # message:incoming HookRegistry event.
+        # Mirrors the existing pre_gateway_dispatch plugin hook, but uses the
+        # gateway HookRegistry so HOOK.yaml-based hooks can intercept inbound
+        # text too. Honoured decisions:
+        #   {"decision": "handled", "message": "..."}  -> reply with message,
+        #                                                  do not dispatch agent
+        #   {"decision": "skip"}                        -> drop silently
+        # Hooks returning anything else (or None) fall through to normal flow.
+        if not is_internal:
+            try:
+                _msg_results = await self.hooks.emit_collect(
+                    "message:incoming",
+                    {
+                        "platform": source.platform.value if source.platform else "",
+                        "user_id": source.user_id,
+                        "user_name": source.user_name,
+                        "chat_id": source.chat_id,
+                        "chat_type": source.chat_type,
+                        "text": event.text,
+                        "reply_to_message_id": getattr(event, "reply_to_message_id", None),
+                    },
+                )
+            except Exception as _hook_err:
+                logger.debug("message:incoming hook dispatch failed: %s", _hook_err)
+                _msg_results = []
+            for _result in _msg_results:
+                if not isinstance(_result, dict):
+                    continue
+                _decision = str(_result.get("decision", "")).strip().lower()
+                if _decision == "handled":
+                    return _result.get("message")
+                if _decision == "skip":
+                    return None
+
         if is_internal:
             pass
         elif source.user_id is None:
```

## Applying the patch

```bash
cd ~/.hermes/hermes-agent
patch -p1 < ~/.hermes/on-this-day-art-trivia/docs/gateway-message-incoming.patch
```

Then restart the gateway. After this, a `HOOK.yaml` like

```yaml
name: on-this-day-art-trivia-inbound
description: Score guesses against the active challenge
events:
  - message:incoming
```

with a `handler.py` returning `{"decision": "handled", "message": ...}` would
work without the plugin.

## Why this is optional

The plugin path uses an existing, shipped extension point (`pre_gateway_dispatch`).
Adding this patch to the gateway is fine — it is small and isolated — but it
is duplicate plumbing. We recommend leaving it unpatched and using the plugin.
