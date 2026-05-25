# 10.10.70.93 (oem93) — Performance & Quirks

**GPU:** 8× NVIDIA RTX 5090 (Blackwell, CC 12.0, 32GB)
**Driver:** 595.58.03 | **CUDA Driver:** 13.2 | **CUDA Toolkit:** cuda-nvcc-13.2.78
**System:** Ubuntu 22.04.1 LTS | **Kernel:** 5.15.0-43-generic
**NIC:** 2× Mellanox ConnectX-6 Dx (MT2892) — RoCE/RDMA capable

## Key Differences from 70.88

- **No proxy** — direct internet access
- **Bare metal** — all toolchain installed from scratch
- **CUDA 13.2** (vs 70.88's 13.0)
- **Mellanox ConnectX-6 Dx** NICs for multi-node

## Performance Notes

- 8 GPUs across 2 NUMA nodes (4 GPU/node)
- Same NUMA: NODE interconnect (best)
- Cross NUMA: SYS (worst — QPI/UPI)
- NIC on NUMA 1 (GPU4-7) — PIX connection to NIC is lowest latency

## vLLM Environment

- Source: `/data/vllm-ds4-sm120/`
- Venv: `/data/venvs/vllm-ds4/` (Python 3.12, PyTorch 2.11.0+cu130)
- Built from source with CMake 4.3.2
