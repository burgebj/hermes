---
name: remote-server-70-96
description: Remote GPU server management for 10.10.70.96 (oem96) — 8× NVIDIA RTX 5090 (32GB each), DeepSeek-V4-Pro master node, LVM storage, proxy access, SSH and operations.
version: 1.0.0
author: Hermes Agent
license: MIT
---

# Remote Server 10.10.70.96 — NVIDIA RTX 5090

## Access

```bash
ssh jianliu@10.10.70.96
```

| Field | Value |
|-------|-------|
| **Username** | jianliu |
| **IP (management)** | 10.10.70.96 |
| **IP (100G)** | 10.10.71.96 |
| **Password** | !QAZ2wsx |
| **Sudo Password** | !QAZ2wsx (same as login) |

> **Important:** This server has a proxy (`http://10.10.60.140:7890`) configured in `~/.bashrc`. Non-interactive SSH does NOT load `.bashrc` automatically. **Always prefix remote commands with `source ~/.bashrc &&`**.

### SSH Patterns

```bash
# Non-interactive command (most common)
ssh jianliu@10.10.70.96 "source ~/.bashrc && command"

# Sudo commands — use SUDO_ASKPASS helper (sudo -S piped password is blocked)
ssh jianliu@10.10.70.96 'cat > /tmp/spwd_helper.sh << '\''EOF'\''
#!/bin/bash
echo "!QAZ2wsx"
EOF
chmod 700 /tmp/spwd_helper.sh
SUDO_ASKPASS=/tmp/spwd_helper.sh sudo -A <command>; rm -f /tmp/spwd_helper.sh'

# SCP / file transfer
scp local_file jianliu@10.10.70.96:/path/to/dest/
```

## Hardware Specs

| Component | Detail |
|-----------|--------|
| **Hostname** | oem96 |
| **IP (management)** | 10.10.70.96 on `ens20f0` (Intel I350 1GbE) |
| **IP (high-speed)** | 10.10.71.96/24 on `ens35f0np0` (ConnectX-6 Dx 100GbE) |
| **GPU** | 8× NVIDIA RTX 5090 |
| **GPU Memory** | 32 GB each (256 GB total) |
| **Compute Capability** | 12.0 (Blackwell) |
| **Driver** | 595.58.03 |
| **CUDA Driver** | 13.2 |
| **CPU** | Intel Xeon |
| **System** | Ubuntu 22.04.1 LTS, Kernel 5.15.0-43-generic |
| **Storage (root)** | 1.7 TB LVM — `/dev/mapper/vgubuntu-root` |
| **Storage (data)** | LVM, mounted at `/data` |
| **Proxy** | `http://10.10.60.140:7890` (via `~/.bashrc`) |

### Network Interfaces

| Interface | Hardware | Speed | IP | Purpose |
|-----------|----------|-------|----|---------|
| ens20f0 | Intel I350 (igb) | 1 Gb/s | 10.10.70.96 | Management, SSH |
| ens35f0np0 | ConnectX-6 Dx (mlx5) | 100 Gb/s | 10.10.71.96 | vLLM NCCL/Gloo/TP |
| ens35f1np1 | ConnectX-6 Dx (mlx5) | 100 Gb/s | — | Unused (no cable) |

ens35f0np0 is configured via NetworkManager (persistent across reboots):

## Role: DeepSeek-V4-Pro Master Node

As of 2026-05-19, 70.96 is the master node (pp_rank=0) in the 2-node cluster with 70.98:

| Node | Role | GPU | Memory |
|------|------|-----|--------|
| 70.96 (oem96) | master, pp_rank=0, API server | RTX 5090 × 8 | 32 GB each |
| 70.98 (oem98) | worker, pp_rank=1, headless | RTX PRO 6000 × 8 | 96 GB each |

**Model:** deepseek_v4_pro (DeepSeek-V4-Pro, ~806 GB)
**Strategy:** TP=8 (intra-node) + PP=2 (inter-node) + EP enabled
**API key:** sk-warpdriveai

