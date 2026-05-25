# 10.10.70.95 (oem95) — Security Config

**GPU:** 8× NVIDIA RTX 5090 (Blackwell, CC 12.0, 32GB)
**Driver:** 595.58.03 | **CUDA Driver:** 13.2
**System:** Ubuntu 22.04.1 LTS | **Kernel:** 6.8.0-111-generic (newer! vs 93/96 5.15)
**Storage:** LVM (`/dev/mapper/vgubuntu-root`)

## Key Differences from 70.93

- **Has proxy** (`http://10.10.60.140:7890` in ~/.bashrc — same as 70.88)
- **Newer kernel** (6.8.0) — better Mellanox/RDMA support
- **LVM storage** — easier expansion

## SSH (proxy required)

```
ssh jianliu@10.10.70.95 "source ~/.bashrc && command"
```

Same proxy pattern as 70.88 — always source .bashrc.

## vLLM Environment

- Source: `/data/vllm-ds4-sm120/`
- Venv: `/data/venvs/vllm-ds4/` (Python 3.12, PyTorch 2.11.0+cu130)
- CUDA dev packages installed (nvrtc, cublas, cusparse, cusolver)
