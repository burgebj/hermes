---
sidebar_position: 15
title: "Nextcloud Talk"
description: "Set up Hermes Agent as a Nextcloud Talk bot"
---

# Nextcloud Talk Setup

Hermes Agent integrates with [Nextcloud Talk](https://nextcloud.com/talk/) using the User API with long-polling. Once connected, your agent appears as a regular participant in Talk conversations. The integration supports text messages, voice memos (with STT transcription), images (with vision analysis), document attachments, and outgoing file uploads.

## Prerequisites

- A Nextcloud instance (version 25+) with the Talk app enabled
- A dedicated Nextcloud user account for the agent (recommended)
- Network access from the Hermes gateway to the Nextcloud instance

## Step 1: Create a Nextcloud User for Hermes

Create a dedicated user account that the agent will use to participate in conversations. You can create the user via the Nextcloud admin panel or via the `occ` CLI:

```bash
sudo -u www-data php occ user:add hermes --display-name="Hermes Agent"
```

Alternatively, if your Nextcloud uses an external identity provider (LDAP, OIDC), create the user there.

:::tip
Using a dedicated account keeps the agent's messages clearly separated from human users and allows fine-grained permission control.
:::

## Step 2: Generate an App Password

The agent authenticates via an [app password](https://docs.nextcloud.com/server/latest/user_manual/en/session_management.html#managing-devices), not the user's login password. This is more secure and avoids issues with two-factor authentication.

**Option A — Via Nextcloud UI:**
1. Log in as the `hermes` user
2. Go to **Settings → Security → Devices & sessions**
3. Enter a name (e.g., "Hermes Gateway") and click **Create new app password**
4. Copy the generated password

**Option B — Via `occ` CLI:**
```bash
sudo -u www-data php occ user:add-app-password hermes
```

:::warning
The app password is shown only once. Copy it immediately and store it securely.
:::

## Step 3: Add Hermes to Conversations

Add the `hermes` user to each Talk conversation where the agent should be active. You can do this via the Talk UI (conversation settings → participants → add user) or via the OCS API.

Note the **conversation token** for each conversation — this is the short alphanumeric string in the URL when viewing the conversation (e.g., `abc123xy` from `https://nextcloud.example.com/call/abc123xy`).

## Step 4: Configure Hermes

Add the Nextcloud Talk platform to your `~/.hermes/config.yaml`:

```yaml
platforms:
  nextcloud_talk:
    enabled: true
    extra:
      nextcloud_url: https://nextcloud.example.com
      username: hermes
      app_password_env: NEXTCLOUD_TALK_APP_PASSWORD
      conversations:
        - token: abc123xy
          alias: general
        - token: def456zw
          alias: engineering
      edit_ack_into_response: true
      poll_timeout: 30
```

Set the app password as an environment variable in `~/.hermes/.env`:

```
NEXTCLOUD_TALK_APP_PASSWORD=your-app-password-here
```

### Configuration Reference

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `nextcloud_url` | string | required | Base URL of your Nextcloud instance |
| `username` | string | `hermes` | Nextcloud username for the agent |
| `app_password_env` | string | `NEXTCLOUD_TALK_APP_PASSWORD` | Environment variable containing the app password |
| `conversations` | list | required | Conversations to join (token + optional alias) |
| `edit_ack_into_response` | bool | `true` | Show "thinking..." placeholder, then edit to final response |
| `poll_timeout` | int | `30` | Long-poll timeout in seconds |
| `channel_aliases` | dict | `{}` | Additional aliases for conversation tokens |

### STT Configuration (Optional)

To enable speech-to-text for voice messages:

```yaml
      stt:
        provider: llamacpp
        base_url: http://your-whisper-server:8080
```

## Step 5: Start the Gateway

```bash
hermes gateway run
```

The agent will join the configured conversations and start listening for messages via long-polling.

## How It Works

- **Receiving messages:** The adapter polls each configured conversation for new messages. When a message arrives, it is parsed and forwarded to the agent.
- **Sending responses:** If `edit_ack_into_response` is enabled (default), the agent first sends a "thinking..." placeholder, then edits it with the final response. This provides immediate feedback while the agent processes the request.
- **Media handling:** Images are analyzed via the vision tool. Voice messages are transcribed via STT. Documents are downloaded and their content extracted. Outgoing files are uploaded via WebDAV and shared into the conversation.
- **Voice messages:** The agent can send voice messages with an inline audio player in Talk, using the `talkMetaData` mechanism.

## Troubleshooting

### Agent doesn't respond

- Check that `NEXTCLOUD_TALK_APP_PASSWORD` is set in `~/.hermes/.env`
- Verify the conversation token is correct (check the URL in Talk)
- Ensure the `hermes` user is a participant in the conversation
- Check the gateway logs: `hermes gateway logs` or `journalctl -u hermes-gateway`

### HTTP 401 errors

- The app password may be invalid. Generate a new one via Step 2.
- If using Nextcloud behind a reverse proxy, ensure the `Authorization` header is forwarded.

### Brute-force throttling (HTTP 429)

Nextcloud may throttle the agent's IP after failed authentication attempts. Reset via:

```bash
sudo -u www-data php occ security:bruteforce:reset <agent-ip>
```
