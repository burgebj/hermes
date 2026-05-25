# NCCL Bandwidth Benchmark Report

**Date:** 2025-04-29 17:09-17:15
**Host:** 10.10.70.88 (oem88)
**GPU:** 8× NVIDIA GeForce RTX 5090 (Blackwell, CC 12.0)
**GPU Interconnect:** PCIe 5.0 x16
**Driver:** 580.126.09 | **CUDA Driver:** 13.0
**nvcc:** 13.0.88 | **NCCL:** 2.28.9-1+cuda13.0
**nccl-tests:** v2.18.3 (headers=22809, library=22809)

---

## 1. AllReduce — 2 Cards (Rank 0-1)

| Data Size | AlgoBW (GB/s) | BusBW (GB/s) | Latency (us) |
|-----------|:-----------:|:-----------:|:----------:|
| 8 B | 0.00 | 0.00 | 7.84 |
| 1 KB | 0.13 | 0.13 | 7.95 |
| 16 KB | 2.06 | 2.06 | 7.97 |
| 256 KB | 10.88 | 10.88 | 24.10 |
| 1 MB | 18.95 | 18.95 | 55.33 |
| 8 MB | 29.65 | 29.65 | 282.92 |
| 64 MB | 31.67 | 31.67 | 2119.13 |
| 512 MB | 33.06 | 33.06 | 16240.9 |
| **8 GB** | **35.36** | **35.36** | **242925** |

**Avg Bus Bandwidth:** 15.34 GB/s
**Peak Bus Bandwidth:** 35.36 GB/s (at 8 GB)

> Latency floor: ~7.8 us (min 8 B). Scales near-perfectly with PCIe 5.0 x16 unidirectional limit (~31.5 GB/s).

---

## 2. AllReduce — 8 Cards (Rank 0-7)

| Data Size | AlgoBW (GB/s) | BusBW (GB/s) | Latency (us) |
|-----------|:-----------:|:-----------:|:----------:|
| 8 B | 0.00 | 0.00 | 31.76 |
| 1 KB | 0.03 | 0.06 | 32.04 |
| 16 KB | 0.50 | 0.87 | 32.79 |
| 256 KB | 5.86 | 10.25 | 44.77 |
| 1 MB | 7.46 | 13.06 | 140.48 |
| 8 MB | 19.25 | 33.68 | 435.84 |
| 64 MB | 22.32 | 39.07 | 3006.17 |
| 512 MB | 22.69 | 39.71 | 23658.6 |
| 4 GB | 23.17 | 40.56 | 185330 |
| **8 GB** | **23.26** | **40.70** | **369379** |

**Avg Bus Bandwidth:** 16.95 GB/s
**Peak Bus Bandwidth:** 40.70 GB/s (at 8 GB)

> Latency floor: ~31.8 us (8 B). Ring algorithm overhead gives 4× latency vs 2-card.

---

## 3. Full 8-Card Collective Summary

| Operation | Peak AlgoBW (GB/s) | Peak BusBW (GB/s) | Avg BusBW (GB/s) | Latency @ 8B (us) |
|-----------|:----------------:|:----------------:|:---------------:|:----------------:|
| **all_reduce** | 23.26 | 40.70 | 16.95 | 31.8 |
| **all_gather** | 45.42 | 39.74 | 15.75 | 40.7 |
| **broadcast** | 41.25 | 41.25 | 17.61 | 30.5 |
| **reduce_scatter** | 43.57 | 38.12 | 15.43 | 40.5 |
| **alltoall** | 31.52 | 27.58 | 8.81 | 54.8 |
| **sendrecv** | 25.82 | 25.82 | 10.54 | 42.6 |

---

## 4. Small Message Latency (8 B, critical for communication-bound workloads)

| Operation | Latency (us) |
|-----------|:----------:|
| broadcast | 30.5 |
| all_reduce | 31.8 |
| reduce_scatter | 40.5 |
| all_gather | 40.7 |
| sendrecv | 42.6 |
| alltoall | 54.8 |

---

## 5. Key Findings

1. **Peak Bus Bandwidth 40.70 GB/s** — Consistent with PCIe 5.0 x16 theoretical peak (63 GB/s bidirectional / ~31.5 GB/s unidirectional), with ring algorithm overhead accounting for the 2x factor in BusBW vs AlgoBW.

2. **all_reduce scales well:** 2-card peak = 35.36 GB/s, 8-card peak = 40.70 GB/s (+15%). The 8-card ring topology achieves higher effective bandwidth by utilizing more links simultaneously.

3. **all_gather/reduce_scatter efficiency:** Peak ~39-41 GB/s indicate strong ring-pipeline utilization. Broadcast is the most efficient single-source operation (41.25 GB/s).

4. **alltoall bottleneck:** Only 27.58 GB/s peak — all-to-all is inherently bandwidth-limited on PCIe topology (no dedicated NVSwitch). This is expected for PCIe-only interconnects.

5. **sendrecv moderate:** ~25.8 GB/s — peer-to-peer bandwidth between non-adjacent GPUs is limited by PCIe switch topology.

6. **Latency floor:** ~30-55 us for small messages — dominated by PCIe traversal and host-side synchronization overhead.

---

## 6. Comparison: 2 GPUs vs 8 GPUs

| Metric | 2 GPUs | 8 GPUs | Delta |
|--------|:------:|:------:|:-----:|
| all_reduce peak AlgoBW | 35.36 GB/s | 23.26 GB/s | -34% |
| all_reduce peak BusBW | 35.36 GB/s | 40.70 GB/s | +15% |
| all_reduce avg BusBW | 15.34 GB/s | 16.95 GB/s | +11% |
| all_reduce min latency | 7.84 us | 31.76 us | +305% |

> **Note:** AlgoBW drops from 35→23 GB/s going 2→8 GPUs because the ring topology must move more data per GPU (each GPU sends/receives (N-1)/N of the total data). BusBW correctly reflects the aggregate interconnect utilization.

---

## 7. Environment Verification

```
GPU Model       : NVIDIA GeForce RTX 5090
Driver Version  : 580.126.09
CUDA Version    : 13.0
nvcc Version    : 13.0.88
NCCL Library    : 2.28.9-1+cuda13.0
nccl-tests      : v2.18.3
Python / PyTorch: not installed
```

---

*Report generated from live NCCL bandwidth tests on 10.10.70.88.*
