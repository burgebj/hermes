---
name: remote-70-66
description: 远程操作 GPU 服务器 (10.10.70.66) — SSH 连接、CUDA/nvcc 配置、NCCL 安装、6×A100 环境管理
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [ssh, gpu, cuda, nccl, nvcc, a100, remote, devops]
    related_skills: [remote-70-88]
---

# Remote GPU Server (10.10.70.66)

远程操作 GPU 服务器 10.10.70.66 的常用工作流。包含 SSH 连接、CUDA 工具链配置、NCCL 安装、环境搭建等操作。

## 环境信息

| 项目 | 值 |
|------|-----|
| 主机 | 10.10.70.66 |
| 用户 | jianliu |
| 系统 | Ubuntu 20.04.6 LTS (Focal Fossa) |
| 内核 | 5.15.0-119-generic |
| CPU | 128× Intel Xeon Platinum 8336C @ 2.30GHz |
| 内存 | 1.0 TiB |
| 磁盘 | 5.2T (已用 95%，仅剩 ~260G) |
| GPU | 6× NVIDIA A100-PCIE-40GB (Ampere, CC 8.0) |
| 驱动 | 535.216.01 |
| CUDA Driver API | 12.2 |
| CUDA Toolkit | 12.3.107 (安装于 /usr/local/cuda-12.3，/usr/local/cuda → cuda-12.3) |
|  | 另有 CUDA 12.2 (安装于 /usr/local/cuda-12.2，对应驱动版本) |
| 系统 nvcc | **CUDA 10.1.243** (`/usr/bin/nvcc`) — 与 /usr/local/cuda 不同，PATH 需注意 |
| NCCL | 未安装 |
| PyTorch | 未安装 |
| Python | 3.8.10 (系统) |
| Docker | 27.2.1 |
| nvidia-persistenced | 运行中 |
| sudo | 需要密码（同 70.88） |

## GPU 拓扑

**NUMA 架构:** 2 个 NUMA 节点，每个节点 3 张 GPU

```
NUMA 0 (CPU 0-31, 64-95): GPU0, GPU1, GPU2
NUMA 1 (CPU 32-63, 96-127): GPU3, GPU4, GPU5

     GPU0  GPU1  GPU2  GPU3  GPU4  GPU5
GPU0   X    PIX   PXB   SYS   SYS   SYS
GPU1  PIX    X    NV12  PXB   SYS   SYS
GPU2  PXB   NV12   X    PIX   SYS   SYS
GPU3  SYS   SYS   PIX    X    PXB   PXB
GPU4  SYS   SYS   SYS   PXB    X    NV12
GPU5  SYS   SYS   SYS   PXB   NV12   X
```

- **GPU0↔GPU1**: PIX（同 PCIe 交换机，低延迟）
- **GPU1↔GPU2, GPU4↔GPU5**: NV12（NVLink 桥接，最高带宽）
- **GPU0↔GPU3, GPU1↔GPU4, GPU2↔GPU5**: SYS（跨 NUMA，需经 QPI/UPI，延迟最高）
- **PCIe**: Gen 4 ×16

## SSH 连接

```bash
# 首次连接接受 host key
ssh -o StrictHostKeyChecking=accept-new jianliu@10.10.70.66 "echo connected"

# 交互式登录
ssh -t jianliu@10.10.70.66

# 执行命令并返回
ssh jianliu@10.10.70.66 "command"

# 需要 sudo 时通过管道传密码
ssh jianliu@10.10.70.66 "echo 'PASSWORD' | sudo -S apt-get install -y PACKAGE"
```

**注意:** sudo 密码同 70.88 服务器。`-t` 参数仅在需要 PTY 时使用。

## CUDA 环境说明

### 已有 CUDA 安装

| 路径 | 版本 | 说明 |
|------|------|------|
| `/usr/local/cuda-12.3` | 12.3.107 | 完整 CUDA Toolkit（nvcc 12.3） |
| `/usr/local/cuda-12.2` | 12.2 | 与驱动 CUDA Version 12.2 匹配 |
| `/usr/local/cuda` | → 12.3 | 符号链接指向 12.3 |
| `/usr/bin/nvcc` | **10.1.243** | 系统包管理器安装的旧版本 |

### PATH 注意事项

**重要：** 系统默认 `/usr/bin/nvcc` 是 CUDA 10.1，远低于 `/usr/local/cuda/bin/nvcc`（CUDA 12.3）。使用 nvcc 时必须确保 PATH 优先指向 `/usr/local/cuda/bin`：

