---
name: remote-70-95
description: 远程操作 GPU 服务器 (10.10.70.95 / oem95) — SSH 连接、CUDA Toolkit 安装、NCCL 管理、8×RTX 5090 环境搭建
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [ssh, gpu, cuda, nccl, nvcc, bandwidth-test, remote, devops, rtx5090, blackwell]
    related_skills: [remote-70-93, remote-70-96, remote-70-88]
---

# Remote GPU Server (10.10.70.95 / oem95)

远程操作 GPU 服务器 10.10.70.95 (oem95) 的常用工作流。与 10.10.70.93 (oem93) 和 10.10.70.96 (oem96) 完全相同的硬件配置，
三台服务器构成 GPU 集群，通过 Mellanox ConnectX-6 Dx NIC 互联。

> **与 70.93 的区别：** 70.95 使用 LVM 卷组（`/dev/mapper/vgubuntu-root`）而非直接分区，
> 内核版本为 **6.8.0-111-generic**（较新）。其余硬件完全一致。

## 环境信息

| 项目 | 值 |
|------|-----|
| 主机名 | oem95 |
| IP | 10.10.70.95 |
| 用户 | jianliu |
| 系统 | Ubuntu 22.04.1 LTS (Jammy) |
| 内核 | 6.8.0-111-generic（比 93/96 的 5.15 更新） |
| CPU | 128× Intel Xeon (2 NUMA 节点) |
| 内存 | 1.0 TiB |
| 磁盘 | 1.7T (LVM: /dev/mapper/vgubuntu-root, 使用 1%) |
| GPU | 8× NVIDIA RTX 5090 (Blackwell, CC 12.0, 32GB/卡, PCIe Gen4×16) |
| 驱动 | 595.58.03 |
| CUDA Driver | 13.2 |
| CUDA Toolkit | 未安装 |
| NCCL | 未安装 |
| Docker | 未安装 |
| Python | 3.10.12 (系统) |
| PyTorch | 未安装 |
| NIC | 2× Mellanox ConnectX-6 Dx (MT2892) — 支持 RoCE / RDMA |
| 代理 | `http://10.10.60.140:7890`（已在 `~/.bashrc` 中配置，同 70.88） |
| sudo | 需要密码（同 70.88/93） |

### GPU 拓扑

与 70.93 完全一致：8 张 GPU 分布在 2 个 NUMA 节点，同 NUMA 内 NODE 互连，跨 NUMA 经 SYS。

## vLLM 环境

vLLM (jasl/ds4-sm120 fork, v0.6.0.dev0) 已编译安装完成：

- **源码**: `/data/vllm-ds4-sm120/`
- **venv**: `/data/venvs/vllm-ds4/` (Python 3.12, 7.4 GB)
- **PyTorch**: 2.11.0+cu130
- **CUDA**: 13.2 nvcc + 完整 CUDA dev 库（nvrtc, cublas, cusparse, cusolver dev）
- **完成时间**: 2026-05-10 00:36 CST

验证方式：`source /data/venvs/vllm-ds4/bin/activate && python -c "import vllm; print(vllm.__version__)"`

## SSH 连接

> **重要：** 服务器代理配置在 `~/.bashrc` 中，但非交互式 SSH 不会自动加载 `.bashrc`。**所有通过 SSH 执行的命令都必须先 `source ~/.bashrc`** 才能正常使用代理访问 GitHub / PyPI 等外部服务。

```bash
# 首次连接接受 host key
ssh -o StrictHostKeyChecking=accept-new jianliu@10.10.70.95 "echo connected"

# 交互式登录（自动加载 ~/.bashrc 环境）
ssh -t jianliu@10.10.70.95 "source ~/.bashrc && bash -l"

# 执行命令并返回（务必 source ~/.bashrc）
ssh jianliu@10.10.70.95 "source ~/.bashrc && command"

# 需要 sudo 时通过管道传密码（同时 source ~/.bashrc）
ssh jianliu@10.10.70.95 "source ~/.bashrc && echo 'PASSWORD' | sudo -S apt-get install -y PACKAGE"
```

