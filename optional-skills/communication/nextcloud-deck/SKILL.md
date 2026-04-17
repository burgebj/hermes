---
name: nextcloud-deck
description: Manage tasks via Nextcloud Deck boards. Create, update, move, delete cards. Assign users, labels, due dates, comments, attachments. Use when the user asks for todos, tasks, or Kanban management.
version: 4.0.0
author: niko
license: MIT
metadata:
  hermes:
    tags: [Tasks, Kanban, Nextcloud, Project Management]
prerequisites:
  commands: [curl]
---

# Nextcloud Deck — Task & Todo Management

**WICHTIG:** Es gibt KEIN built-in Tool namens "nextcloud-deck". Nutze das `terminal` Tool fuer die Befehle unten. NICHT execute_code — das hat keinen Zugriff auf API-Keys.

## Helper-Script verwenden

Nutze das `terminal` Tool fuer die Befehle unten. NICHT execute_code — das hat keinen Zugriff auf API-Keys.

```bash
DK=~/.hermes/skills/nextcloud-deck/deck

# === Boards & Stacks ===
$DK boards | jq '.[] | {id, title}'
$DK board 6 | jq '{id, title, labels: [.labels[] | {id, title, color}]}'
$DK stacks 6 | jq '.[] | {id, title, cards: [.cards[]? | {id, title}]}'
$DK create-stack 6 "Neuer Stack"
$DK delete-stack 6 18

# === Cards (Aufgaben) ===
$DK cards 6 | jq '.[] | {stack: .title, cards: [.cards[]? | {id, title, duedate, done}]}'
$DK card 6 26 46 | jq '{id, title, description, duedate, done, labels, assignedUsers}'
$DK create-card 6 26 "Neue Aufgabe" "Beschreibung hier"
echo "Lange Beschreibung mit [Link](https://example.com (preview))" | $DK create-card-stdin 6 26 "Titel"
$DK update-card 6 26 46 "Neuer Titel" "Neue Beschreibung"
echo "Markdown mit Links und (Klammern)" | $DK update-card-stdin 6 26 46 "Titel"
$DK move-card 6 46 27
$DK delete-card 6 26 46
$DK set-duedate 6 26 46 "2026-04-20T12:00:00+02:00"
$DK done 6 26 46
$DK undone 6 26 46

# === Labels ===
$DK labels 6
$DK create-label 6 "Dringend" "FF0000"
$DK assign-label 6 26 46 25
$DK remove-label 6 26 46 25

# === User zuweisen ===
$DK assign-user 6 26 46 "niko"
$DK unassign-user 6 26 46 "niko"

# === Kommentare ===
$DK comments 46
$DK add-comment 46 "Das ist ein Kommentar"
echo "Kommentar mit (Klammern) und Links" | $DK add-comment-stdin 46
$DK delete-comment 46 123

```

## Dateien und Links in Cards referenzieren

Nutze die Beschreibung (Markdown) um NC-Dateien, Weblinks oder Kollektiv-Seiten zu referenzieren.

**WICHTIG:** Fuer Beschreibungen mit Links, Klammern oder Sonderzeichen IMMER die stdin-Variante verwenden:

```bash
echo "## Links
- [Anleitung PDF]($NEXTCLOUD_URL/f/42)
- [Wiki-Seite]($NEXTCLOUD_URL/apps/collectives/Projekte-3/Adept-Slim-Frame-Trackball-Mod-201179 (preview))
- [Externes Dokument](https://example.com/doc)" | $DK update-card-stdin 6 26 46 "Smartmeter"
```

Die NC Deck App rendert Markdown in der Beschreibung. Links zu anderen NC-Apps:
- **Dateien:** `$NEXTCLOUD_URL/f/{FILE_ID}`
- **Collectives-Seiten mit Embedded Preview:** `$NEXTCLOUD_URL/apps/collectives/<Name>-<ID>/<Slug>-<PageID> (preview)`
  Beispiel: `[Titel]($NEXTCLOUD_URL/apps/collectives/Projekte-3/Adept-Slim-Frame-Trackball-Mod-201179 (preview))`
  Die Werte (Slug, Page-ID) kommen aus: `collectives pages <CID> | jq ".ocs.data.pages[]"`

## Workflow

1. Boards mit `$DK boards` auflisten, passenden waehlen
2. Stacks mit `$DK stacks <board_id>` anzeigen
3. Cards mit Titel und optionaler Beschreibung erstellen
4. Optional: Due Date, Label, User-Zuweisung
