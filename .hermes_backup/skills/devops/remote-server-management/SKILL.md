---
name: remote-server-management
description: Remote GPU server management — SSH access, CUDA/nvcc toolchain, NCCL configuration, nccl-tests compilation, bandwidth testing, and multi-server cluster operations for servers in the 10.10.70.x network.
version: 1.1.0
author: Hermes Agent
license: MIT
---

# Remote Server Management

Umbrella skill for managing remote GPU servers in the 10.10.70.x network. Covers SSH access patterns, CUDA toolchain installation, NCCL version management, nccl-tests compilation, bandwidth testing, Docker/vLLM deployment, and multi-server cluster operations.

## Supported Servers

| Server | Hostname | GPU | GPUs | Notes |
|--------|----------|-----|------|-------|
| 10.10.70.66 | oem66 | A100 40GB | 6× | Older setup, full CUDA 12.3 installed, no proxy needed |
| 10.10.70.88 | oem88 | RTX 5090 | 8× | Primary dev server, has proxy, has vLLM fork compiled |
| 10.10.70.93 | oem93 | RTX 5090 | 8× | Cluster node 1 — no proxy, bare metal initially |
| 10.10.70.95 | oem95 | RTX 5090 | 8× | Cluster node 2 — has proxy (via .bashrc), LVM storage, DeepSeek-V4-Pro models |
| 10.10.70.96 | oem96 | RTX 5090 | 8× | Cluster node 3 — has proxy (via .bashrc), DeepSeek-V4-Pro master node |
| 10.10.70.98 | oem98 | RTX PRO 6000 Blackwell SE | 8× | New server, 96 GB GPUs, no proxy, DeepSeek-V4-Pro worker node |
| 10.10.70.96 | oem96 | Cluster node 3, proxy via .bashrc, LVM storage details |
| 10.10.70.98 | oem98 | New RTX PRO 6000 Blackwell SE server, no proxy, no CUDA/Docker yet |
| 10.10.70.98 | oem98 | RTX PRO 6000 Blackwell SE | 8× | New server, 96 GB GPUs, no proxy, no Docker yet |

## SSH Connection Patterns

### No-proxy servers (66, 93, 98)
```bash
ssh -o StrictHostKeyChecking=accept-new jianliu@10.10.70.XX "command"
```
No need to `source ~/.bashrc` — direct internet access.

### Proxy servers (88, 95, 96)
> **Important:** These servers have a proxy (`http://10.10.60.140:7890`) configured in `~/.bashrc`. Non-interactive SSH does NOT load `.bashrc` automatically. **Always prefix commands with `source ~/.bashrc &&`**:

```bash
ssh jianliu@10.10.70.XX "source ~/.bashrc && command"
ssh -t jianliu@10.10.70.XX "source ~/.bashrc && echo 'PASSWORD' | sudo -S apt-get install -y PACKAGE"
```

### Sudo password handling
- All servers share the same sudo password
- `!` in bash needs single quotes: `echo '!QAZ2wsx' | sudo -S ...`
- Use `-t` flag when PTY is needed (watch, top, interactive sudo)

## CUDA / nvcc Installation

### For RTX 5090 (Blackwell, CC 12.0)
Requires CUDA 12.8+. Install via fine-grained nvcc package (~87 MB):

```bash
# Add NVIDIA repository (first time only)
ssh jianliu@10.10.70.XX "echo 'PASSWORD' | sudo -S bash -c '
  wget -q https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2204/x86_64/cuda-keyring_1.1-1_all.deb
  dpkg -i cuda-keyring_1.1-1_all.deb
  apt-get update
'"

# Install nvcc matching driver CUDA version (check with nvidia-smi -q | grep "CUDA Version")
ssh jianliu@10.10.70.XX "echo 'PASSWORD' | sudo -S apt-get install -y cuda-nvcc-13-2"
```

**Available nvcc versions:** `cuda-nvcc-12-8`, `cuda-nvcc-13-0`, `cuda-nvcc-13-1`, `cuda-nvcc-13-2`