**注意:**
- **代理已配置** (`http://10.10.60.140:7890`) — 非交互式 SSH 不会加载 `~/.bashrc`，**务必在每个命令前加 `source ~/.bashrc &&`**（同 70.88 的注意事项）
- sudo 密码同 70.88 服务器。`!` 在 bash 中有特殊含义，需要用单引号包裹：`echo '!QAZ2wsx' | sudo -S ...`
- `-t` 参数仅在需要 PTY 时使用（watch、top、交互式 sudo）

## 所有操作参考 remote-70-93

**70.93、70.95、70.96 三台服务器硬件配置完全相同**，所有安装和操作步骤与 remote-70-93 skill 一致：

| 操作 | 参考命令 |
|------|---------|
| CUDA Toolkit 安装 | 见 remote-70-93 skill: `apt-get install -y cuda-nvcc-13-2` |
| NCCL 安装 | 见 remote-70-93 skill: `apt-get install -y libnccl2 libnccl-dev` |
| nccl-tests 编译 | `git clone + make` 步骤同上 |
| Docker 安装 | 同上 |
| NVIDIA Container Toolkit | 同上 |
| 多机 NCCL 测试 | 三台配合使用 Mellanox ConnectX-6 Dx RoCE |

批量操作示例：

```bash
# 同时在 3 台服务器执行命令
for host in 93 95 96; do
  echo "=== 10.10.70.$host ==="
  ssh jianliu@10.10.70.$host "source ~/.bashrc && bash -l -c 'echo OK'"
done
```

## 综合检查命令

```bash
ssh jianliu@10.10.70.95 "source ~/.bashrc && \
  echo '=== GPU ==='; nvidia-smi --query-gpu=name,driver_version --format=csv,noheader | head -1;
  echo '=== CUDA Driver ==='; nvidia-smi -q | grep 'CUDA Version';
  echo '=== nvcc ==='; /usr/local/cuda/bin/nvcc --version 2>&1 | tail -2;
  echo '=== NCCL ==='; awk '/NCCL_(MAJOR|MINOR|PATCH)/{printf \"%s.%s.%s\\n\", \$3, \$3, \$3}' /usr/include/nccl.h;
  echo '=== nccl-tests ==='; ls ~/work/bandwidth_test/nccl-tests/build/*_perf 2>/dev/null | wc -l;
  echo '=== Disk ==='; df -h / | tail -1
"
```

## 常用快捷命令

| 目的 | 命令 |
|------|------|
| 快速检查 | `ssh jianliu@10.10.70.95 "source ~/.bashrc && nvidia-smi --query-gpu=name,driver_version,memory.used --format=csv"` |
| GPU 监控 | `ssh -t jianliu@10.10.70.95 "watch -n 1 nvidia-smi"` |
| GPU 拓扑 | `ssh jianliu@10.10.70.95 "source ~/.bashrc && nvidia-smi topo -m"` |
| 磁盘 | `ssh jianliu@10.10.70.95 "source ~/.bashrc && df -h /"` |
| 网卡 | `ssh jianliu@10.10.70.95 "source ~/.bashrc && ip addr show ens20f0 && rdma link show"` |

## 注意事项

- 与 70.93、70.96 **完全同配置**，所有安装步骤一致
- 内核 6.8.0（较新）— 对 Mellanox/RDMA 支持更好
- **代理已配置** — `http://10.10.60.140:7890` 已写入 `~/.bashrc`（同 70.88），非交互式 SSH 需要 `source ~/.bashrc &&` 才能生效
- LVM 卷组存储，扩展性强（可加磁盘扩充卷组）
- 三台集群建议使用统一工具链版本，避免 NCCL CUDA 版本不一致导致的通信问题
