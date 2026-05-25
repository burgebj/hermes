---
name: install-nvcc-minimal
description: Install only the CUDA compiler (nvcc) from NVIDIA's official apt repo — no full toolkit download. Covers version selection based on GPU architecture and driver.
version: 1.0.0
author: Hermes Agent
tags: [cuda, nvcc, gpu, blackwell, nvidia, compiler]
---

# Install nvcc (minimal CUDA compiler)

Install just the CUDA compiler (`nvcc`) without pulling in the full multi-GB CUDA toolkit.

## When to use

- Someone asks to install "only nvcc" or "just the CUDA compiler"
- Building C/C++ CUDA projects (PyTorch from source, llama.cpp with CUDA, Flash Attention, vLLM, etc.) and wants to avoid the full toolkit
- A remote/headless GPU machine needs compilation capability but not profiling/visualization libraries
- Installing on a machine with limited bandwidth or disk space
- The user complains `apt-get install nvidia-cuda-toolkit` is too slow (63 MB download, 123 MB installed — but it pulls unnecessary bloat too via the dep chain)
- Fixing **version mismatches** between packages from NVIDIA's repo (e.g., NCCL, cuBLAS libraries) and the driver's CUDA version — when `ldconfig -p | grep nccl` or `nm -D /usr/lib/libnccl.so | grep ncclGetVersion` shows a version linked against a newer CUDA than the driver supports

## Prerequisites

- Ubuntu (check with `cat /etc/os-release`)
- x86_64 or aarch64 (`uname -m`)
- Root/sudo access
- NVIDIA driver already installed (check with `nvidia-smi`)

## Determine the right CUDA version

### 1. Check GPU architecture and driver

```bash
nvidia-smi --query-gpu=name,driver_version --format=csv,noheader
nvidia-smi -q | grep -i cuda   # shows driver-supported CUDA version
```

### 2. Version compatibility rules

| GPU Architecture | Compute Capability | Minimum CUDA |
|---|---|---|
| Blackwell (RTX 5090 / 5080) | 12.0 | **12.8+** |
| Lovelace (RTX 4090 / 4080) | 8.9 | **11.8+** |
| Ada / Hopper (H100) | 9.0 | **11.8+** |
| Ampere (RTX 3090 / A100) | 8.x | **11.0+** |
| Turing (RTX 2080) | 7.5 | **10.0+** |
| Volta (V100) | 7.0 | **9.0+** |

**Key pitfall:** Blackwell (RTX 5090) requires **CUDA 12.8 minimum** — 12.6 won't work.

### 3. Choose the version

Pick the **latest stable** CUDA version that:
- Is ≥ the minimum required for your GPU architecture
- Is ≤ the driver's reported CUDA Version (from `nvidia-smi -q | grep CUDA`)

The safest choice is the `cuda-nvcc-X-Y` that matches the driver-reported CUDA version.

## Installation

### 1. Add NVIDIA's official apt repo (one-time)

```bash
# Determine Ubuntu codename
. /etc/os-release && echo $VERSION_CODENAME

# Download and install the keyring package
wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2204/x86_64/cuda-keyring_1.1-1_all.deb
sudo dpkg -i cuda-keyring_1.1-1_all.deb
sudo apt-get update
```

**URL format:**
- Ubuntu: `https://developer.download.nvidia.com/compute/cuda/repos/ubuntu<NUM>/x86_64/`
- Replace `<NUM>` with `2204` for 22.04, `2404` for 24.04, etc.
- Replace `x86_64` with `sbsa` for ARM (e.g., NVIDIA Grace Hopper)

### 2. Find available nvcc packages

```bash
apt-cache search cuda-nvcc- | sort
```

This lists packages like `cuda-nvcc-12-8`, `cuda-nvcc-13-0`, `cuda-nvcc-13-1`, etc.

### 3. Install just nvcc (small, ~30-60 MB)

```bash
sudo apt-get install -y cuda-nvcc-13-0
```

Replace `13-0` with your chosen version.

### 4. Verify

```bash
/usr/local/cuda-*/bin/nvcc --version
# Add to PATH if needed:
export PATH=/usr/local/cuda-13.0/bin:$PATH
```

## Optional: add to PATH permanently

```bash
# Add to ~/.bashrc or ~/.profile
# (auto-detect the installed version)
echo 'export PATH=/usr/local/cuda-$(ls /usr/local/ | grep "^cuda-[0-9]" | sort -V | tail -1)/bin:$PATH' >> ~/.bashrc
```

## What you get vs what you avoid

| Component | `nvidia-cuda-toolkit` | `cuda-nvcc-13-0` (this method) |
|---|---|---|
| nvcc (compiler) | ✅ | ✅ |
| cuBLAS / cuFFT / cuRAND / cuSOLVER / cuSPARSE / NPP | ✅ | ❌ |
| CUDA profiler | ✅ | ❌ |
| OpenCL dev files | ✅ | ❌ |
| Download size | ~63 MB (but pulls more deps) | ~30-60 MB (compiler only) |

If you also need cuBLAS etc., install `cuda-libraries-dev-13-0` as well.

## Pitfalls

- **Wrong repo / old cuda-keyring**: If the keyring version is too old, newer CUDA versions won't appear in the repo. Get the latest from `https://developer.download.nvidia.com/compute/cuda/repos/`.
- **Mixed versions**: Don't install `cuda-nvcc-13-0` + `cuda-libraries-dev-12-8` — they'll conflict. Use one CUDA major version consistently.
- **apt-file not available**: If you need to find which package owns a specific binary, install `apt-file` first.
- **Driver too old for CUDA**: nvcc may still compile code the driver can't run. Always check the driver's CUDA version first (see step 1 above).
- **NCCL version mismatch**: The NVIDIA repo serves NCCL (libnccl2/libnccl-dev) compiled against multiple CUDA versions (e.g., `2.30.4-1+cuda13.2` and `2.28.9-1+cuda13.0`). Running `apt-get install libnccl2` will pull the **latest NCCL package**, which may be compiled against a newer CUDA than your driver supports, causing silent runtime failures.
  
  **Fix:** Check which CUDA-versioned NCCL builds are available, then downgrade:
  ```bash
  apt-cache policy libnccl2  # shows all available builds
  sudo apt-get install -y --allow-downgrades libnccl2=2.28.9-1+cuda13.0 libnccl-dev=2.28.9-1+cuda13.0
  ```
  
  **Verify:**
  ```bash
  awk '/NCCL_MAJOR|NCCL_MINOR|NCCL_PATCH/{print}' /usr/include/nccl.h
  nm -D /usr/lib/x86_64-linux-gnu/libnccl.so | grep ' ncclGetVersion'
  ```
  
  The same pattern applies to any `cuda-*-dev` or `libcuda*` packages — always match the `+cudaX.Y` suffix to the driver's CUDA version, not the latest available.