### For A100 (CC 8.0, sm_80)
Server 70.66 has full CUDA 12.3 installed at `/usr/local/cuda-12.3`. Note: system `/usr/bin/nvcc` is CUDA 10.1 — always use `/usr/local/cuda/bin/nvcc` instead.

### Add CUDA to PATH
```bash
ssh jianliu@10.10.70.XX "echo 'PASSWORD' | sudo -S tee -a /etc/profile.d/cuda.sh > /dev/null << 'EOF'
export PATH=/usr/local/cuda/bin:\$PATH
export LD_LIBRARY_PATH=/usr/local/cuda/lib64:\$LD_LIBRARY_PATH
EOF
sudo chmod +x /etc/profile.d/cuda.sh"
```

## NCCL Version Management

### Install NCCL
```bash
# Check available versions
ssh jianliu@10.10.70.XX "source ~/.bashrc && apt-cache madison libnccl2"

# Install matching CUDA version
ssh jianliu@10.10.70.XX "echo 'PASSWORD' | sudo -S apt-get install -y libnccl2 libnccl-dev"
```

### Version compatibility
| CUDA Version | Latest NCCL | Notes |
|-------------|-------------|-------|
| cuda13.2 | 2.30.4 | Latest |
| cuda13.0 | 2.28.9 | Used on 70.88 |
| cuda12.9 | 2.30.4 | |
| cuda12.8 | 2.26.2 | Minimum for Blackwell |
| cuda12.x | Varied | For A100 on 70.66 |

### Verify NCCL
```bash
cat > /tmp/test_nccl.cu << 'EOF'
#include <nccl.h>
#include <stdio.h>
int main() { printf("NCCL compiled OK (version code: %d)\n", NCCL_VERSION_CODE); return 0; }
EOF
/usr/local/cuda/bin/nvcc -I/usr/include -o /tmp/test_nccl /tmp/test_nccl.cu -lnccl 2>&1 && /tmp/test_nccl
```

## nccl-tests Compilation & Bandwidth Testing

### Compile
```bash
ssh jianliu@10.10.70.XX "source ~/.bashrc && mkdir -p ~/work/bandwidth_test/ && \
  cd ~/work/bandwidth_test/ && \
  git clone https://github.com/NVIDIA/nccl-tests.git && \
  cd nccl-tests && \
  make -j\$(nproc)"
```

### Run tests
```bash
# Single GPU validation
./all_reduce_perf -b 8 -e 256M -f 2 -g 1 2>&1 | tail -5

# Full GPU test (adjust -g N for server's GPU count)
CUDA_VISIBLE_DEVICES=0,1,2,3 ./all_reduce_perf -b 8 -e 8G -f 2 -g 4 2>&1
./all_reduce_perf -b 8 -e 8G -f 2 -g 8 2>&1
```

### Output interpretation
- **AlgoBW**: Algorithm bandwidth (actual data/time)
- **BusBW**: Bus bandwidth (accounts for NCCL internal data movement, ~1.7-2× AlgoBW)

## Docker Setup & vLLM Deployment

### Install Docker
```bash
ssh jianliu@10.10.70.XX "echo 'PASSWORD' | sudo -S bash -c '
  apt-get update && apt-get install -y ca-certificates curl
  install -m 0755 -d /etc/apt/keyrings
  curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
  chmod a+r /etc/apt/keyrings/docker.asc
  echo \"deb [arch=\$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \$(. /etc/os-release && echo \"\$VERSION_CODENAME\") stable\" | tee /etc/apt/sources.list.d/docker.list > /dev/null
  apt-get update && apt-get install -y docker-ce docker-ce-cli containerd.io
  usermod -aG docker jianliu
'"
```

