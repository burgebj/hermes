---
sidebar_position: 34
sidebar_label: "Zoom Team Chat"
title: "Zoom Team Chat"
description: "Run Hermes inside Zoom Team Chat via the bundled Zoom gateway platform adapter"
---

# Zoom Team Chat

Hermes ships a bundled **Zoom Team Chat** gateway adapter at `plugins/platforms/zoom/`. It is a webhook-first integration:

- inbound Zoom Team Chat events arrive through an `aiohttp` webhook server
- Zoom webhook URL-validation and request signatures are verified
- Hermes normalizes incoming messages into gateway `MessageEvent`s
- outbound replies use Zoom server-to-server OAuth plus a bot JID

This is the Zoom analogue of the existing Teams and IRC platform adapters.

## What you need

Environment variables:

- `ZOOM_ACCOUNT_ID`
- `ZOOM_CLIENT_ID`
- `ZOOM_CLIENT_SECRET`
- `ZOOM_CHAT_BOT_JID`
- `ZOOM_WEBHOOK_SECRET_TOKEN`

Optional auth controls:

- `ZOOM_ALLOWED_USERS`
- `ZOOM_ALLOW_ALL_USERS`

Python dependencies:

```bash
pip install aiohttp requests
```

## Gateway config

Add the Zoom platform in `~/.hermes/config.yaml`:

```yaml
gateway:
  platforms:
    zoom:
      enabled: true
      extra:
        host: 0.0.0.0
        port: 8762
        path: /zoom/chat/webhook
        webhook_secret: ${ZOOM_WEBHOOK_SECRET_TOKEN}
        account_id: ${ZOOM_ACCOUNT_ID}
        client_id: ${ZOOM_CLIENT_ID}
        client_secret: ${ZOOM_CLIENT_SECRET}
        bot_jid: ${ZOOM_CHAT_BOT_JID}
```

Then start the gateway:

```bash
hermes gateway run
```

## What the adapter does today

- verifies `endpoint.url_validation`
- verifies `x-zm-signature` / `x-zm-request-timestamp`
- ignores duplicate message IDs
- ignores self-messages from the configured bot JID
- turns Team Chat messages into Hermes gateway events
- sends text replies back through Zoom's chat API

## Current limitations

- exact Zoom Team Chat payload shapes can vary by app type
- exact send endpoint shape can vary across Zoom app surfaces
- rich interactive cards / typing indicators are not implemented yet
- thread/reply semantics are basic and should be verified in a live tenant

For that reason the adapter exposes these escape hatches via `extra`:

- `base_url`
- `send_path`

Defaults:

- `base_url`: `https://api.zoom.us`
- `send_path`: `/v2/im/chat/messages`

## Live verification checklist

Before treating the adapter as production-ready in your tenant, verify these in a real Zoom app:

1. Webhook challenge
   Set the Zoom webhook target to `http(s)://<host>:8762/zoom/chat/webhook` and confirm Zoom accepts the `plainToken` / `encryptedToken` response.

2. Signature enforcement
   Send one real webhook event and confirm Hermes only accepts requests with the correct `x-zm-signature`.

3. Inbound message shape
   Send a Team Chat DM and a channel message, then confirm Hermes sees:
   - correct `chat_id`
   - correct sender identity
   - stable `message_id`
   - text body in the expected field

4. Self-echo suppression
   Send a reply from Hermes and confirm that Zoom's own webhook echo does not trigger a second Hermes turn.

5. Outbound send endpoint
   Confirm the default `POST /v2/im/chat/messages` shape is valid for your app type. If not, override `base_url` / `send_path` first.

6. Reply semantics
   Verify whether `reply_main_message_id` actually threads replies in your Zoom chat surface the way you expect.

7. Authorization
   If you do not want every Zoom user chatting with the bot, set `ZOOM_ALLOWED_USERS` and verify a denied user is blocked.

## Operator checklist

- Keep the webhook secret and OAuth credentials in `.env`, not inline in shared config.
- Expose the webhook over HTTPS in real deployments.
- If send requests fail but inbound webhooks work, test the Zoom app's bot scopes and the exact bot JID first.
- If inbound webhooks never arrive, test URL-validation and signature headers before debugging Hermes.

## Related pieces

- `plugins/platforms/zoom/adapter.py` — gateway adapter
- `plugins/platforms/zoom/README.md` — repo-local quick reference
- `plugins/zoom_meeting/` — separate meeting-intelligence plugin for Zoom meetings
