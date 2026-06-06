# zoom platform plugin

Webhook-first Zoom Team Chat adapter for the Hermes gateway.

## What it does

- receives Zoom webhook events over `aiohttp`
- validates Zoom webhook signatures and URL-validation challenges
- normalizes Team Chat messages into Hermes `MessageEvent`s
- sends bot replies back through Zoom using server-to-server OAuth

## Required environment

- `ZOOM_ACCOUNT_ID`
- `ZOOM_CLIENT_ID`
- `ZOOM_CLIENT_SECRET`
- `ZOOM_CHAT_BOT_JID`
- `ZOOM_WEBHOOK_SECRET_TOKEN`

Optional:

- `ZOOM_ALLOWED_USERS`
- `ZOOM_ALLOW_ALL_USERS`

## Gateway config

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

## API drift note

Zoom Team Chat app payloads and send endpoints can vary by app type. This adapter
keeps two escape hatches configurable through `extra`:

- `base_url`
- `send_path`

Defaults:

- `base_url`: `https://api.zoom.us`
- `send_path`: `/v2/im/chat/messages`

If your Zoom app expects a different chat-send endpoint or payload rollout, adjust
those values first before changing adapter code.
