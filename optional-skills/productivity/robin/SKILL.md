---
name: robin
description: Save and review notes, links, media references, and other knowledge in a local commonplace book.
version: 0.3.3
author: Nitin Gupta
license: MIT
platforms: [macos, linux]
metadata:
  hermes:
    tags: [productivity, knowledge-management, notes, commonplace, spaced-repetition]
    requires_toolsets: [terminal]
    category: productivity
---

# Robin

Robin is a local commonplace-book skill for saving, organizing, searching, and reviewing knowledge over time. Use it when the user wants to remember a note, quote, article, link, image, video reference, or other durable item.

Robin stores data in a user-controlled state directory. It does not require external services, API keys, or package installation.

## When to Use

Use Robin when the user wants to:

- save something for later recall
- organize knowledge by topic and tags
- search or review prior saved entries
- move or delete existing entries
- check the health of the local Robin library

Do not use Robin for short-lived reminders, calendar events, secrets, credentials, or files the user does not want persisted.

## Setup

Choose a Robin state directory, usually:

```bash
~/.hermes/data/robin
```

Initialize the directory before first use:

```bash
mkdir -p ~/.hermes/data/robin/topics ~/.hermes/data/robin/media
printf '{}\n' > ~/.hermes/data/robin/robin-config.json
python3 scripts/doctor.py --state-dir ~/.hermes/data/robin --json
```

Robin accepts either `--state-dir` or `ROBIN_STATE_DIR`. Prefer passing `--state-dir` explicitly in agent-run commands.

## Common Commands

Save a text entry:

```bash
python3 scripts/add_entry.py --state-dir ~/.hermes/data/robin --topic "AI" --content "Useful note" --description "Short label" --tags ai,notes
```

Save a source-backed entry:

```bash
python3 scripts/add_entry.py --state-dir ~/.hermes/data/robin --topic "Reading" --content "Key takeaway" --description "Article title" --source "https://example.com"
```

Search:

```bash
python3 scripts/search.py --state-dir ~/.hermes/data/robin --query "takeaway"
python3 scripts/search.py --state-dir ~/.hermes/data/robin --topic "Reading" --json
python3 scripts/search.py --state-dir ~/.hermes/data/robin --tags ai,notes
```

Review due items:

```bash
python3 scripts/review.py --state-dir ~/.hermes/data/robin --limit 5
```

Move or delete entries:

```bash
python3 scripts/entries.py --state-dir ~/.hermes/data/robin --id <entry-id> --move-to "New Topic"
python3 scripts/entries.py --state-dir ~/.hermes/data/robin --id <entry-id> --delete
```

Check health:

```bash
python3 scripts/doctor.py --state-dir ~/.hermes/data/robin
python3 scripts/selftest.py
```

## Operating Rules

- Always include a topic and concise description when saving.
- Use tags only when they will help future search or review.
- Respect duplicate warnings. Use `--allow-duplicate` only when the user explicitly wants another copy.
- For images, pass a local image path and let Robin copy it into the state directory.
- For videos, save the URL/reference only; Robin does not copy video files.
- When deleting, confirm the entry ID and user intent first.

## Verification

After setup or changes, run:

```bash
python3 scripts/doctor.py --state-dir ~/.hermes/data/robin --json
```

For a non-destructive integration check, run:

```bash
python3 scripts/selftest.py
```

See `references/guide.md` for the full CLI reference, JSON contracts, and advanced workflows.
