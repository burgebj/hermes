# 10.10.70.88 — Primary Dev Server Detailed Setup

**GPU:** 8× NVIDIA RTX 5090 (Blackwell, CC 12.0, 32GB)
**Driver:** 580.126.09 | **CUDA Driver:** 13.0 | **CUDA Toolkit:** 13.0.88 (nvcc only)
**System:** Ubuntu 22.04 LTS | **Kernel:** (default)

## Key Environment

- **Proxy:** `http://10.10.60.140:7890` (in ~/.bashrc)
- **NCCL:** 2.28.9-1+cuda13.0
- **vLLM fork:** `/data/vllm-ds4-sm120/` (jasl/vllm ds4-sm120, v0.6.0.dev0)
- **venv:** `/data/venvs/vllm-ds4/` (Python 3.12, PyTorch 2.11.0+cu130)
- **Model path:** `/home/jianliu/work/models/deepseekv4_flash/`
- **Work directory:** `~/work/bandwidth_test/`

## SSH (proxy required)

```
ssh -t jianliu@10.10.70.88 "source ~/.bashrc && command"
```

Non-interactive SSH does NOT load .bashrc — always source it first.

## nccl-tests

Compiled at `~/work/bandwidth_test/nccl-tests/build/`.
Makefile auto-detects CUDA and sm_120 support.

## Reference 8-card bandwidth

| Operation | Large Data (>128MB) |
|-----------|---------------------|
| all_reduce | 22-23 GB/s (Algo) / 39-40 GB/s (Bus) |

## Docker image available

`vllm/vllm-openai:latest` can be used for quick deployment without source compilation.
