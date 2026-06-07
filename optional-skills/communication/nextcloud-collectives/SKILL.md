---
name: nextcloud-collectives
description: Nextcloud Collectives (Collective) — Wiki-Seiten und Wissensbasen verwalten. Seiten erstellen, lesen, schreiben, organisieren, taggen und durchsuchen in gemeinsamen Collectives/Kollektiven. Fuer Dokumentation, Wissensmanagement und kollaboratives Schreiben. Use when the user mentions Collective, Collectives, Kollektiv, Wiki, or knowledge pages.
version: 1.0.0
author: niko
license: MIT
metadata:
  hermes:
    tags: [Wiki, Knowledge, Nextcloud, Documentation, Collectives, Collective, Kollektiv, Seiten, Pages]
    homepage: https://github.com/nextcloud/collectives
prerequisites:
  commands: [curl, python3]
---

# Nextcloud Collectives — Wiki & Knowledge Management

Manage shared wiki collectives, pages (markdown), tags, attachments, shares, and templates via the Nextcloud Collectives REST API + WebDAV.

## How to call the helper script

Use the `terminal` tool (NOT `execute_code`) to run commands:

```bash
CL=~/.hermes/skills/nextcloud-collectives/collectives
$CL collectives
```

**IMPORTANT:** ALWAYS use the `terminal` tool. NEVER use `execute_code` — it sandboxes API keys.

## Getting Started

Use `$CL collectives` to list available collectives and their IDs.

## Commands Reference

### Collectives

```bash
# List all collectives
$CL collectives

# Create a new collective
$CL create-collective "Infrastructure Docs"
$CL create-collective "Meeting Notes" "📝"

# Update collective emoji
$CL update-collective 5 "🏗️"

# Trash / restore / delete
$CL trash-collective 5
$CL trashed-collectives
$CL restore-collective 5
$CL delete-collective 5           # permanent, from trash only
$CL delete-collective 5 true      # also delete underlying Team

# Settings
$CL set-edit-level 5 1      # who can edit (member level)
$CL set-share-level 5 1     # who can share
$CL set-page-mode 5 1       # 0=rich text, 1=markdown
```

### Pages

Pages are organized in a tree. The landing page (parentId=0) is the root — create top-level pages under its ID.

```bash
# List all pages in a collective
$CL pages 5

# Get single page metadata
$CL page 5 42

# Create page at root level (use landing page ID as parent)
# First get the landing page ID from: $CL pages 5 (the one with parentId=0)
$CL create-page 5 <LANDING_PAGE_ID> "Server Setup Guide"

# Create subpage under page 42
$CL create-page 5 42 "Network Configuration"

# Move page to new parent
$CL move-page 5 42 0        # move to root
$CL move-page 5 42 10 2     # move under page 10, position 2

# Copy page
$CL copy-page 5 42 0        # copy to root

# Trash / restore / delete
$CL trash-page 5 42
$CL trashed-pages 5
$CL restore-page 5 42
$CL delete-page 5 42        # permanent, from trash only

# Page metadata
$CL set-page-emoji 5 42 "🖥️"
$CL set-page-width 5 42 true    # full width
$CL touch-page 5 42             # mark as edited by hermes
```

### Page Content (Markdown via WebDAV)

Page content is markdown, accessed via WebDAV (not REST).

```bash
# Read page content (outputs raw markdown)
$CL read-page 5 42

# Write content from a file
echo "# Server Setup\n\nThis page documents..." > /tmp/page.md
$CL write-page 5 42 /tmp/page.md

# Write content from stdin
echo "# Updated Content

New markdown here." | $CL write-page-stdin 5 42
```

**Workflow for editing a page:**
1. Read current content: `$CL read-page 5 42 > /tmp/page.md`
2. Modify `/tmp/page.md`
3. Write back: `$CL write-page 5 42 /tmp/page.md`

### Tags

Tags are per-collective labels with colors.

```bash
# List tags
$CL tags 5

# Create tag (color as #hex)
$CL create-tag 5 "Important" "#ff0000"
$CL create-tag 5 "Draft" "#ffaa00"

# Update tag
$CL update-tag 5 3 "Critical" "#cc0000"

# Delete tag
$CL delete-tag 5 3

# Apply/remove tag on a page
$CL tag-page 5 42 3
$CL untag-page 5 42 3
```

### Attachments

```bash
# List attachments on a page
$CL attachments 5 42

# Upload file as attachment
$CL upload-attachment 5 42 /tmp/diagram.png

# Delete attachment
$CL delete-attachment 5 42 7
```

### Shares

Create public share links for collectives or individual pages.

```bash
# List all shares
$CL shares 5

# Create collective share (read-only)
$CL create-share 5

# Create editable collective share
$CL create-share 5 true

# Create page share
$CL create-page-share 5 42
$CL create-page-share 5 42 true   # editable

# Delete shares
$CL delete-share 5 <token>
$CL delete-page-share 5 42 <token>
```

### Templates

```bash
# List templates
$CL templates 5

# Create template page
$CL create-template 5 0 "Meeting Notes Template"

# Delete template
$CL delete-template 5 8
```

### Search

```bash
# Search pages in a collective
$CL search 5 "docker"
$CL search 5 "network configuration"
```

## API Response Format

All responses are JSON in OCS envelope:
```json
{
  "ocs": {
    "meta": {"status": "ok", "statuscode": 200},
    "data": { ... }
  }
}
```

Extract data with: `| python3 -c "import sys,json; print(json.dumps(json.load(sys.stdin)['ocs']['data'], indent=2))"`

## Page Object Fields

Key fields in page responses:
- `id` — page ID (also NC file ID)
- `title` — page title
- `parentId` — parent page ID (0 = root)
- `fileName` — e.g. "MyPage.md"
- `filePath` — path within collective folder
- `collectivePath` — collective root path
- `emoji` — page emoji
- `tags` — array of tag IDs
- `timestamp` — last modification (unix)
- `lastUserId` — last editor

## Links zu Collectives-Seiten

Fuer eingebettete Vorschau (Embedded Preview) in Deck, Talk und anderen NC-Apps:

```
$NEXTCLOUD_URL/apps/collectives/<CollectiveName>-<CollectiveID>/<PageSlug>-<PageID>
```

In Markdown mit Preview:
```
[Seitentitel]($NEXTCLOUD_URL/apps/collectives/<CollectiveName>-<CollectiveID>/<PageSlug>-<PageID> (preview))
```

Beispiel:
```
[Page Title]($NEXTCLOUD_URL/apps/collectives/<CollectiveName>-<CID>/<PageSlug>-<PageID> (preview))
```

Die Werte kommen aus der API-Response: `id` (Page-ID), `slug` (Page-Slug), Collective-Name und Collective-ID aus `collectives`.

## Important Notes

1. **Content is separate from metadata** — the REST API manages page structure, WebDAV manages markdown content. Use `read-page`/`write-page` for content.
2. **Landing page = root** — to create top-level pages, use the landing page's ID as parent (the page with `parentId: 0` in the pages list). Do NOT use `0` as parent_id — it returns 404.
3. **Trash is two-step** — `trash-page` moves to trash, `delete-page` permanently deletes from trash.
4. **Touch after writing** — `write-page` automatically calls `touch-page` after WebDAV PUT.
5. **Collectives folder** — pages are stored under `/.Collectives/` in NC Files. The Files Service may see these — they are managed by Collectives, do not sync them separately.