### Install NVIDIA Container Toolkit
```bash
ssh jianliu@10.10.70.XX "echo 'PASSWORD' | sudo -S bash -c '
  curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
  curl -sL https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | sed \"s#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g\" | tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
  apt-get update && apt-get install -y nvidia-container-toolkit
  nvidia-ctk runtime configure --runtime=docker
  systemctl restart docker
'"
```

### vLLM Docker deployment
```bash
docker run --gpus all \
  -v /home/jianliu/work/models:/models \
  -p 8000:8000 \
  --shm-size=32g \
  vllm/vllm-openai:latest \
  --model /models/MODEL_NAME --host 0.0.0.0 --port 8000 \
  --tensor-parallel-size 8 --gpu-memory-utilization 0.90 --trust-remote-code
```

## Multi-Server Cluster Operations

For the 93/95/96 cluster (same hardware, Mellanox ConnectX-6 Dx NICs):

### Batch execution
```bash
for host in 93 95 96; do
  echo "=== 10.10.70.$host ==="
  ssh jianliu@10.10.70.$host "source ~/.bashrc && command"
done
```

### NCCL socket interface (multi-node)
```bash
export NCCL_SOCKET_IFNAME=ens20f0
export NCCL_IB_DISABLE=1
export NCCL_DEBUG=INFO
```

### Quick health check
```bash
ssh jianliu@10.10.70.XX "source ~/.bashrc && \
  echo '=== GPU ==='; nvidia-smi --query-gpu=name,driver_version --format=csv,noheader | head -1; \
  echo '=== CUDA Driver ==='; nvidia-smi -q | grep 'CUDA Version'; \
  echo '=== nvcc ==='; /usr/local/cuda/bin/nvcc --version 2>&1 | tail -2; \
  echo '=== NCCL ==='; awk '/NCCL_(MAJOR|MINOR|PATCH)/{printf \"%s.%s.%s\\n\", \$3, \$3, \$3}' /usr/include/nccl.h; \
  echo '=== Disk ==='; df -h / | tail -1"
```

## vLLM Server Management

### Finding server process and config

```bash
# Find running vLLM processes and their startup config
ssh jianliu@10.10.70.XX "ps aux | grep 'vllm serve' | grep -v grep"

# Read the startup script to get full config including API key
ssh jianliu@10.10.70.XX "cat /path/to/start_script.sh"

# Get exact cmdline (includes API key which may be stripped from ps output)
ssh jianliu@10.10.70.XX "cat /proc/PID/cmdline | tr '\0' ' '"
```

### Graceful restart procedure

1. **Identify all vLLM-related PIDs** (main process, resource_tracker, workers):
```bash
ssh jianliu@10.10.70.XX "ps aux | grep vllm | grep -v grep | awk '{print \$2}'"
```

