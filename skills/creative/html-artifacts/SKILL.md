---
name: html-artifacts
description: "Use when a durable deliverable works better as single-file HTML than markdown: comparisons, plans, reviews, explainers, timelines, diagrams, decks, reports, or one-off editors with copy/export back to text."
version: 1.0.0
author: dogum/html-artifacts, adapted by Hermes Agent
license: Apache-2.0
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [html, artifacts, documents, reports, planning, comparison, diagrams, editors, visualization]
    related_skills: [claude-design, popular-web-designs, architecture-diagram, design-md, excalidraw, sketch]
    upstream_skill: https://github.com/dogum/html-artifacts
---

# HTML Artifacts

## Overview

Use this skill when the user needs a deliverable that benefits from layout,
navigation, visual hierarchy, color, diagrams, or interaction. Markdown is still
right for short chat answers and code snippets, but durable artifacts are often
clearer as a self-contained HTML file that can be opened, reviewed, shared, and
reused without a build step.

The output is not "HTML for everything." The goal is to choose the medium that
makes the work easiest to understand. If the shape of the content matters, use
HTML. If the user only needs a quick answer, stay in markdown.

Adapted from `dogum/html-artifacts` under Apache-2.0.

## When to Use

Reach for a single-file HTML artifact when any of these are true:

- **Comparison or decision support:** multiple options, tradeoffs, proposals,
  designs, vendors, implementation paths, or review outcomes.
- **Spatial information:** architecture maps, module relationships, timelines,
  flows, diffs, dependency graphs, before/after states, or process diagrams.
- **Long reference material:** a plan, spec, report, postmortem, review, or
  explainer that needs headings, navigation, anchors, tabs, or collapsible
  sections.
- **Color or hierarchy carries meaning:** severity, status, ownership, risk,
  confidence, progress, dependency, or category labels.
- **A shared artifact:** something the user will send to teammates, attach to a
  PR, present in a meeting, or revisit later.
- **Interactive one-off tooling:** triage boards, prompt tuners, checklist
  editors, data labelers, config explorers, reorderable plans, or other small
  editors that need to export state back to markdown, JSON, or prompt text.

Common trigger words include: comparison, plan, spec, report, review,
postmortem, incident timeline, explainer, dashboard, diagram, flowchart, deck,
slides, mockup, prototype, editor, playground, roadmap, module map, and status
update.

## When to Stay in Markdown

Use markdown instead when the answer is:

- A short conversational reply.
- A code-only answer, patch explanation, config snippet, command sequence, or
  terminal-style procedure.
- A quick summary the reader will scan once.
- A file that humans will hand-edit and review in git repeatedly.
- A request where speed matters more than presentation.

If unsure, choose markdown for disposable content and HTML for deliverables.

## Output Contract

Every artifact must follow this contract:

1. **Single `.html` file.** Put CSS in `<style>` and JavaScript in `<script>`.
   Avoid build steps, bundlers, package installs, or multi-file assets unless the
   user explicitly asks for them.
2. **Works offline where practical.** Prefer system fonts, inline SVG, CSS, and
   small embedded data. If a CDN is useful, make it optional rather than
   load-bearing.
3. **Responsive layout.** Include the viewport meta tag and verify narrow
   screens do not overlap, clip text, or hide primary actions.
4. **Real layout.** Use columns for comparisons, timelines for sequences, lanes
   for ownership, diagrams for flows, and tables only when tabular reading is
   actually best.
5. **Readable immediately.** Start with a clear title, date/context when useful,
   and a short framing or TL;DR section.
6. **Accessible basics.** Use semantic landmarks, sufficient contrast, visible
   focus states, button labels, and text that still makes sense without color.
7. **No decorative overload.** Avoid generic gradient-card dashboards, emoji
   headings, excessive shadows, and one-color palettes unless the user's design
   system calls for them.
8. **Editors must export.** Any interactive editor must provide a copy/export
   path back to markdown, JSON, prompt text, or another user-useful plain-text
   format.

## Workflow

