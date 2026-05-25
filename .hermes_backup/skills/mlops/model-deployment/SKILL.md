---
name: model-deployment
description: ML model deployment workflows — multi-node vLLM server setup, DeepSeek-V4 configuration, tensor parallelism constraints, memory analysis, and distributed inference cluster management.
version: 1.0.0
author: Hermes Agent
license: MIT
---

# Model Deployment

Umbrella skill for deploying ML models to production inference servers. Covers multi-node vLLM setup, model-specific configuration constraints (FP8 block quantization, tensor parallelism sizing), memory analysis, and distributed serving cluster management.

## DeepSeek-V4 Multi-Node Deployment

Reference: `references/deepseek-v4-multi-node.md` for detailed DeepSeek-V4-Pro setup across 4 GPU servers.

### Critical: FP8 Block Quantization Constraint

DeepSeek-V4-Pro uses FP8 weight quantization with `weight_block_size: [128, 128]`. Every TP-split dimension must be divisible by 128 (block_k).

Key dimensions:
- `moe_intermediate_size`: 3072
- `hidden_size`: 7168
- `q_lora_rank`: 1536

Working TP configs:
- **TP=4**: 3072/4=768 ✅, 7168/4=1792 ✅, 1536/4=384 ✅
- **TP=2**: All pass
- **TP=1**: No FP8 split needed
- **TP=8+**: **BLOCKED** — q_lora_rank 1536/8=192, 192%128=64 ❌

### DP+EP Architecture (4 nodes × 8 GPUs)

Since TP > 4 is blocked, use: **TP=4, DP=4, EP enabled** to utilize all 32 GPUs.

```bash
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
```

### Memory Budget (RTX 5090 32GB)
- Non-expert weights: ~19 GB/GPU
- Expert weights (FP4): ~12 GB/GPU
- Total: ~31 GB — tight fit on 32 GB

### Network Config (1 Gbps TCP, no RDMA)
```bash
export GLOO_SOCKET_IFNAME=ens20f0
export TP_SOCKET_IFNAME=ens20f0
export NCCL_SOCKET_IFNAME=ens20f0
export NCCL_IB_DISABLE=1
```

## General Model Serving Principles

1. **Tensor parallelism scaling** — limited by smallest divisible dimension and inter-node bandwidth
2. **Pipeline parallelism** — better for multi-node when TP hits constraints
3. **Expert parallelism (EP)** — essential for Mixture-of-Experts models across many GPUs
4. **Data parallelism (DP)** — use when TP/PP saturated, for throughput scaling

## Pitfalls

- **FP8 block_k constraints** dominate TP sizing — check model config `weight_block_size` before choosing TP
- **CUDA OOM** with FP4 experts on 32 GB cards — reduce `--gpu-memory-utilization` to 0.85
- **DP coordinator address** — `--data-parallel-address` must be set on the head node to avoid TCPStore connection failures
- **hostname resolution** — if hostname resolves to 127.0.1.1, explicitly set `NCCL_SOCKET_IFNAME`
- **1 Gbps TCP is slow** for model weight broadcast during DP — expect longer startup times