```bash
# 正确使用 CUDA 12.3 nvcc
export PATH=/usr/local/cuda/bin:$PATH
/usr/local/cuda/bin/nvcc --version  # CUDA 12.3

# 避免使用旧版系统 nvcc
/usr/bin/nvcc --version  # CUDA 10.1 — 太旧，不兼容 A100 (CC 8.0)
```

### 检查驱动兼容的 CUDA 版本

```bash
ssh jianliu@10.10.70.66 "nvidia-smi -q | grep 'CUDA Version'"
# 输出: CUDA Version: 12.2
# → 驱动支持最高 CUDA 12.x 版本
```

**版本匹配规则:**
- 驱动 CUDA Version 12.2 → 支持 **CUDA 12.x** 全系列
- CUDA 12.3 toolkit（已安装）在当前驱动上兼容运行
- A100 (CC 8.0) 需要 CUDA 11.0+，CUDA 12.3 完全支持

## NCCL 安装

70.66 目前**未安装 NCCL**。需要在 CUDA 12.3 环境下安装。

### Step 1: 安装 libnccl

通过 NVIDIA 仓库安装（Ubuntu 20.04 focal）：

```bash
# 添加 NVIDIA CUDA 仓库（需 sudo）
ssh jianliu@10.10.70.66 "echo 'PASSWORD' | sudo -S bash -c '
  wget -q https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2004/x86_64/cuda-keyring_1.1-1_all.deb
  dpkg -i cuda-keyring_1.1-1_all.deb
  apt-get update
'"
```

安装 NCCL：

```bash
# 查看可用版本
ssh jianliu@10.10.70.66 "apt-cache madison libnccl2"

# 安装与 CUDA 12.x 匹配的 NCCL
ssh jianliu@10.10.70.66 "echo 'PASSWORD' | sudo -S apt-get install -y libnccl2 libnccl-dev"
```

### Step 2: 验证 NCCL

```bash
cat > /tmp/test_nccl.cu << 'EOF'
#include <nccl.h>
#include <stdio.h>
int main() {
  printf("NCCL compiled OK\n");
#if NCCL_VERSION_CODE
  printf("NCCL version code: %d\n", NCCL_VERSION_CODE);
#endif
  return 0;
}
EOF
/usr/local/cuda/bin/nvcc -I/usr/include -o /tmp/test_nccl /tmp/test_nccl.cu -lnccl 2>&1 && /tmp/test_nccl
```

## 编译 nccl-tests

```bash
# 创建工作目录
mkdir -p ~/work/bandwidth_test/
cd ~/work/bandwidth_test/
git clone https://github.com/NVIDIA/nccl-tests.git
cd nccl-tests
make -j$(nproc)
```

**注意:**
- A100 (CC 8.0, sm_80) 在 nccl-tests Makefile 中自动支持
- CUDA 12.3 nvcc 使用 `-std=c++17`
- 确保使用 `/usr/local/cuda/bin/nvcc`（非系统 `/usr/bin/nvcc`）
- 如果编译时找不到 nccl.h，检查 libnccl-dev 是否正确安装

### nvcc 架构号速查

| GPU 架构 | 架构号 (sm_) | 对应 GPU |
|----------|-------------|----------|
| Ampere | sm_80, sm_86 | **A100 (sm_80)**, A40, RTX 3090 |
| Ada Lovelace | sm_89 | RTX 4090 |
| Hopper | sm_90 | H100 |
| Blackwell | sm_120 | RTX 5090 |

## 环境准备（首次设置）

### 创建标准工作目录结构

```bash
ssh jianliu@10.10.70.66 "mkdir -p ~/work/bandwidth_test/nccl-tests"
```

### 安装 PyTorch（如需要）

```bash
# Python 3.8 + CUDA 12.x
ssh jianliu@10.10.70.66 "pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121"
```

**注意:** 磁盘仅剩 ~260G，安装大型包前请确认空间充足。

## 运行带宽测试

### 单 GPU 验证

```bash
cd ~/work/bandwidth_test/nccl-tests/build
./all_reduce_perf -b 8 -e 256M -f 2 -g 1 2>&1 | tail -5
```

### 2 卡测试（基础性能）

