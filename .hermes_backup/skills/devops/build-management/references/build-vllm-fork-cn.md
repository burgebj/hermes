# Build vLLM Fork on Remote GPU Server (China Network)

## Scenario

Building a vLLM fork (e.g., `jasl/vllm ds4-sm120` branch) on a remote GPU server in China with network restrictions (GitHub, Docker Hub, PyPI access issues).

## Environment

- Ubuntu 22.04 | RTX 5090 (Blackwell, CC 12.0)
- CUDA Driver: 13.0-13.2 | nvcc: matching version
- NCCL: matching CUDA version

## China Mirror Configuration

| Resource | Mirror URL |
|----------|-----------|
| apt (Ubuntu) | `mirrors.aliyun.com` |
| PyPI | `mirrors.aliyun.com/pypi/simple/` |
| PyTorch CUDA 13.0 | `download.pytorch.org/whl/cu130` |
| GitHub proxy | `ghproxy.net` |
| NVIDIA CUDA | `developer.download.nvidia.cn` |

## Known Pitfalls

1. **CMake ≥ 3.26 required** — Ubuntu 22.04 ships 3.22; use `pip install cmake`
2. **flashinfer wheel** — 2GB download from GitHub Releases; use ghproxy.net
3. **CMake FetchContent** — cloning CUTLASS/Triton from GitHub times out in China; **preserve `.deps/` cache**
4. **Docker layer caching** — RUN layer modifications invalidate full cache; prefer host compilation
5. **Aliyun PyPI SHA256 mismatches** — some packages fail checksum; use Tsinghua mirror or `--no-cache-dir`
6. **Replace apt sources.list** in Dockerfile in a separate RUN layer before apt-get to avoid shell syntax errors

## Recommended Strategy: Host Compilation

Prefer direct venv-based compilation on the host server. Only use Docker when environment isolation is strictly required.
