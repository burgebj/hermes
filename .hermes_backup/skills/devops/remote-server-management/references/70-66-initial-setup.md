# 10.10.70.66 — Initial Setup & Environment

**GPU:** 6× NVIDIA A100-PCIE-40GB (Ampere, CC 8.0)
**Driver:** 535.216.01 | **CUDA Driver:** 12.2 | **CUDA Toolkit:** 12.3.107
**System:** Ubuntu 20.04.6 LTS (Focal Fossa) | **Kernel:** 5.15.0-119-generic
**Disk:** 5.2T (95% used, ~260G free)

## Critical: System nvcc is CUDA 10.1

System `/usr/bin/nvcc` is CUDA 10.1.243 — too old for A100 (CC 8.0).
**Always use** `/usr/local/cuda/bin/nvcc` (CUDA 12.3).

## GPU Topology

- 2 NUMA nodes, 3 GPUs each
- GPU0↔GPU1: PIX (same PCIe switch)
- GPU1↔GPU2, GPU4↔GPU5: NV12 (NVLink)
- Cross-NUMA: SYS (highest latency)
- PCIe Gen 4 ×16

## NCCL

Not installed initially. Install via NVIDIA repo (Ubuntu 20.04 focal):
```
apt-cache madison libnccl2
sudo apt-get install -y libnccl2 libnccl-dev
```

## SSH

- No proxy needed (direct internet)
- sudo password same as 70.88