```bash
# 选择 NVLink 连接的 pair (GPU1↔GPU2 通过 NVLink)
CUDA_VISIBLE_DEVICES=1,2 ./all_reduce_perf -b 8 -e 8G -f 2 -g 2 2>&1

# 跨 NUMA 对比 (GPU0↔GPU3 经过 SYS)
CUDA_VISIBLE_DEVICES=0,3 ./all_reduce_perf -b 8 -e 8G -f 2 -g 2 2>&1
```

### 6 卡全集合操作

```bash
# all_reduce (全部 6 卡)
./all_reduce_perf -b 8 -e 8G -f 2 -g 6 2>&1

# 单 NUMA 节点 3 卡 (NUMA 0)
CUDA_VISIBLE_DEVICES=0,1,2 ./all_reduce_perf -b 8 -e 8G -f 2 -g 3 2>&1
```

### A100 参考性能值

| 操作 | 预期峰值 BusBW (GB/s) | 说明 |
|------|:--------------------:|------|
| all_reduce (2卡 NVLink) | ~300-400 | NVLink 600 GB/s 双工 |
| all_reduce (2卡 PCIe) | ~25 | PCIe 4.0 ×16 单方向 |
| all_reduce (6卡) | ~200-300 | 混合 NVLink + PCIe 拓扑 |
| all_gather (6卡) | ~200-300 | |
| broadcast (6卡) | ~200-300 | |

**注意:** A100 的 NVLink 带宽远高于 PCIe 4.0。同一 NUMA 节点内 NVLink 连接的 pair 性能最佳。

## 综合检查命令

```bash
ssh jianliu@10.10.70.66 "
  echo '=== GPU ==='; nvidia-smi --query-gpu=name,driver_version,memory.used --format=csv,noheader;
  echo '=== CUDA Driver ==='; nvidia-smi -q | grep 'CUDA Version';
  echo '=== nvcc (local) ==='; /usr/local/cuda/bin/nvcc --version 2>&1 | tail -2;
  echo '=== NCCL ==='; cat /usr/include/nccl.h 2>/dev/null | grep NCCL_MAJOR || echo 'NCCL not installed';
  echo '=== Python torch ==='; python3 -c 'import torch; print(\"torch\", torch.__version__); print(\"cuda\", torch.version.cuda)' 2>/dev/null || echo 'torch not installed';
  echo '=== Disk ==='; df -h / | tail -1;
  echo '=== Topology ==='; nvidia-smi topo -m 2>&1 | head -10
"
```

## 常用快捷命令

| 目的 | 命令 |
|------|------|
| 快速检查状态 | `ssh jianliu@10.10.70.66 "nvidia-smi --query-gpu=name,driver_version,memory.used --format=csv"` |
| 监控 GPU | `ssh -t jianliu@10.10.70.66 "watch -n 1 nvidia-smi"` |
| 查看磁盘 | `ssh jianliu@10.10.70.66 "df -h /"` |
| 查看 GPU 拓扑 | `ssh jianliu@10.10.70.66 "nvidia-smi topo -m"` |
| CUDA 版本检查 | `ssh jianliu@10.10.70.66 "/usr/local/cuda/bin/nvcc --version"` |

## Docker GPU 容器

Docker 27.2.1 支持 CDI (Container Device Interface)。参考 70.88 的配置方式：

```bash
# 检查 nvidia-container-toolkit
ssh jianliu@10.10.70.66 "dpkg -l | grep nvidia-container"

# 运行 GPU 容器（推荐使用 CDI device 语法）
ssh jianliu@10.10.70.66 "echo 'PASSWORD' | sudo -S docker run --rm --device='nvidia.com/gpu=all' nvidia/cuda:12.2-base-ubuntu20.04 nvidia-smi"
```

## 注意事项

- **磁盘空间紧张 (95%)** — 安装大型包前务必确认剩余空间
- **系统 nvcc 是 CUDA 10.1** — 始终使用 `/usr/local/cuda/bin/nvcc` 而非 `/usr/bin/nvcc`
- **sudo 需要密码** — 通过管道传入时注意特殊字符转义（`!` 用单引号包裹）
- **没有 ~/work/** — 首次使用需创建标准目录结构
- **NCCL 未安装** — 首次使用需按上述步骤安装
- **A100 没有 NVSwitch** — 但 pair 间有 NVLink (NV12)，跨 NUMA 通信性能较差
- 同一 NUMA 节点内 GPU 通信性能最佳（GPU0/1/2 或 GPU3/4/5）
- GPU1↔GPU2 和 GPU4↔GPU5 之间有 NVLink，适合 pair 级高速通信