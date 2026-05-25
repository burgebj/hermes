---
name: remote-70-93
description: 远程操作 GPU 服务器 (10.10.70.93 / oem93) — SSH 连接、CUDA Toolkit 安装、NCCL 管理、8×RTX 5090 环境搭建
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [ssh, gpu, cuda, nccl, nvcc, bandwidth-test, remote, devops, rtx5090, blackwell]
    related_skills: [remote-70-95, remote-70-96, remote-70-88]
---

# Remote GPU Server (10.10.70.93 / oem93)

远程操作 GPU 服务器 10.10.70.93 (oem93) 的常用工作流。与 10.10.70.95 (oem95) 和 10.10.70.96 (oem96) 完全相同的硬件配置，
三台服务器构成一个 GPU 集群，通过 Mellanox ConnectX-6 Dx NIC 互联。

> **与 70.88 的关键区别：** 70.93 是全新裸机（无 proxy、无 CUDA Toolkit、无 NCCL、无 Docker）。
> 所有工具链需要从零安装。有 Mellanox ConnectX-6 Dx 网卡，支持 RDMA/RoCE 多机通信。

## 环境信息

| 项目 | 值 |
|------|-----|
| 主机名 | oem93 |
| IP | 10.10.70.93 |
| 用户 | jianliu |
| 系统 | Ubuntu 22.04.1 LTS (Jammy) |
| 内核 | 5.15.0-43-generic |
| CPU | 128× Intel Xeon (2 NUMA 节点: 0-31,64-95 / 32-63,96-127) |
| 内存 | 1.0 TiB |
| 磁盘 | 1.7T (使用 1%) — 充足 |
| GPU | 8× NVIDIA RTX 5090 (Blackwell, CC 12.0, 32GB/卡, PCIe Gen4×16) |
| 驱动 | 595.58.03 |
| CUDA Driver | 13.2 |
| CUDA Toolkit | cuda-nvcc-13.2.78 (仅 nvcc，非完整 toolkit) |
| NCCL | 未安装（系统） |
| Python | 3.10.12 (系统) + 3.12.13 (deadsnakes PPA) |
| PyTorch | 2.11.0+cu130 (venv: /data/venvs/vllm-ds4/) |
| vLLM | 0.6.0.dev0 (jasl/ds4-sm120 fork, 源码: /data/vllm-ds4-sm120/) |
| NIC | 2× Mellanox ConnectX-6 Dx (MT2892) — 支持 RoCE / RDMA |
| 代理 | 无 (直连互联网，与 70.88 不同) |
| sudo | 需要密码（同 70.88） |

### GPU 拓扑

8 张 GPU 分布在 2 个 NUMA 节点：

```
NUMA 0 (CPU 0-31, 64-95): GPU0, GPU1, GPU2, GPU3  (NODE 互连)
NUMA 1 (CPU 32-63, 96-127): GPU4, GPU5, GPU6, GPU7  (NODE 互连)

同 NUMA 内: NODE — PCIe Host Bridge 内部通信（优于 SYS）
跨 NUMA:    SYS — 经 QPI/UPI 互联（延迟最高）
NIC: GPU4-7 所在 NUMA 的 NIC 为 PIX（低延迟）
```

## SSH 连接

```bash
# 首次连接接受 host key（已自动添加）
ssh -o StrictHostKeyChecking=accept-new jianliu@10.10.70.93 "echo connected"

# 交互式登录
ssh -t jianliu@10.10.70.93

# 执行命令并返回
ssh jianliu@10.10.70.93 "command"

# 需要 sudo 时通过管道传密码
ssh jianliu@10.10.70.93 "echo 'PASSWORD' | sudo -S apt-get install -y PACKAGE"
```

**注意:**
- 70.93 **没有代理**，直连互联网，无需 `source ~/.bashrc`
- sudo 密码同 70.88 服务器。`!` 在 bash 中有特殊含义，需要用单引号包裹：`echo '!QAZ2wsx' | sudo -S ...`
- `-t` 参数仅在需要 PTY 时使用（watch、top、交互式 sudo）

## CUDA Toolkit 安装

