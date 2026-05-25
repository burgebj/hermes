---
name: build-management
description: Build and compile workflows for GPU-accelerated projects — vLLM fork building, CMake configuration, CUDA compilation, and handling China network restrictions for build dependencies.
version: 1.0.0
author: Hermes Agent
license: MIT
---

# Build Management

Umbrella skill for build and compilation tasks, especially CUDA-accelerated projects like vLLM forks on remote GPU servers. Covers build strategies, mirror configuration, CMake pitfalls, and dependency management under network constraints.

## Build Strategy Selection

### Option A: Host (Bare Metal) Compilation — RECOMMENDED
Direct venv-based compilation on the server. Faster iteration, no Docker layer caching issues.

```bash
# Prerequisites
sudo apt-get install -y --no-install-recommends g++-10 ninja-build ccache libibverbs-dev python3.12 python3.12-dev python3.12-venv
export PATH=/usr/local/cuda/bin:$PATH
export LD_LIBRARY_PATH=/usr/local/cuda/lib64:$LD_LIBRARY_PATH

# Venv setup
python3.12 -m venv /path/to/venv
source /path/to/venv/bin/activate
pip install --upgrade pip

# PyTorch (match CUDA version)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu130

# Build tools
pip install cmake ninja wheel packaging setuptools-scm

# Build
export SETUPTOOLS_SCM_PRETEND_VERSION=0.6.0.dev0
MAX_JOBS=4 pip install -e . --no-build-isolation
```

### Option B: Docker Build — Use when isolation needed
Use for clean-room builds or reproducible environments. Higher risk of network issues in China.

## China Network Configuration

### Mirrors
| Resource | Mirror URL |
|----------|-----------|
| Ubuntu apt | `mirrors.aliyun.com` |
| PyPI | `mirrors.aliyun.com/pypi/simple/` or `pypi.tuna.tsinghua.edu.cn/simple/` |
| PyTorch CUDA 13.0 | `download.pytorch.org/whl/cu130` |
| GitHub proxy | `ghproxy.net` |
| NVIDIA CUDA | `developer.download.nvidia.cn` |

### Known Issues with Aliyun Mirror
- Some NVIDIA packages on Aliyun have SHA256 checksum mismatches
- **Fix:** Use Tsinghua mirror (`pypi.tuna.tsinghua.edu.cn`) or skip mirror with `--no-cache-dir`
- For PyTorch: use download.pytorch.org as primary index + Aliyun/Tsinghua as extra-index

## CMake Pitfalls

- **CMake version:** vLLM fork requires CMake ≥ 3.26; Ubuntu 22.04 ships 3.22 → use `pip install cmake`
- **CMake FetchContent** clones from GitHub (CUTLASS, Triton) — can timeout in China. **Preserve `.deps/` cache** — do not `rm -rf .deps`
- When `cmake` hangs or fails on FetchContent, check network/proxy first

## vLLM Fork Build (jasl/vllm ds4-sm120)

For the DeepSeek V4 fork at `github.com/jasl/vllm/tree/ds4-sm120`:

### Required CUDA dev packages (beyond cuda-nvcc)
```bash
sudo apt-get install -y cuda-nvrtc-dev-13-2 libcusparse-dev-13-2 libcusolver-dev-13-2 libcublas-dev-13-2
```

### Build command
```bash
export MAX_JOBS=4 SETUPTOOLS_SCM_PRETEND_VERSION=0.6.0.dev0
cd /path/to/vllm-source
pip install -e . --no-build-isolation --no-cache-dir
```

### Verification
```bash
python -c "import vllm; print(vllm.__version__)"  # Should print 0.6.0.dev0
```

## Pitfalls

- **Failing to `source ~/.bashrc`** on proxy servers → builds hang on GitHub/PyPI access
- **`--no-cache-dir`** important when mirror SHA256 issues are suspected
- **Docker layer caching** — modifying Dockerfile RUN layers invalidates cache; prefer host compilation for iteration
- **flashinfer** ~2GB wheel downloaded from GitHub Releases — use ghproxy.net proxy for China
- **CUDA dev packages** — minimal nvcc install does NOT include nvrtc, cusparse, cusolver, cublas dev headers; install separately
