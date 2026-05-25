---
name: remote-server-70-98
description: Remote GPU server management for 10.10.70.98 (oem98) — NVIDIA RTX PRO 6000 Blackwell Server Edition (8×, 96GB each), Mellanox ConnectX-6 Dx NICs, NFS mount, initial setup and operations.
version: 1.0.0
author: Hermes Agent
license: MIT
---

# Remote Server 10.10.70.98 — NVIDIA RTX PRO 6000 Blackwell Server Edition

## Hardware Specs

| Component | Detail |
|-----------|--------|
| **Hostname** | oem98 |
| **IP** | 10.10.70.98 |
| **GPU** | 8× NVIDIA RTX PRO 6000 Blackwell Server Edition |
| **GPU Memory** | 97,887 MiB (~96 GB) each |
| **Compute Capability** | 12.0 |
| **Driver** | 595.58.03 (nvidia-driver-595-open) |
| **CUDA Driver** | 13.2 |
| **CUDA Toolkit** | 13.2 (cuda-nvcc-13-2) |
| **Python** | 3.12.13 with /data/venvs/vllm-ds4/ |

## Current Service (2-node cluster with 70.96)

As of 2026-05-19, 70.98 runs as a PP worker node in a 2-node cluster:

| Node | Role | GPU | Memory |
|------|------|-----|--------|
| 70.96 (oem96) | master, pp_rank=0, API server | RTX 5090 × 8 | 32 GB each |
| 70.98 (oem98) | worker, pp_rank=1, headless | RTX PRO 6000 × 8 | 96 GB each |

**Model:** deepseek_v4_pro (DeepSeek-V4-Pro, ~806 GB)
**Strategy:** TP=8 (intra-node) + PP=2 (inter-node) + EP enabled
**API key:** sk-warpdriveai
**Context length:** 1,048,576

### Start command (known working)

> **Important:** This vLLM fork (ds4-sm120) defaults to `CompilationMode.VLLM_COMPILE: 3`. This triggers a Gloo TCPStore bug on oem96 because `/etc/hosts` maps `127.0.1.1 → oem96`. The fix is setting `MASTER_ADDR=10.10.70.96` + `VLLM_HOST_IP=10.10.70.96` env vars.

```bash
# 70.96 (master)
export NCCL_SOCKET_IFNAME=ens20f0 GLOO_SOCKET_IFNAME=ens20f0
export TP_SOCKET_IFNAME=ens20f0 VLLM_HOST_IP=10.10.70.96 MASTER_ADDR=10.10.70.96

vllm serve /data/models/deepseekv4_pro \
  --host 0.0.0.0 --port 8000 \
  --trust-remote-code --distributed-executor-backend mp \
  --tensor-parallel-size 8 --pipeline-parallel-size 2 \
  --nnodes 2 --node-rank 0 \
  --master-addr 10.10.70.96 --master-port PORT \
  --kv-cache-dtype fp8 --block-size 256 \
  --enable-expert-parallel \
  -cc.pass_config.fuse_allreduce_rms=False \
  --max-model-len 1048576 \
  --gpu-memory-utilization 0.90 \
  --max-num-seqs 512 --max-num-batched-tokens 512 \
  --no-enable-flashinfer-autotune \
  --tokenizer-mode deepseek_v4 \
  --tool-call-parser deepseek_v4 \
  --enable-auto-tool-choice \
  --reasoning-parser deepseek_v4 \
  --api-key sk-warpdriveai \
  --served-model-name deepseek_v4_pro
```

Use a unique `--master-port` each time (29500, 29501, 29503, 29504, 29505, etc.) because previous process's TCP store can linger and cause EADDRINUSE or `Broken pipe` on restart.

### Pitfalls