1. Decide whether HTML is justified. State the choice only if it affects the
   user's workflow.
2. Pick the artifact pattern from the request: comparison, plan, review, diagram,
   report, deck, or editor.
3. Design the content structure before writing code: sections, navigation,
   hierarchy, and the minimum useful interactions.
4. Write a descriptive kebab-case filename in the current workspace unless the
   user gives a path, for example `release-risk-review.html` or
   `backend-options-comparison.html`.
5. Implement self-contained HTML with inline CSS and any required inline JS.
6. Verify the file opens, the layout is responsive, and any copy/export action
   works.
7. Return the file path and a brief note about what the artifact contains.

## Artifact Patterns

| Request shape | Recommended structure |
| --- | --- |
| Option comparison | Side-by-side columns, decision matrix, recommendation strip, tradeoff notes |
| Implementation plan | Milestone timeline, dependency map, risk register, owner/status lanes |
| Code review or PR writeup | Summary, severity lanes, file/module map, annotated findings, test gaps |
| Architecture or flow | Inline SVG diagram, legend, sequence steps, failure paths, assumptions |
| Incident/postmortem | Timeline, impact strip, root-cause chain, action items with owners |
| Research or explainer | Sticky navigation, key terms, diagrams, examples, takeaways |
| Slide deck | Full-screen sections, keyboard navigation, speaker-note comments if useful |
| One-off editor | Editable state, drag/toggle/input controls, validation, copy/export button |

## HTML Defaults

Use these defaults unless a project design system or user preference overrides
them:

- Set `<html lang="en">` unless the requested artifact is in another language.
- Include `<meta charset="UTF-8">` and
  `<meta name="viewport" content="width=device-width, initial-scale=1">`.
- Prefer system font stacks for durability:
  `font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;`
- Keep body text around `16px` with comfortable line height.
- Constrain prose width to roughly `68ch`, but allow diagrams, tables, and
  comparison grids to use wider responsive containers.
- Use CSS custom properties for colors and spacing.
- Use `@media (max-width: ...)` rules to collapse grids into stacked sections.
- Use inline SVG for diagrams that must remain crisp and dependency-free.

## Interactive Editors

Interactive artifacts are successful only if the user's edits can leave the
page. For editors:

- Store state in memory or in the DOM; do not require a backend.
- Provide a clear `Copy` or `Export` control.
- Export a plain text representation the user can paste into chat, a PR, a
  config file, or another tool.
- Show copy success/failure without blocking the page.
- Keep controls stable on mobile: buttons, checkboxes, selects, sliders, and
  textareas should not resize unexpectedly when state changes.

Use local storage only if persistence is explicitly useful, and make export the
primary durability mechanism.

## Verification Checklist

- [ ] The artifact is a single `.html` file with no required build step.
- [ ] It opens in a browser and shows useful content immediately.
- [ ] The first screen explains what the artifact is and why it exists.
- [ ] Layout is responsive at desktop and mobile widths.
- [ ] Text does not overlap controls, diagrams, cards, or neighboring columns.
- [ ] Color is not the only signal for severity/status/category.
- [ ] Interactive controls work with mouse and keyboard.
- [ ] Any editor exports back to markdown, JSON, prompt text, or another clear
      plain-text format.
- [ ] The design fits the user's domain and does not look like a generic
      gradient-card template.

## Common Pitfalls

1. **Converting markdown one-to-one into tags.** Use HTML to reveal structure:
   columns, lanes, callouts, diagrams, and navigation.
2. **Overbuilding.** A single durable artifact should be polished, not a small
   app with unnecessary routing, dependencies, or state management.
3. **No export path for editors.** If the user can change state, they need a way
   to copy that state out.
4. **Tiny mobile afterthoughts.** Test narrow layouts early; tables and columns
   need intentional collapse behavior.
5. **Style before content.** The artifact must make the information easier to
   understand. Visual treatment should support the reading task.
6. **External dependencies for static work.** A static report should not require
   React, Tailwind, or chart libraries unless they materially improve the result.
