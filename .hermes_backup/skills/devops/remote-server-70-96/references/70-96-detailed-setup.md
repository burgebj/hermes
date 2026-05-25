# 10.10.70.96 (oem96) — Detailed Setup

**GPU:** 8× NVIDIA RTX 5090 (Blackwell, CC 12.0, 32GB each)
**Driver:** 595.58.03 | **CUDA Driver:** 13.2
**System:** Ubuntu 22.04.1 LTS | **Kernel:** 5.15.0-43-generic
**Storage:** LVM — `/dev/mapper/vgubuntu-root` (1.7 TB), `/data` LVM volume

## Access Credentials

| Field | Value |
|-------|-------|
| Username | jianliu |
| IP | 10.10.70.96 |
| Password | !QAZ2wsx |
| Sudo Password | !QAZ2wsx |

SSH key authentication is configured. Password-based auth also works.

## Network

- **Proxy:** `http://10.10.60.140:7890` (configured in `~/.bashrc`)
- **Mellanox ConnectX-6 Dx NICs** (ens20f0)
- Part of 10.10.70.x subnet

## vLLM Environment

- Source code: `/data/vllm-ds4-sm120/`
- Python venv: `/data/venvs/vllm-ds4/`
- Python: 3.12
- PyTorch: 2.11.0+cu130
- vLLM fork: jasl/vllm ds4-sm120 branch

## /etc/hosts Gloo Bug

The file `/etc/hosts` contains:
```
127.0.1.1 oem96
```

This causes Gloo TCPStore to bind to `127.0.1.1` instead of the actual interface IP when `CompilationMode.VLLM_COMPILE` is active. The fix is always setting:

```bash
export MASTER_ADDR=10.10.70.96
export VLLM_HOST_IP=10.10.70.96
```

## Key Differences from Other 10.10.70.x Servers

- **Has proxy** — unlike 70.93, 70.98; same as 70.88, 70.95
- **LVM storage** — unlike 70.93's direct partition
- **Kernel 5.15** — same as 70.93, unlike 70.95's 6.8
- **RTX 5090** (32 GB) — unlike 70.98's RTX PRO 6000 (96 GB)
- **Master node role** — runs API server on port 8000