2. **Kill processes** (SIGTERM first, SIGKILL if they don't die):
```bash
ssh jianliu@10.10.70.XX "kill PID1 PID2 ... 2>/dev/null; sleep 2"
# Force kill if still alive:
ssh jianliu@10.10.70.XX "kill -9 PID1 PID2 ... 2>/dev/null; sleep 2"
```

3. **Start the server** using its startup script (background recommended):
```bash
ssh jianliu@10.10.70.XX "cd /path/to/venv && bash start_script.sh"
# From Hermes: use terminal(background=true, notify_on_complete=true)
```

4. **Verify the server is up** — it can take several minutes for large models with compilation:
```bash
# Check if process is running
ssh jianliu@10.10.70.XX "ps aux | grep vllm | grep -v grep"

# Health endpoint (loads faster than models endpoint)
python3 -c 'import urllib.request; r=urllib.request.urlopen("http://localhost:8000/health"); print(r.status)'

# Models endpoint with API key (get max_model_len, served model name)
python3 -c '
import json, urllib.request
req = urllib.request.Request("http://localhost:8000/v1/models")
req.add_header("Authorization", "Bearer API_KEY_HERE")
r = urllib.request.urlopen(req)
for m in json.loads(r.read().decode())["data"]:
    print(json.dumps(m, indent=2))
'

# Quick chat test
python3 -c '
import json, urllib.request
body = json.dumps({"model":"MODEL_NAME","messages":[{"role":"user","content":"hi"}],"max_tokens":10}).encode()
req = urllib.request.Request("http://localhost:8000/v1/chat/completions", data=body,
    headers={"Content-Type":"application/json", "Authorization":"Bearer API_KEY_HERE"})
r = urllib.request.urlopen(req)
res = json.loads(r.read().decode())
print(res["choices"][0]["message"]["content"])
'
```

### Verifying context length

The `max_model_len` is set via `--max-model-len` in the startup script. To confirm it at runtime, check the v1/models endpoint response which includes `max_model_len` in the model metadata.

### Known server configs

| Server | Model | Port | API Key | Startup Script | Setup |
|--------|-------|------|---------|----------------|-------|
| 10.10.70.95 | minimax_m2_7 (MiniMax M2 nvfp4) | 8000 | `***.95-vllm` | `/data/venvs/vllm-ds4/start_minimax_m2_nvfp4_tpep.sh` | TP=8, EP, max_model_len=80920, kv-cache=fp8, compilation mode=3 |

### Pitfalls

- **API keys with asterisks** — some startup scripts may have literal `***` characters in the `--api-key` value due to placeholder substitution. These literal values actually work as the API key. Read the raw file or `/proc/PID/cmdline` to get the exact key.
- **Kill may not work on first try** — vLLM main processes and workers can be stubborn. Use `kill -9` if SIGTERM doesn't work after a few seconds.
- **Model loading is slow** — large models with `--compilation-config` can take several minutes to start. Don't assume failure — poll the process and health endpoint.
- **Use the venv's python** — for HTTP requests on servers without curl, use the vLLM venv's python interpreter to avoid Python version issues: `/data/venvs/vllm-ds4/bin/python3 -c '...'`
- **SSH port forwarding from Hermes** — when checking from the Hermes host, connections to vLLM ports on remote servers may be blocked. Check via SSH to the remote server instead.

## References

Detailed server-specific notes are stored in `references/`:
- `references/70-66-initial-setup.md` — 70.66 (A100 server): CUDA 10.1 system nvcc pitfall, partial CUDA installs, 6×A100 topology, 95% disk usage
- `references/70-88-detailed-setup.md` — 70.88: Primary dev server with proxy, full CUDA/NCCL/nccl-tests/vLLM fork setup
- `references/70-93-performance-quirks.md` — 70.93: Cluster node 1, no proxy, bare-metal initial setup patterns
- `references/70-95-security-config.md` — 70.95: Cluster node 2, proxy via .bashrc, LVM storage, newer kernel
- `references/70-96-storage-resize.md` — 70.96: Cluster node 3, proxy via .bashrc, LVM storage details
- `references/70-98-detailed-setup.md` — 70.98: RTX PRO 6000 Blackwell SE, no proxy, initial setup status

## GPU Architecture Codes

| GPU | Arch | Compute Capability |
|-----|------|-------------------|
| A100 | Ampere | sm_80 |
| RTX 5090 | Blackwell | sm_120 |
| RTX PRO 6000 Blackwell SE | Blackwell | sm_120 |

## Pitfalls

- **Proxy servers need `source ~/.bashrc`** — non-interactive SSH never loads .bashrc; commands will hang without proxy
- **NVIDIA repo auto-redirects** in China to `developer.download.nvidia.cn` (mirror)
- **CUDA 10.1 on 70.66** — system `/usr/bin/nvcc` is ancient; always use `/usr/local/cuda/bin/nvcc`
- **Disk space on 70.66** — 95% full (~260 GB free); install large packages with caution
- **No RDMA on cluster** — CX-6 Dx NICs are not connected for RDMA; 1 Gbps TCP only
- **Do not hardcode passwords** in cron jobs or scripts — prefer SSH key auth for automated tasks
- **`-t` flag required** for PTY-dependent commands (watch, top, interactive sudo)
