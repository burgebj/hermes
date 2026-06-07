# Visibility OS

Visibility OS is a Hermes dashboard plugin for engineering-lead visibility:

- scans configured GitHub repositories for actionable issues, PRs, and failing CI
- correlates CI failures with PR state before proposing work
- drafts Slack or GitHub updates behind a human approval queue
- runs a one-click **Fix CI** lane that prepares a local branch, self-audits, launches an independent fresh-session review, then queues a separate **Push branch** decision
- runs the same one-click **Fix Issue** lane for GitHub issues

## Configuration

Copy `plugins/visibility_os/.env.example` into your Hermes profile `.env` file, usually:

```bash
cp plugins/visibility_os/.env.example ~/.hermes/.env
```

Then edit these values for your organisation:

- `VISIBILITY_OS_COMPANY_NAME`: label used in agent prompts, for example `Acme Robotics`
- `VISIBILITY_OS_GITHUB_ORGS`: comma-separated GitHub org owners that Visibility OS may inspect or modify
- `VISIBILITY_OS_GITHUB_REPOS`: comma-separated `owner/repo` list scanned by **Scan GitHub Repos**
- `VISIBILITY_OS_DEFAULT_SLACK_CHANNEL`: default Slack destination for drafted updates
- `SLACK_BOT_TOKEN`: required only when executing Slack message actions

GitHub access uses the local `gh` CLI session:

```bash
gh auth login
gh auth refresh -h github.com -s repo -s read:org -s workflow
```

## Safety model

Visibility OS is intentionally scoped by environment configuration:

- GitHub actions and Fix CI lanes reject repositories outside `VISIBILITY_OS_GITHUB_ORGS`.
- If `VISIBILITY_OS_GITHUB_REPOS` is set, scans and actions are restricted to that explicit repo list.
- The Fix CI and Fix Issue lanes prepare local branches only. They do not push, open PRs, merge, or deploy.
- A separate fresh Hermes session reviews the prepared branch before any push action is queued.
- Pushing the branch and creating the PR remains a separate explicit human action.

## Running locally

```bash
hermes dashboard --host 0.0.0.0 --port 9119 --no-open --skip-build --insecure
```

Then open the Hermes dashboard and choose **Visibility OS**.