### Start command (70.96 as master)

The startup script is at `/data/venvs/vllm-ds4/start_dsv4_pro_2node.sh`.
NCCL/Gloo/TP use `ens35f0np0` (ConnectX-6 100G, 10.10.71.96).

```bash
# 70.96 (master)
bash /data/venvs/vllm-ds4/start_dsv4_pro_2node.sh master

# 70.98 (worker)
bash /data/venvs/vllm-ds4/start_dsv4_pro_2node.sh worker
```

Key env vars inside the script:
```bash
export NCCL_SOCKET_IFNAME=ens35f0np0
export GLOO_SOCKET_IFNAME=ens35f0np0
export TP_SOCKET_IFNAME=ens35f0np0
export VLLM_HOST_IP="10.10.71.96"
export MASTER_ADDR="10.10.71.96"
```

Use a unique `--master-port` each time (29500, 29501, etc.).

> **Note:** `--no-enable-flashinfer-autotune` has been removed from the script. It is irrelevant for DeepSeek V4 which uses MLA (Multi-Head Latent Attention) with a custom Triton backend — FlashInfer autotune has no effect on this model.

### API

**Endpoint:** `http://10.10.70.96:8000`
**Model name:** `deepseek_v4_pro`
**API key:** `sk-warpdriveai`

## vLLM Environment

- Source: `/data/vllm-ds4-sm120/`
- Venv: `/data/venvs/vllm-ds4/` (Python 3.12, PyTorch 2.11.0+cu130)
- CUDA dev packages installed

## Quick Health Check

```bash
ssh jianliu@10.10.70.96 "source ~/.bashrc && \
  echo '=== GPU ==='; nvidia-smi --query-gpu=name,driver_version --format=csv,noheader | head -1; \
  echo '=== CUDA Driver ==='; nvidia-smi -q | grep 'CUDA Version'; \
  echo '=== Memory ==='; nvidia-smi --query-gpu=memory.used,memory.total --format=csv,noheader; \
  echo '=== Disk ==='; df -h / /data | tail -2"
```

## Batch Operations (cluster)

Part of 93/95/96 cluster — use bulk commands:

```bash
for h in 93 95 96; do
  echo "=== 10.10.70.$h ==="
  ssh jianliu@10.10.70.$h "source ~/.bashrc && command"
done
```

## Pitfalls

- **Proxy required** — Always `source ~/.bashrc` before any command. Non-interactive SSH never loads `.bashrc`.
- **Gloo 127.0.1.1 bug** — `/etc/hosts` maps `127.0.1.1 → oem96`, causing Gloo TCPStore to fail when `mode=VLLM_COMPILE`. Workaround: set `MASTER_ADDR=10.10.71.96` and `VLLM_HOST_IP=10.10.71.96`.
- **Port reuse** — Master port can get stuck with TCP store from previous run. Always use a new port on restart.
- **`!` in password** — When using the password in bash, wrap in single quotes: `'!QAZ2wsx'` to prevent history expansion.
- **ConnectX-6 vs Intel NIC** — `ens20f0` is the 1GbE Intel NIC, `ens35f0np0` is the 100G ConnectX-6. NCCL must use `ens35f0np0` for multi-node communication.
- **FlashInfer irrelevant** — DeepSeek V4 uses MLA attention (Triton backend). FlashInfer autotune flags have no effect.

## Network Hardware Discovery

Quick check for NIC inventory on a node:

```bash
lspci | grep -i mellanox          # physical card
ip -br link show                   # all interfaces
ethtool ens35f0np0 | grep Speed    # link speed
rdma link show                     # RDMA state
ls /sys/class/infiniband/          # IB devices
lsmod | grep mlx5                  # driver loaded
```

## References

Detailed notes in `references/`:
- `references/70-96-detailed-setup.md` — Full setup details