RTX 5090 (Blackwell, CC 12.0) 需要 **CUDA 12.8+**。驱动 595.58.03 支持 CUDA 13.2。

### 安装 nvcc（推荐细粒度安装，~87 MB）

```bash
# 添加 NVIDIA 仓库（仅首次）
ssh jianliu@10.10.70.93 "echo 'PASSWORD' | sudo -S bash -c '
  cd /tmp
  wget -q https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2204/x86_64/cuda-keyring_1.1-1_all.deb
  dpkg -i cuda-keyring_1.1-1_all.deb
  apt-get update
'"

# 安装 nvcc（选择与驱动匹配的版本：驱动 13.2 → cuda-nvcc-13-2）
ssh jianliu@10.10.70.93 "echo 'PASSWORD' | sudo -S apt-get install -y cuda-nvcc-13-2"

# 自动安装依赖：cuda-cudart-13-2, cuda-cccl-13-2, cuda-crt-13-2
# 自动设置 /usr/local/cuda -> /usr/local/cuda-13.2
```

**可用 nvcc 版本（Ubuntu 22.04 NVIDIA 仓库）:**

| 包名 | CUDA 版本 | Blackwell 支持 |
|------|-----------|---------------|
| `cuda-nvcc-12-8` | 12.8 | ✓ (最低要求) |
| `cuda-nvcc-13-0` | 13.0 | ✓ |
| `cuda-nvcc-13-1` | 13.1 | ✓ |
| `cuda-nvcc-13-2` | 13.2 | ✓ (当前推荐) |

### 将 CUDA 加入 PATH

```bash
ssh jianliu@10.10.70.93 "echo 'PASSWORD' | sudo -S tee -a /etc/profile.d/cuda.sh > /dev/null << 'EOF'
export PATH=/usr/local/cuda/bin:\$PATH
export LD_LIBRARY_PATH=/usr/local/cuda/lib64:\$LD_LIBRARY_PATH
EOF
sudo chmod +x /etc/profile.d/cuda.sh"

# 验证
ssh jianliu@10.10.70.93 "bash -l -c 'nvcc --version'"
```

### 可选：安装完整 CUDA Toolkit（如有需要）

完整 toolkit 约 3.2 GB，99% 的功能 nvcc + cudart 已覆盖，仅在需要 CUDA 样本/工具时安装：
```bash
ssh jianliu@10.10.70.93 "source ~/.bashrc && echo 'PASSWORD' | sudo -S apt-get install -y cuda-toolkit-13-2"
```

## NCCL 安装

### 安装 libnccl2 + libnccl-dev

```bash
# 查看可用 NCCL 版本
ssh jianliu@10.10.70.93 "source ~/.bashrc && apt-cache madison libnccl2"

# 安装与 CUDA 13.2 匹配的最新 NCCL
ssh jianliu@10.10.70.93 "source ~/.bashrc && echo 'PASSWORD' | sudo -S apt-get install -y libnccl2 libnccl-dev"

# 验证安装
ssh jianliu@10.10.70.93 "source ~/.bashrc && awk '/NCCL_MAJOR|NCCL_MINOR|NCCL_PATCH/{print \$3}' /usr/include/nccl.h | tr '\n' '.'"
```

### 验证 NCCL 编译

```bash
cat > /tmp/test_nccl.cu << 'EOF'
#include <nccl.h>
#include <stdio.h>
int main() {
  printf("NCCL compiled OK (version code: %d)\n", NCCL_VERSION_CODE);
  return 0;
}
EOF
scp /tmp/test_nccl.cu jianliu@10.10.70.93:/tmp/
ssh jianliu@10.10.70.93 "bash -l -c 'nvcc -I/usr/include -o /tmp/test_nccl /tmp/test_nccl.cu -lnccl && /tmp/test_nccl'"
```

## 编译 nccl-tests

```bash
# 创建工作目录
ssh jianliu@10.10.70.93 "source ~/.bashrc && mkdir -p ~/work/bandwidth_test/"

# 克隆并编译
ssh jianliu@10.10.70.93 "bash -l -c '
  cd ~/work/bandwidth_test/
  git clone https://github.com/NVIDIA/nccl-tests.git
  cd nccl-tests
  make -j\$(nproc)
'"

# 确认编译产物
ssh jianliu@10.10.70.93 "source ~/.bashrc && ls -lh ~/work/bandwidth_test/nccl-tests/build/*_perf"
```

