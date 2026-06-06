# Pawrtal

Pawrtal adds portable animated companions to Hermes sessions. It can import
Codex pet packs, render them as a transparent desktop companion, and show
Hermes task progress in compact bubbles above the character.

This bundled plugin exposes the Hermes-side commands and hooks. The companion
renderer and default packs live in the Pawrtal CLI:

https://github.com/nativ3ai/Pawrtal

## Install Pawrtal

macOS/Linux:

```bash
curl -fsSL https://raw.githubusercontent.com/nativ3ai/Pawrtal/main/install.sh | bash
```

Windows PowerShell:

```powershell
iwr https://raw.githubusercontent.com/nativ3ai/Pawrtal/main/install.ps1 -UseB | iex
```

Then enable the Hermes plugin:

```bash
hermes plugins enable pawrtal
```

## Use

```text
/pawrtal list
/pawrtal use h3retik
/pawrtal spawn h3retik
/pawrtal vanish h3retik
/pawrtal status
/pawrtal update
```

Start the desktop companion:

```bash
pawrtal spawn h3retik
```

Hide it again:

```bash
pawrtal vanish h3retik
```

You can also start the desktop renderer directly:

```bash
pawrtal desktop hermes
```

The plugin writes activity state under `~/.pawrtal/state/hermes`, so the
desktop companion can react to Hermes thinking, tool calls, success, failure,
and completed replies.
