---
name: phantom-mesh
description: "Decentralized, end-to-end encrypted peer-to-file sharing over the Reticulum mesh network. Uses the terminal tool to run phantom CLI commands. Triggers: phantom, reticulum, mesh, p2p file sharing, encrypted transfer, ghost file, .ghost"
version: 1.0.0
author: roogle-dev
license: MIT
metadata:
  hermes:
    tags: [p2p, mesh, file-sharing, encryption, reticulum, decentralized, torrent, lora, radio]
    category: devops
    requires_toolsets: [terminal]
---

# Phantom Mesh — P2P Encrypted File Sharing over Reticulum

Share files over [Reticulum](https://reticulum.network/) — a cryptographic mesh networking stack for resilient, long-range, low-bandwidth communications. No central servers. No trackers. No cleartext. Just the mesh.

All commands use the **terminal tool** to run `phantom` CLI commands.

## When to Use

- User wants to share files without central servers (like a torrent, but decentralized)
- User needs encrypted file transfer over LoRa, packet radio, serial links, or TCP/IP
- User mentions Reticulum, mesh networking, or .ghost files
- User wants resilient P2P file sharing that works offline or over long-range radio
- User needs censorship-resistant file distribution

## Prerequisites

### 1. Install Phantom

```bash
# Clone the repository
git clone https://github.com/roogle-dev/reticulum-phantom.git ~/reticulum-phantom
cd ~/reticulum-phantom

# Install dependencies
pip install rns rich textual
```

### 2. Verify Installation

```bash
cd ~/reticulum-phantom && python3 phantom.py --help
```

### 3. First Run

The first command automatically creates:
- A cryptographic identity (X25519/Ed25519 keypair)
- Default Reticulum configuration (`~/.reticulum/config`)
- Data directory (`~/Library/Application Support/ReticulumPhantom/` on macOS, or `~/.local/share/ReticulumPhantom/` on Linux)

## Quick Reference

| Command | Description |
|---------|-------------|
| `phantom seed <file>` | Seed a file (auto-creates `.ghost`) |
| `phantom download <file.ghost>` | Download via `.ghost` file |
| `phantom create <file>` | Create `.ghost` without seeding |
| `phantom info <file.ghost>` | Show ghost metadata |
| `phantom identity` | Show node identity |
| `phantom seed-all [dir]` | Seed all files in a directory |
| `phantom settings` | View/update settings |
| `phantom clean` | Remove temp files |
| `phantom tui` | Interactive dashboard |

All commands must be run from the Phantom directory:

```bash
cd ~/reticulum-phantom
```

## Workflow

### Share a File (2 steps)

```bash
# 1. Seed — creates .ghost file and starts serving on the mesh
cd ~/reticulum-phantom && python3 phantom.py seed movie.mkv

# 2. Share the .ghost file (email, USB, Discord, etc.)
# The .ghost file is created next to the original: movie.mkv.ghost
```

### Download a File

```bash
# Download using a .ghost file
cd ~/reticulum-phantom && python3 phantom.py download movie.mkv.ghost

# Download to a specific folder
cd ~/reticulum-phantom && python3 phantom.py download movie.mkv.ghost -o ~/Downloads
```

### Seed an Entire Directory

```bash
cd ~/reticulum-phantom && python3 phantom.py seed-all /path/to/files/
```

## The .ghost File

The `.ghost` file is the Phantom equivalent of a `.torrent` file:

```
┌─────────────────────────────────────────────────────────┐
│  1. Seed:     phantom seed movie.mkv                    │
│               → creates movie.mkv.ghost                 │
│               → announces on mesh, serves chunks        │
│                                                         │
│  2. Share:    Send movie.mkv.ghost to your friend       │
│               (email, USB, Discord, whatever)           │
│                                                         │
│  3. Download: phantom download movie.mkv.ghost          │
│               → auto-discovers ALL seeders              │
│               → downloads in swarm mode                 │
│               → auto-seeds after completion             │
└─────────────────────────────────────────────────────────┘
```

## Key Features

- **E2E Encrypted**: All transfers use Reticulum's X25519/Ed25519 encryption
- **Fully Decentralized**: No trackers, no central servers, no DNS
- **Mesh-Native**: Works over TCP/IP, LoRa, packet radio, serial links
- **Multi-Peer Swarm**: Download from multiple seeders simultaneously
- **Auto-Failover**: If a seeder goes offline, others pick up instantly
- **Resume Support**: Downloads pick up where they left off
- **PEX (Peer Exchange)**: Seeders share peer lists over encrypted links
- **Auto-Seed**: After downloading, automatically starts seeding

## Network Configuration

Reticulum config is at `~/.reticulum/config`. Default uses `AutoInterface` (UDP link-local).

For WAN connectivity, add a TCP interface:

```toml
[[My TCP Interface]]
  type = TCPInterface
  enabled = Yes
  target_ip = 192.168.1.100
  target_port = 42420
```

For LoRa hardware, add an RNode interface per the [Reticulum docs](https://reticulum.network/manual/interfaces.html).

## Settings

View and modify settings:

```bash
cd ~/reticulum-phantom && python3 phantom.py settings
cd ~/reticulum-phantom && python3 phantom.py settings chunk_size 524288
```

Key settings:

| Setting | Default | Description |
|---------|---------|-------------|
| `chunk_size` | 1048576 (1MB) | File chunk size |
| `announce_interval` | 10800 (3h) | Re-announce interval |
| `auto_seed_after_download` | true | Auto-seed after download |
| `tcp_enabled` | true | Enable TCP interface |
| `tcp_port` | 7777 | TCP listen port |
| `download_directory` | `~/Downloads` | Download location |

## Troubleshooting

**No seeders found**: Ensure the seeder is running and the `.ghost` file contains the seeder's destination hash. Check with `phantom info <file.ghost>`.

**Download hangs**: The seeder may be offline. Try `phantom probe <ghost_hash>` to test mesh connectivity.

**Permission errors**: Ensure write access to `~/Library/Application Support/ReticulumPhantom/` (macOS) or `~/.local/share/ReticulumPhantom/` (Linux).

## Pitfalls

- First run creates RNS config automatically (~4s delay on first command)
- Seeding requires the source file to remain on disk
- Ghost hash changes if file content changes
- `seed` from `.ghost` requires source file next to it or at stored path
- Transport is disabled by default — enable in config for multi-node mesh routing

### Installation gotcha (Python 3.9)

`pip install -e .` fails because `pyproject.toml` uses `setuptools.backends._legacy` which is not available on Python 3.9. Install dependencies directly:

```bash
pip3 install "rns>=0.9.0" "rich>=14.0.0" "textual>=0.90.0"
```

Then run via `python3 phantom.py <cmd>` (no `pip install` needed — it's a pure Python project).

### Ghost file location — seeder destinations

After starting a seeder, the **library ghost** (at `$PHANTOM_DATA/ghosts/<name>.ghost`) gets updated with the seeder's destination hash. The ghost file **next to the original source file does NOT get updated** (unless `source_path` was set).

When downloading, always use the library ghost:

```bash
# Seed (updates library ghost)
python3 phantom.py seed myfile.bin

# Download using library ghost (has seeder dests)
python3 phantom.py download "$HOME/Library/Application Support/ReticulumPhantom/ghosts/myfile.bin.ghost"
```

Not the original `myfile.bin.ghost` next to the source — it won't have the seeder destination.

### Same-process seed+download doesn't work

You cannot seed and download in the same Python process. RNS shared instance has no mesh routing for intra-process destinations. Use two separate CLI invocations:

```bash
# Terminal 1
python3 phantom.py seed myfile.bin

# Terminal 2 (after seeder is running)
python3 phantom.py download "/path/to/library/ghost/myfile.bin.ghost"
```

Both processes share the RNS socket automatically (default `share_instance = Yes`), so the leecher discovers the seeder via the mesh announce system.

### Auto-seed after download bug

After a successful download, the auto-seed feature crashes with `__init__() missing 1 required positional argument: 'identity'` in the `cmd_download()` function. The download itself completes fine — this only affects the post-download auto-reseed. Workaround: manually seed after download with `phantom seed <file>`.