**注意:** RTX 5090 (CC 12.0, sm_120) 在 nccl-tests Makefile 中已自动支持。

## 运行带宽测试

### 单 GPU 验证（快速检查）

```bash
ssh jianliu@10.10.70.93 "bash -l -c '
  cd ~/work/bandwidth_test/nccl-tests/build
  ./all_reduce_perf -b 8 -e 256M -f 2 -g 1 2>&1 | tail -5
'"
```

### 单 NUMA 4 卡测试（最优拓扑）

```bash
ssh jianliu@10.10.70.93 "bash -l -c '
  cd ~/work/bandwidth_test/nccl-tests/build
  CUDA_VISIBLE_DEVICES=0,1,2,3 ./all_reduce_perf -b 8 -e 8G -f 2 -g 4 2>&1
'"
```

### 全量 8 卡测试

```bash
ssh jianliu@10.10.70.93 "bash -l -c '
  cd ~/work/bandwidth_test/nccl-tests/build
  ./all_reduce_perf -b 8 -e 8G -f 2 -g 8 2>&1
  ./all_gather_perf -b 8 -e 8G -f 2 -g 8 2>&1
'"
```

### 8× RTX 5090 参考值（待实测补充）

| 操作 | 预期值 | 说明 |
|------|--------|------|
| all_reduce (8卡) | TBD | 同 NUMA 4 卡应优于跨 NUMA 8 卡 |
| 跨服务器 (93↔95↔96) | TBD | 通过 Mellanox ConnectX-6 Dx RoCE |

## Docker 安装

```bash
# 安装 Docker
ssh jianliu@10.10.70.93 "echo 'PASSWORD' | sudo -S bash -c '
  apt-get update && apt-get install -y ca-certificates curl
  install -m 0755 -d /etc/apt/keyrings
  curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
  chmod a+r /etc/apt/keyrings/docker.asc
  echo \"deb [arch=\$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \$(. /etc/os-release && echo \\\"\$VERSION_CODENAME\\\") stable\" | tee /etc/apt/sources.list.d/docker.list > /dev/null
  apt-get update && apt-get install -y docker-ce docker-ce-cli containerd.io
  usermod -aG docker jianliu
'"

# 验证
ssh jianliu@10.10.70.93 "source ~/.bashrc && docker --version"
```

### NVIDIA Container Toolkit（Docker GPU 支持）

```bash
ssh jianliu@10.10.70.93 "echo 'PASSWORD' | sudo -S bash -c '
  curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
  curl -sL https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | sed \"s#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g\" | tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
  apt-get update && apt-get install -y nvidia-container-toolkit
  nvidia-ctk runtime configure --runtime=docker
  systemctl restart docker
'"

# 验证 GPU 容器运行
ssh jianliu@10.10.70.93 "source ~/.bashrc && docker run --rm --gpus all nvidia/cuda:13.2-base-ubuntu22.04 nvidia-smi 2>&1 | head -5"
```

## 多机 NCCL 测试（RDMA/RoCE 配置）

三台服务器（93/95/96）均配备 **Mellanox ConnectX-6 Dx** 双端口网卡，支持 RoCE v2。

### 检查 RDMA 设备

```bash
# 在所有三台服务器上执行
for host in 93 95 96; do
  echo "--- 10.10.70.$host ---"
  ssh jianliu@10.10.70.$host "source ~/.bashrc && ibstat 2>/dev/null | head -10 || echo 'No InfiniBand'; rdma link show 2>/dev/null || echo 'No RDMA link'; ip addr show ens20f0 | head -3"
done
```

### NCCL 多机通信关键环境变量

```bash
export NCCL_SOCKET_IFNAME=ens20f0          # 使用 Mellanox 网卡
export NCCL_IB_DISABLE=0                    # 启用 InfiniBand/RoCE
export NCCL_IB_HCA=mlx5                     # 使用 Mellanox HCA
export NCCL_NET_GDR_LEVEL=5                 # 启用 GPU Direct RDMA
export NCCL_DEBUG=INFO                      # 调试信息
```

