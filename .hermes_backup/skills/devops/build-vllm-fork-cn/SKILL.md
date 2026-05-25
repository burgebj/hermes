---
name: build-vllm-fork-cn
description: Build vLLM fork on remote GPU server with China network restrictions — aliyun mirrors, Docker vs host compilation, CMake FetchContent pitfalls, NCCL/CUDA compatibility
---

# Build vLLM Fork on Remote GPU Server (China Network)

## 场景

需要在远程 GPU 服务器上构建 vLLM fork 版本（如 `jasl/vllm ds4-sm120` 分支），服务器在中国，存在网络限制（GitHub、Docker Hub、PyPI 访问慢或不可用）。

## 环境

- 服务器：Ubuntu 22.04
- GPU：NVIDIA RTX 5090 (Blackwell, CC 12.0)
- CUDA Driver：13.0
- nvcc：13.0.88
- NCCL：2.28.9-1+cuda13.0

## 策略选择

### 策略 A：Docker 构建（不推荐，在 CN 网络下极易失败）

```bash
# 预先下载 flashinfer wheel 并放入构建上下文
curl -L -o /path/to/vllm-source/flashinfer_jit_cache-0.6.8.post1+cu130-cp39-abi3-manylinux_2_28_x86_64.whl \\
  'https://ghproxy.net/https://github.com/flashinfer-ai/flashinfer/releases/download/v0.6.8.post1/flashinfer_jit_cache-0.6.8.post1+cu130-cp39-abi3-manylinux_2_28_x86_64.whl'

# 简化版 Dockerfile（避免官方 Dockerfile 的复杂度和网络问题）
cat > Dockerfile.custom << 'DOCKER'
FROM vllm/vllm-openai:latest

ARG DEBIAN_FRONTEND=noninteractive
RUN sed -i 's|http://archive.ubuntu.com/ubuntu/|http://mirrors.aliyun.com/ubuntu/|g' /etc/apt/sources.list \\
    && sed -i 's|http://security.ubuntu.com/ubuntu|http://mirrors.aliyun.com/ubuntu|g' /etc/apt/sources.list \\
    && apt-get update -y

RUN apt-get install -y --no-install-recommends g++-10 ninja-build ccache libibverbs-dev \\
    && update-alternatives --install /usr/bin/gcc gcc /usr/bin/gcc-10 110 \\
    && update-alternatives --install /usr/bin/g++ g++ /usr/bin/g++-10 110 \\
    && rm -rf /var/lib/apt/lists/*

RUN python3 -m pip install cmake -i https://mirrors.aliyun.com/pypi/simple/

ENV SETUPTOOLS_SCM_PRETEND_VERSION=0.6.0.dev0
ENV CCACHE_DIR=/root/.cache/ccache

COPY . /workspace/vllm
RUN cd /workspace/vllm \\
    && MAX_JOBS=4 python3 -m pip install -e . \\
        --no-build-isolation \\
        -i https://mirrors.aliyun.com/pypi/simple/
DOCKER

docker build --network=host -f Dockerfile.custom -t vllm-fork:latest .
```

### 策略 B：宿主机直接编译（推荐）

直接在宿主机上创建 venv 编译，避免 Docker 层缓存失效和网络隔离问题。

```bash
# 安装必要的系统包
sudo apt-get install -y --no-install-recommends g++-10 ninja-build ccache libibverbs-dev python3.12 python3.12-dev python3.12-venv

# 设置 CUDA 路径
export PATH=/usr/local/cuda/bin:$PATH
export LD_LIBRARY_PATH=/usr/local/cuda/lib64:$LD_LIBRARY_PATH

# 创建 venv
python3.12 -m venv /path/to/venv
source /path/to/venv/bin/activate
pip install --upgrade pip -i https://mirrors.aliyun.com/pypi/simple/

# 安装 PyTorch CUDA 13.0（匹配宿主机驱动版本）
pip install torch torchvision torchaudio \\
  --index-url https://download.pytorch.org/whl/cu130 \\
  --extra-index-url https://mirrors.aliyun.com/pypi/simple/ \\
  -i https://mirrors.aliyun.com/pypi/simple/

# 安装 cmake >= 3.26（系统 cmake 可能过旧）
pip install cmake ninja wheel packaging setuptools-scm -i https://mirrors.aliyun.com/pypi/simple/

# 安装 vLLM 依赖
cd /path/to/vllm-source
pip install -r requirements/cuda.txt \\
  -i https://mirrors.aliyun.com/pypi/simple/ \\
  --extra-index-url https://download.pytorch.org/whl/cu130

# 设置版本
export SETUPTOOLS_SCM_PRETEND_VERSION=0.6.0.dev0
export CCACHE_DIR=$HOME/.cache/ccache

# 编译 vLLM fork
MAX_JOBS=4 pip install -e . --no-build-isolation \\
  -i https://mirrors.aliyun.com/pypi/simple/

# 验证
python3 -c "import vllm; print('vLLM:', vllm.__version__)"
```

## 国内镜像配置

| 资源 | 镜像地址 |
|------|---------|
| apt (Ubuntu) | `mirrors.aliyun.com` |
| PyPI | `mirrors.aliyun.com/pypi/simple/` |
| PyTorch CUDA 13.0 | `download.pytorch.org/whl/cu130` |
| GitHub 代理 | `ghproxy.net` |
| NVIDIA CUDA | `developer.download.nvidia.cn` |

## 已知坑点

1. **CMake 版本**：vLLM fork 需 CMake ≥ 3.26，Ubuntu 22.04 系统包只有 3.22 → 用 `pip install cmake`
2. **flashinfer**：镜像默认从 GitHub Releases 下载 2GB wheel，在国内极慢 → 通过 ghproxy 预下载
3. **CMake FetchContent**：从 GitHub 克隆 CUTLASS、Triton 等依赖会超时 → 保留 `.deps` 缓存（不要 `rm -rf .deps`）
4. **Docker 缓存**：修改 Dockerfile 会使层缓存失效，每次从头构建 → 优先宿主机编译
5. **CUDA devel 镜像**：官方 `vllm/vllm-openai:latest` 已含 nvcc 和 CUDA 开发库
6. **Dockerfile patching**：在 RUN 层前用单独 `RUN sed` 修改 `sources.list`，不要篡改原 apt-get 行的语法避免 shell 错误

## 验证

```bash
# 检查 vLLM 版本
source /path/to/venv/bin/activate
python3 -c "import vllm; print(vllm.__version__)"

# 检查 GPU 可用性
python3 -c "import torch; print('CUDA:', torch.cuda.is_available(), 'GPUs:', torch.cuda.device_count())"

# 测试启动
vllm serve --model /path/to/model --tensor-parallel-size 8
```
