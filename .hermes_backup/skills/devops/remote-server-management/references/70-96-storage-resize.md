# 10.10.70.96 (oem96) — Storage & Resize

**GPU:** 8× NVIDIA RTX 5090 (Blackwell, CC 12.0, 32GB)
**Driver:** 595.58.03 | **CUDA Driver:** 13.2
**System:** Ubuntu 22.04.1 LTS | **Kernel:** 5.15.0-43-generic (same as 93)
**Storage:** LVM (`/dev/mapper/vgubuntu-root`) — 1.7T, 1% used

## Key Differences from 70.93

- **Has proxy** (`http://10.10.60.140:7890` in ~/.bashrc — same as 70.88/95)
- **LVM storage** (unlike 93's direct partition)
- **Kernel 5.15** (same as 93, unlike 95's 6.8)

## SSH (proxy required)

```
ssh jianliu@10.10.70.96 "source ~/.bashrc && command"
```

## vLLM Environment

- Source: `/data/vllm-ds4-sm120/`
- Venv: `/data/venvs/vllm-ds4/` (Python 3.12, PyTorch 2.11.0+cu130)
- CUDA dev packages installed

## Batch Operations

Part of 93/95/96 cluster — use `for h in 93 95 96; do ... done` for bulk commands.
