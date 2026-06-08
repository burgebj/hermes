# Upstream awesome-design-md comparison

Snapshot date: 2026-06-08

Upstream repository: `VoltAgent/awesome-design-md`
Upstream commit: `6d10c14` (`2026-05-30T19:12:02+03:00`)

## Summary

`popular-web-designs` is a Hermes-ready curated subset/adaptation of `VoltAgent/awesome-design-md`, not a complete mirror of the upstream catalog. The bundled templates add Hermes implementation notes, CDN font substitutions, and HTML/CSS generation guidance, while upstream `DESIGN.md` files are generally longer formal design specifications.

At this snapshot:

| Source | Count |
|---|---:|
| Hermes `skills/creative/popular-web-designs/templates/*.md` | 54 |
| Upstream `design-md/*/DESIGN.md` | 73 |
| Shared design slugs | 54 |
| Upstream-only design slugs | 19 |
| Hermes-only design slugs | 0 |

## Upstream-only design slugs

These upstream design systems were not present in the bundled Hermes catalog at the snapshot above:

- `binance`
- `bmw-m`
- `bugatti`
- `dell-1996`
- `ferrari`
- `hp`
- `lamborghini`
- `mastercard`
- `meta`
- `nike`
- `playstation`
- `renault`
- `shopify`
- `slack`
- `starbucks`
- `tesla`
- `theverge`
- `vodafone`
- `wired`

## Format differences

Hermes templates:

- use `templates/<slug>.md` files loaded via `skill_view(name="popular-web-designs", file_path="templates/<slug>.md")`;
- include a Hermes implementation notes block for font substitutions, paste-ready Google Fonts links, and HTML/CSS generation guidance;
- are optimized as practical visual vocabularies for generated web artifacts.

Upstream files:

- use `design-md/<slug>/DESIGN.md` and usually a companion `README.md`;
- are generally more verbose formal design analyses;
- often include YAML frontmatter and canonical DESIGN.md sections.

## Safe refresh strategy

When refreshing this bundled skill from upstream:

1. Compare local `templates/*.md` against upstream `design-md/*/DESIGN.md` before claiming the catalog is complete.
2. Import missing upstream designs in small batches rather than one very large PR.
3. Preserve Hermes-specific implementation notes, especially font substitutions and artifact-generation guidance.
4. Keep generated website docs in sync with the corresponding skill changes.
5. Re-run skill/documentation smoke tests after editing bundled skills.