- **Gloo bug on 70.96** — `/etc/hosts` maps `127.0.1.1 → oem96`, causing Gloo TCPStore to fail when `mode=VLLM_COMPILE`. Workaround: set `MASTER_ADDR=10.10.70.96` and `VLLM_HOST_IP=10.10.70.96`.
- **CUDA context not freed on pkill** — Killing vLLM with `pkill -9` leaves ~90 GB GPU memory allocated. The CUDA contexts are held by the GPU driver. Check `nvidia-smi pmon` for residual processes (like orphaned `VLLM::Worker_PP*`). Kill them with `sudo kill -9`. Xorg / gdm3 also pins GPU memory.
- **Port reuse** — Master port can get stuck with TCP store from previous run. Always use a new port on restart.
- **Context length vs memory** — `--max-model-len 1048576` works on this TP=8+PP=2 setup with gpu_mem=0.90. Increasing to 0.95 may cause OOM.
| **CPU** | Intel Xeon Gold 6530 (128 threads) |
| **RAM** | 1.0 TiB |
| **Disk (root)** | 1.7 TB LVM (13 GB used, 1.6 TB free) — `/dev/mapper/vgubuntu-root` |
| **Disk (data)** | 3.5 TB LVM — `/dev/mapper/datavg-datalv` mounted at `/data` (2.0G used, 3.3T free — model storage) |
| **NFS** | `/nasdata` — NFS mount from `10.10.80.223:/volume1/sharedata/software` (131 TB, 71 TB used) |
| **NICs** | Mellanox ConnectX-6 Dx (MT2892 Family) — dual-port, `ens35f0np0` (100G, 10.10.71.98/24 persistent via NM), `ens35f1np1` (unused) |
| **Management NIC** | Intel I350 Gigabit — `ens20f0` (10.10.70.98/24) |
| **System** | Ubuntu 22.04.1 LTS, Kernel 5.15.0-43-generic |
| **nvidia-persistenced** | v595.58.03 (running) |

## GPU Topology

- **NUMA 0** — GPU0-3, CPU 0-31,64-95 (connected via NODE)
- **NUMA 1** — GPU4-7, CPU 32-63,96-127 (connected via NODE)
- **Cross-NUMA** — SYS (PCIe + QPI/UPI)
- **NICs** — mlx5_0 (NIC0), mlx5_1 (NIC1) — both on NUMA 1 side (PIX to GPU4-7)
- **PCIe** — Gen 4, x16 (currently at Gen 1 per GPU — needs clock gating warm-up or BIOS config for full Gen 4)

## SSH Access

```bash
ssh jianliu@10.10.70.98 "command"
```

**No proxy needed** — this server has direct internet access (no HTTP proxy configured).

### Initial User Setup

The server was initially accessed via the `qs` user (password: `!QAZ2wsx`). The `jianliu` user was created with:

- Passwordless sudo (`/etc/sudoers.d/jianliu`)
- SSH key-based authentication (same key as other servers)

## Current Setup State (as of 2026-05-18)

| Component | Status | Version |
|-----------|--------|---------|
| CUDA Driver | ✅ Installed | 13.2 (driver 595.58.03) |
| CUDA Toolkit (nvcc) | ✅ Installed | 13.2.78 |
| Python 3.12 | ✅ Installed | 3.12.13 (deadsnakes PPA) |
| NCCL (system) | ✅ Installed | 2.30.4-1+cuda13.2 |
| Docker | ❌ Not installed | — |
| NVIDIA Container Toolkit | ❌ Not installed | — |
| nccl-tests | ❌ Not compiled | — |

### Python venv: `/data/venvs/vllm-ds4/`

Created matching 70.88's environment. Key packages:

| Package | Version |
|---------|---------|
| Python | 3.12.13 |
| pip | 26.1.1 |
| torch | 2.11.0+cu130 |
| transformers | 5.8.0 |
| huggingface_hub | 1.13.0 |
| flashinfer | 0.6.8.post1 |
| xgrammar | 0.2.0 |
| vllm (fork) | ✅ Installed | 0.1.dev1+gb709b75b4 (jasl/vllm ds4-sm120, editable install) |
| CUDA Dev Libraries | ✅ Installed | cuda-libraries-dev-13-2 (cublas, cusparse, nvrtc, etc.) |
| cmake | ✅ Installed | 4.3.2 (pip, set as system default via update-alternatives) |
| ninja | ✅ Installed | 1.10.1 (apt) |
| NCCL (system) | ✅ Installed | 2.30.4-1+cuda13.2 |
| Docker | ❌ Not installed | — |
| NVIDIA Container Toolkit | ❌ Not installed | — |
| nccl-tests | ❌ Not compiled | — |

