---
sidebar_position: 10
title: "IRC"
---

# IRC Setup

## Quick Start

```bash
pip install irc3
export IRC_SERVER=irc.libera.chat
export IRC_NICK=hermes-bot
export IRC_TLS=true
export IRC_ALLOWED_USERS=your-nick
hermes gateway
```

## Configuration

```
IRC_SERVER=irc.libera.chat
IRC_NICK=hermes-bot
IRC_PORT=6697
IRC_TLS=true
IRC_CHANNELS=#channel
IRC_SASL_USERNAME=hermes-bot
IRC_SASL_PASSWORD=secret
IRC_ALLOWED_USERS=alice,bob
```

## Features

- TLS support (port 6697)
- SASL authentication
- Flood protection
- CTCP support (PING, VERSION, TIME)
- Auto-reconnect