### 多机带宽测试

```bash
# 在两台服务器上分别运行
# 服务器 1 (93):
ssh -t jianliu@10.10.70.93 "bash -l -c '
  cd ~/work/bandwidth_test/nccl-tests/build
  NCCL_SOCKET_IFNAME=ens20f0 NCCL_DEBUG=INFO ./all_reduce_perf -b 8 -e 256M -f 2 -g 8 2>&1
'"
```

## vLLM 环境部署（从 70.88 复制源码）

### 前置条件

- Python 3.12 (deadsnakes PPA)
- CUDA nvcc 13.2 (`cuda-nvcc-13-2`)
- `systemd-run` 或 `screen` 用于后台执行（避免 SSH 超时断连）

### 快速部署脚本

部署流程：创建 venv → 安装 cmake/ninja → 安装 PyTorch → 编译 vLLM。

**已知问题：** 阿里云 PyPI 镜像 (`mirrors.aliyun.com`) 的某些 NVIDIA 包 SHA256 校验失败。解决方案：
1. PyTorch 安装时同时使用阿里云主索引 + download.pytorch.org 额外索引
2. vLLM 编译时使用默认 PyPI（不加镜像），配合 `--no-cache-dir` 避免缓存问题

一键部署脚本（上传到服务器执行）：

```bash
# 从 WSL 复制
scp /tmp/run_build.sh jianliu@10.10.70.93:/tmp/run_build.sh

# 在服务器执行（screen 后台运行）
ssh jianliu@10.10.70.93 "screen -dmS vllm bash /tmp/run_build.sh"

# 查看进度
ssh jianliu@10.10.70.93 "tail -5 /tmp/build.log"

# 实时监控
ssh -t jianliu@10.10.70.93 "screen -r vllm"
# Ctrl+A, D 分离 screen
```

## vLLM 构建（jasl/ds4-sm120 fork）

vLLM fork from `https://github.com/jasl/vllm/tree/ds4-sm120`，包含 DeepSeek V4 专用 SM12x sparse MLA 内核优化和 FP8 einsum 路径。**已构建完成**（vLLM 0.6.0.dev0）。

### 已有的环境

- **源码**: `/data/vllm-ds4-sm120/`
- **venv**: `/data/venvs/vllm-ds4/` (Python 3.12, 7.4 GB site-packages)
- **CUDA**: 13.2 nvcc (`cuda-nvcc-13-2`) + cuda-nvrtc-dev + libcusparse-dev + libcusolver-dev + libcublas-dev + libnccl2
- **PyTorch**: 2.11.0+cu130
- **git**: 已安装（CMake 构建需要）

### 完整构建步骤（参考用）

> 注意：此 fork 需要通过源文件编译安装（非 vLLM 官方），因此需要 CUDA Toolkit dev 包支持。

```bash
# 1. Python 3.12 venv
python3.12 -m venv /data/venvs/vllm-ds4 --clear
source /data/venvs/vllm-ds4/bin/activate

# 2. 基础构建工具（使用 Tsinghua 镜像加速）
pip install cmake ninja setuptools-scm -q \
  -i https://pypi.tuna.tsinghua.edu.cn/simple/ --default-timeout=600

# 3. PyTorch (cu130) — Tsinghua镜像 + download.pytorch.org补充
pip install torch torchvision torchaudio \
  -i https://pypi.tuna.tsinghua.edu.cn/simple/ \
  --extra-index-url https://download.pytorch.org/whl/cu130 \
  --no-cache-dir --default-timeout 1800

# 4. 构建 vLLM
export MAX_JOBS=4 SETUPTOOLS_SCM_PRETEND_VERSION=0.6.0.dev0
cd /data/vllm-ds4-sm120
pip install -e . --no-build-isolation \
  -i https://pypi.tuna.tsinghua.edu.cn/simple/ \
  --no-cache-dir --default-timeout 1800
```

### 已知问题与解决方案