## DeepSeek-V4-Pro Deployment

### Single-node (not possible — OOM)
DeepSeek-V4-Pro weights total 806 GiB, cannot fit on 8×96 GB GPUs (768 GB total). Must use PP=2 with a second node. TP=8 + EP works within each node when weight sharding is split across PP stages.

### Multi-node (working config)
**Master (70.96):** pp_rank=0, TP=8, EP=8, layers 0-30  
**Worker (70.98):** pp_rank=1, TP=8, EP=8, layers 31-60  

**Startup script:** `/data/venvs/vllm-ds4/start_dsv4_pro_2node.sh`

```bash
# 70.96 (master)
MASTER_PORT=29501 bash /data/venvs/vllm-ds4/start_dsv4_pro_2node.sh master

# 70.98 (worker)
MASTER_PORT=29501 bash /data/venvs/vllm-ds4/start_dsv4_pro_2node.sh worker
```

**API:** `http://10.10.70.96:8000`, model=`deepseek_v4_pro`, api-key=`sk-warpdriveai`

### Known Pitfalls
- **Port 29500 EADDRINUSE** — stale worker processes from failed starts can hold the port. Use `MASTER_PORT=29501` or fuser/kill stale processes.
- **Gloo 127.0.1.1 issue** — /etc/hosts on 70.96 maps `oem96` to `127.0.1.1`, causing Gloo TCPStore failures. Only affects local (intra-node) TP workers. Use different master_port to work around.
- **--compilation-config array expansion** — when using bash arrays `${SHARED_ARGS[@]}`, the JSON single quotes can be lost. Use inline command instead of array for `--compilation-config`.
- **vLLM compilation mode** — without explicit `--compilation-config`, default `mode: VLLM_COMPILE` (mode=3) will trigger inductor compilation which is slow and may cause Gloo timeouts.
| NCCL (torch bundled) | 2.28.9 |

### 1. Install CUDA Toolkit (nvcc)

No CUDA toolkit installed currently. Driver version 595.58.03 supports CUDA 13.2.

```bash
ssh jianliu@10.10.70.98 "echo 'PASSWORD' | sudo -S bash -c '
  wget -q https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2204/x86_64/cuda-keyring_1.1-1_all.deb
  dpkg -i cuda-keyring_1.1-1_all.deb
  apt-get update
'"

# Install nvcc matching driver CUDA version
ssh jianliu@10.10.70.98 "sudo -n apt-get install -y cuda-nvcc-13-2"
```

### 2. Install Docker

```bash
ssh jianliu@10.10.70.98 "sudo -N bash -c '
  apt-get update && apt-get install -y ca-certificates curl
  install -m 0755 -d /etc/apt/keyrings
  curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
  chmod a+r /etc/apt/keyrings/docker.asc
  echo \"deb [arch=\$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \$(. /etc/os-release && echo \"\$VERSION_CODENAME\") stable\" | tee /etc/apt/sources.list.d/docker.list > /dev/null
  apt-get update && apt-get install -y docker-ce docker-ce-cli containerd.io
  usermod -aG docker jianliu
'"
```

### 3. Install NVIDIA Container Toolkit

```bash
ssh jianliu@10.10.70.98 "sudo -N bash -c '
  curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
  curl -sL https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | sed \"s#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g\" | tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
  apt-get update && apt-get install -y nvidia-container-toolkit
  nvidia-ctk runtime configure --runtime=docker
  systemctl restart docker
'"
```

