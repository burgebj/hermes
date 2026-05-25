# DeepSeek-V4 Multi-Node Setup

Configuring a multi-node vLLM server for DeepSeek-V4-Pro across 4 GPU servers (70.88, 70.93, 70.95, 70.96, each with 8×RTX 5090 32GB).

## FP8 Block Quantization Constraint

DeepSeek-V4-Pro uses FP8 weight quantization with `weight_block_size: [128, 128]`. Every TP-split dimension must be divisible by 128 (block_k).

**Working: TP=4** (3072/4=768 ✅, 7168/4=1792 ✅, 1536/4=384 ✅)
**Blocked: TP=8+** (q_lora_rank 1536/8=192, 192%128=64 ❌)

## DP+EP Architecture (only way to use 4 nodes × 8 GPUs)

Since TP > 4 is blocked, use: **TP=4, DP=4, EP enabled** to use all 32 GPUs.

## Server Nodes

| IP | Hostname | Role | DP Rank |
|----|----------|------|---------|
| 10.10.70.88 | oem88 | Head | 0 |
| 10.10.70.93 | oem93 | Worker | 1 |
| 10.10.70.95 | oem95 | Worker | 2 |
| 10.10.70.96 | oem96 | Worker | 3 |

Model: `/data/models/deepseekv4_pro/` (806 GB)
Script: `/data/venvs/vllm-ds4/start_dsv4_4node.sh`

## Memory Budget per GPU

- Non-expert weights: ~19 GB
- Expert weights (FP4): ~12 GB
- Total: ~31 GB — tight on 32 GB

## Network (1 Gbps TCP, no RDMA)

```bash
export GLOO_SOCKET_IFNAME=ens20f0
export TP_SOCKET_IFNAME=ens20f0
export NCCL_SOCKET_IFNAME=ens20f0
export NCCL_IB_DISABLE=1
```

## Known Failures

| Config | Failure | Root Cause |
|--------|---------|------------|
| TP=32, 4 nodes | FP8 block_k=128 | 3072/32=96 ❌ |
| TP=16, 2 nodes | FP8 block_k=128 | 3072/16=192 ❌ |
| TP=8 + DP=4 + EP | CUDA OOM | Non-expert + expert weights fill 32 GB |
| DP+EP worker disconnect | TCPStore connection to 127.0.0.1 | `--data-parallel-address` missing on head node |

## OOM Mitigation

```bash
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
# Lower --gpu-memory-utilization from 0.95 to 0.85
```