| 问题 | 原因 | 解决 |
|------|------|------|
| `setuptools_scm` not found | 未安装 setuptools-scm | `pip install setuptools-scm` |
| CMake: `CUDA_nvrtc_LIBRARY NOTFOUND` | cuda-nvcc 最小安装不包含 NVRTC 库 | `apt install cuda-nvrtc-dev-13-2` |
| `cusparseDn.h: No such file` | 缺少 cusparse 开发头文件 | `apt install libcusparse-dev-13-2` |
| `cusolverDn.h: No such file` | 缺少 cusolver 开发头文件 | `apt install libcusolver-dev-13-2` |
| `Can not find git for clone of cutlass` | git 未安装 | `apt install git` |
| SHA256 mismatch (Aliyun mirror) | 镜像缓存损坏 | 换用 Tsinghua 镜像 (`pypi.tuna.tsinghua.edu.cn`) 或加 `--no-cache-dir` |
| PyPI timeout from China | 直连 files.pythonhosted.org 慢 | 使用 `--index-url https://pypi.tuna.tsinghua.edu.cn/simple/` |

### 验证

```bash
source /data/venvs/vllm-ds4/bin/activate
python -c "import vllm; print(vllm.__version__)"
# 应输出: 0.6.0.dev0
```

## 综合检查命令

```bash
ssh jianliu@10.10.70.93 "source ~/.bashrc && \\
  echo '=== GPU ==='; nvidia-smi --query-gpu=name,driver_version --format=csv,noheader | head -1;
  echo '=== CUDA Driver ==='; nvidia-smi -q | grep 'CUDA Version';
  echo '=== nvcc ==='; /usr/local/cuda/bin/nvcc --version 2>&1 | tail -2;
  echo '=== NCCL ==='; awk '/NCCL_(MAJOR|MINOR|PATCH)/{printf \"%s.%s.%s\\\\n\", \$3, \$3, \$3}' /usr/include/nccl.h;
  echo '=== nccl-tests ==='; ls ~/work/bandwidth_test/nccl-tests/build/*_perf 2>/dev/null | wc -l;
  echo '=== Python torch ==='; python3 -c 'import torch; print(\"torch\", torch.__version__)' 2>/dev/null || echo 'no torch';
  echo '=== Docker ==='; docker --version 2>&1 || echo 'no docker';
  echo '=== Disk ==='; df -h / | tail -1
"
```

## 常用快捷命令

| 目的 | 命令 |
|------|------|
| 快速检查状态 | `ssh jianliu@10.10.70.93 "source ~/.bashrc && nvidia-smi --query-gpu=name,driver_version,memory.used --format=csv"` |
| 监控 GPU | `ssh -t jianliu@10.10.70.93 "watch -n 1 nvidia-smi"` |
| 查看 GPU 拓扑 | `ssh jianliu@10.10.70.93 "source ~/.bashrc && nvidia-smi topo -m"` |
| 查看磁盘 | `ssh jianliu@10.10.70.93 "source ~/.bashrc && df -h /"` |
| 查看 RDMA | `ssh jianliu@10.10.70.93 "source ~/.bashrc && rdma link show"` |
| 查看日志 | `ssh -t jianliu@10.10.70.93 "journalctl -n 50 -f"` |

## 注意事项

- **8×32GB = 256GB 总 VRAM**，适合 70B+ 模型推理
- **无代理，直连互联网**（与 70.88 不同，无需 `source ~/.bashrc`）
- **全新裸机** — CUDA Toolkit、NCCL、Docker、PyTorch 目前已安装基础工具链
- **`--no-cache-dir` 很重要** — 阿里云 PyPI 镜像的某些包存在 SHA256 校验问题，安装 vLLM 依赖时建议使用默认 PyPI
- **sudo 密码** 同 70.88，`!` 需要用单引号包裹
- **Mellanox ConnectX-6 Dx** — 双端口 100/200GbE，支持 RoCE v2 和 GPUDirect RDMA
- **同 NUMA 4 卡性能最佳** — GPU0-3 (NUMA 0) 或 GPU4-7 (NUMA 1)
- **三台同配置集群** — 93/95/96 完全一致，配置可批量通过 `for h in 93 95 96; do ... done` 执行