### 4. Install NCCL

```bash
ssh jianliu@10.10.70.98 "sudo -N apt-get install -y libnccl2 libnccl-dev"
```

### 5. Compile nccl-tests

```bash
ssh jianliu@10.10.70.98 "mkdir -p ~/work/bandwidth_test/ && cd ~/work/bandwidth_test/ && git clone https://github.com/NVIDIA/nccl-tests.git && cd nccl-tests && make -j\$(nproc)"
```

## NFS Mount Details

| Mount Point | Source | Size | Used |
|-------------|--------|------|------|
| `/nasdata` | `10.10.80.223:/volume1/sharedata/software` | 131 TB | 61 TB (47%) |
| `/data` | LVM (`datavg-datalv`) | 3.5 TB | 28K |

Contents of `/nasdata`: `sw2` directory (shared software repository).

## Inter-Server Model Transfer

To copy models between 10.10.70.98 and other servers in the subnet:

```bash
# 1. First add the source server's SSH public key to 98's authorized_keys:
# Get source's key:
ssh jianliu@10.10.70.88 "cat ~/.ssh/id_rsa.pub"
# Add it to 98:
ssh jianliu@10.10.70.98 'echo "<key-content>" >> ~/.ssh/authorized_keys'

# 2. Create destination directory (needs sudo for /data/):
ssh jianliu@10.10.70.98 "sudo -n mkdir -p /data/models && sudo -n chown jianliu:jianliu /data/models"

# 3. Run rsync from the source server (push mode):
ssh jianliu@10.10.70.88 "rsync -aP --partial /data/models/<model-name>/ jianliu@10.10.70.98:/data/models/<model-name>/"

# 4. To run in background with notification:
# Use terminal(background=true, notify_on_complete=true) from Hermes, 
# or nohup on the source:
ssh jianliu@10.10.70.88 "nohup rsync -aP --partial /data/models/<model-name>/ jianliu@10.10.70.98:/data/models/<model-name>/ > /tmp/rsync.log 2>&1 &"
```

**Note:** Neither server has the other's SSH key by default — you must add the key first.

### Current Models on /data/

| Model | Source | Size | Status |
|-------|--------|------|--------|
| deepseekv4_pro | 10.10.70.88 | ~806 GiB | Transferred 2026-05-18 |

## Key Differences from Other 10.10.70.x Servers

- **No HTTP proxy** — direct internet access (unlike 70.88, 95, 96)
- **RTX PRO 6000 Blackwell Server Edition** (96 GB) — not RTX 5090 (32 GB) like 88/93/95/96
- **Larger GPU memory** (96 GB vs 32 GB) — suitable for larger models
- **PCIe Gen 4 x16** — all GPUs (currently shows Gen 1, may just need GPU workload to ramp)
- **Dual ConnectX-6 Dx** NICs — for potential RDMA/network connectivity
- **Fresh installation** — minimal software installed, no CUDA toolkit, no Docker, no NCCL

## References

Detailed server-specific notes in `references/`:
- `references/70-98-detailed-setup.md` — Full setup details

## Pitfalls

- **No proxy** — unlike 88/95/96, no need for `source ~/.bashrc` for proxy
- **No CUDA toolkit** — nvcc not available, must be installed
- **No Docker** — must install from scratch
- **No NCCL** — must install separately
- **GPU currently at PCIe Gen 1** — bandwidth may be limited; idle GPUs downclock PCIe; running a CUDA workload should bring it to Gen 4
- **`qs` user access** — initial access via `qs` account is still available, but `jianliu` is the primary operational user
- **Do not hardcode passwords** — prefer SSH key auth for automated tasks
- **SSH key setup required for inter-server transfers** — neither this server nor its peers have each other's keys by default. Must manually add the source server's public key to authorize_keys before rsync. When appending via piped commands, single-quote expansion can fail silently — use `echo "$KEY" >> ~/.ssh/authorized_keys` from a properly expanded context, or inline the full key in quotes.
