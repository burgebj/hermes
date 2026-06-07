# GitHub multi-repo inventory recipe

Use this when asked to search an account or organization for repositories related to a keyword, model family, workflow, or review capability.

## 1. Start with GitHub metadata

```bash
gh repo list OWNER --limit 1000 --json \
  name,nameWithOwner,description,isPrivate,isArchived,isFork,primaryLanguage,defaultBranchRef,url
```

Prefer metadata first; it is fast and avoids cloning everything prematurely.

## 2. Inspect top-level repository shape

For each candidate repository (or all repositories for a full audit), gather:

- top-level files: `README.md`, `SKILL.md`, package manifests
- directories: `scripts/`, `tests/`, `examples/`, `references/`, `schemas/`
- file count excluding `.git`, `node_modules`, virtualenvs, build artifacts
- test count and script count
- keywords in repository name, description, README, SKILL.md, and package metadata

Classify repositories roughly as:

- **lightweight skill/doc repo**: often just `README.md` + `SKILL.md` and small references/examples
- **review/eval workflow repo**: scripts + schemas + examples + skill/docs
- **application/codebase**: package manifests, source dirs, tests, CI, substantial file count
- **vendor/noisy repo**: large `node_modules`, generated files, or forked dependency

## 3. Save a JSON artifact

Write a durable artifact for the session, e.g.:

```text
/tmp/OWNER_repo_inventory.json
```

Suggested fields per repository:

```json
{
  "full_name": "OWNER/repo",
  "description": "...",
  "private": true,
  "archived": false,
  "fork": false,
  "language": "Python",
  "file_count": 123,
  "has_skill": true,
  "manifests": ["pyproject.toml", "package.json"],
  "tests_count": 14,
  "scripts_count": 3,
  "keyword_hits": ["qwen", "review"]
}
```

## 4. Summarize for the user

Report counts first, then the important repositories:

- total repositories, private/public, archived, forks
- repositories with `SKILL.md`
- likely lightweight skill/doc repositories
- real code/app repositories
- keyword-specific matches
- recommended next inspection targets

Avoid overclaiming from names alone: mark likely roles and call out when a repository needs deeper inspection.