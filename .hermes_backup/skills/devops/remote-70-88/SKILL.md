---
name: remote-70-88
description: 远程操作 GPU 服务器 (10.10.70.88) — SSH 连接、CUDA/nvcc 安装、NCCL 版本管理、编译 nccl-tests、运行带宽测试
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [ssh, gpu, cuda, nccl, nvcc, bandwidth-test, remote, devops]
    related_skills: [remote-70-66, systematic-debugging]
---

# Remote GPU Server (10.10.70.88)

远程操作 GPU 服务器 10.10.70.88 的常用工作流。包含 SSH 连接、CUDA 工具链安装、NCCL 版本管理、nccl-tests 编译与运行、带宽测试等操作。

## 环境信息

| 项目 | 值 |
|------|-----|
| 主机 | 10.10.70.88 |
| 用户 | jianliu |
| 系统 | Ubuntu 22.04 LTS |
| GPU | 8× NVIDIA RTX 5090 (Blackwell, CC 12.0) |
| 驱动 | 580.126.09 |
| CUDA Driver API | 13.0 |
| CUDA Toolkit | 13.0.88 (仅 nvcc，非完整 toolkit) |
| NCCL | 2.28.9-1+cuda13.0 (系统级) |
| Python | 系统 Python + vLLM venv at `/data/venvs/vllm-ds4/` |
| vLLM fork | 0.6.0.dev0 (`jasl/vllm` ds4-sm120 分支, 源码: `/data/vllm-ds4-sm120/`) |
| 代理 | `http://10.10.60.140:7890` (在 `~/.bashrc` 中配置) |
| 模型路径 | `/home/jianliu/work/models/deepseekv4_flash/` |
| 工作目录 | `~/work/bandwidth_test/` |

## SSH 连接

> **重要：** 服务器需要代理才能访问 GitHub 等外部资源。代理配置在 `~/.bashrc` 中（`http://10.10.60.140:7890`），但非交互式 SSH 不会自动加载 `.bashrc`。**所有通过 SSH 执行的命令都必须先 `source ~/.bashrc`** 才能正常访问 GitHub / PyPI 等外部服务。

```bash
# 首次连接接受 host key
ssh -o StrictHostKeyChecking=accept-new jianliu@10.10.70.88 "echo connected"

# 交互式登录（自动加载 ~/.bashrc 环境）
ssh -t jianliu@10.10.70.88 "source ~/.bashrc && bash -l"

# 执行命令并返回（记得 source ~/.bashrc）
ssh -t jianliu@10.10.70.88 "source ~/.bashrc && command"

# 需要 sudo 时通过管道传密码（同时 source ~/.bashrc）
ssh -t jianliu@10.10.70.88 "source ~/.bashrc && echo 'PASSWORD' | sudo -S apt-get install -y PACKAGE"
```

**注意:** 
- `-t` 参数强制分配伪终端，某些 sudo 操作需要。如果不需要交互，可以省略 `-t`。
- 非交互式 SSH 不会加载 `~/.bashrc`，**务必在每个命令前加 `source ~/.bashrc &&`**，否则代理和 conda 等环境不会生效。
- 代理已配置 `no_proxy=localhost,127.0.0.1,10.0.0.0/8`，发往本地的请求（如 `curl localhost:8000`）会直连不走代理。若仍有问题请检查 `~/.bashrc` 中 `no_proxy` 是否已设置。
- sudo 密码通过管道传入时要注意特殊字符转义（如 `!` 在 bash 中有特殊含义，需要用单引号包裹）。

## CUDA / nvcc 安装与管理

### 安装单独的 nvcc（不是完整 toolkit）

NVIDIA 官方仓库提供细粒度包，可以只装 nvcc 编译器（~87 MB vs 完整 toolkit 3.2 GB）：

```bash
# 添加 NVIDIA 仓库（仅首次）
wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2204/x86_64/cuda-keyring_1.1-1_all.deb
echo 'PASSWORD' | sudo -S dpkg -i cuda-keyring_1.1-1_all.deb
echo 'PASSWORD' | sudo -S apt-get update

# 安装指定版本的 nvcc（选择与驱动匹配的版本）
echo 'PASSWORD' | sudo -S apt-get install -y cuda-nvcc-13-0

# 会自动安装依赖：cuda-cudart-13-0, cuda-cccl-13-0, cuda-crt-13-0 等
# 自动设置 /usr/local/cuda -> /usr/local/cuda-13.0 备选链接
```

### 选择正确的 nvcc 版本

```bash
# 查看驱动支持的 CUDA 版本
ssh jianliu@10.10.70.88 "source ~/.bashrc && nvidia-smi -q | grep 'CUDA Version'"

# 查看可用版本
curl -sL "https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2204/x86_64/Packages.gz" \
  | gunzip -c | grep -E "^Package:|^Version:" | grep -B1 "cuda-nvcc" | tail -20
```

**版本匹配规则:**
- Blackwell (RTX 5090, CC 12.0) 需要 **CUDA 12.8+**
- 优先选择 nvidia-smi 报告的 CUDA Version 对应的大版本
- 例如驱动报告 CUDA 13.0 → 安装 `cuda-nvcc-13-0`
- 可用版本: `cuda-nvcc-12-8`, `cuda-nvcc-12-9`, `cuda-nvcc-13-0`, `cuda-nvcc-13-1`, `cuda-nvcc-13-2`

### 将 CUDA 加入 PATH

```bash
# 添加到 .profile（login shell）和 .bashrc（interactive shell）
echo 'export PATH=/usr/local/cuda/bin:$PATH' >> ~/.profile
echo 'export LD_LIBRARY_PATH=/usr/local/cuda/lib64:$LD_LIBRARY_PATH' >> ~/.profile
echo 'export PATH=/usr/local/cuda/bin:$PATH' >> ~/.bashrc
echo 'export LD_LIBRARY_PATH=/usr/local/cuda/lib64:$LD_LIBRARY_PATH' >> ~/.bashrc

# 验证
bash -l -c "nvcc --version"
```

## NCCL 版本管理

### 查看已安装的 NCCL

```bash
ssh jianliu@10.10.70.88 "source ~/.bashrc && \\
  dpkg -l | grep -i nccl;
  awk '/NCCL_MAJOR|NCCL_MINOR|NCCL_PATCH/{print}' /usr/include/nccl.h | head -3;
  ldconfig -p | grep nccl
"
```

### 查看可用的 NCCL 版本

```bash
# 列出所有可用的 libnccl2 版本
ssh jianliu@10.10.70.88 "source ~/.bashrc && apt-cache madison libnccl2"
```

### 降级/升级 NCCL 以匹配 CUDA 版本

**重要：** NCCL 的包名包含编译时用的 CUDA 版本号（如 `2.28.9-1+cuda13.0`）。必须使用与驱动支持的 CUDA 版本匹配的 NCCL 包。

```bash
# 降级到指定 CUDA 版本的 NCCL
echo 'PASSWORD' | sudo -S apt-get install -y --allow-downgrades \
  libnccl2=2.28.9-1+cuda13.0 libnccl-dev=2.28.9-1+cuda13.0
```

**版本对应关系（Ubuntu 22.04 NVIDIA 仓库）:**

| CUDA 版本 | 最新 NCCL | 说明 |
|-----------|-----------|------|
| cuda13.2 | 2.30.4 | 最新，但需要 CUDA 13.2 驱动 |
| **cuda13.0** | **2.28.9** | **当前机器驱动支持的最新版本** |
| cuda12.9 | 2.30.4 | 可降级到此版本 |
| cuda12.8 | 2.26.2 | 最低 Blackwell 支持 |

### 验证 NCCL

```bash
# 编译测试
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

nccl-tests 在 `~/work/bandwidth_test/nccl-tests/` 目录下。

```bash
# 编译（Makefile 自动检测 CUDA 版本，Blackwell sm_120 已内置支持）
cd ~/work/bandwidth_test/nccl-tests
make -j8

# 编译产物在 build/ 目录
ls -lh build/*_perf
```

**Makefile 自动处理的细节:**
- CUDA 13.0 检测到后自动使用 `-std=c++17`
- Blackwell (sm_120) 自动加入 GENCODE
- NCCL 从系统默认路径链接 (`-lnccl`)

### 故障排除

如果遇到 `fatal error: nccl.h: No such file or directory`:
- 确认 `libnccl-dev` 已安装
- 检查 `/usr/include/nccl.h` 是否存在
- 可手动指定 `NCCL_HOME=/usr` 或 `CUDAT_HOME=/usr/local/cuda`

如果遇到链接错误 `cannot find -lnccl`:
- 确认 `ldconfig -p | grep nccl` 有输出
- 确认 `/usr/lib/x86_64-linux-gnu/libnccl.so` 存在
- 运行 `echo 'PASSWORD' | sudo -S ldconfig` 刷新库缓存

## 运行带宽测试

### 单 GPU 验证（快速检查编译是否正确）

```bash
cd ~/work/bandwidth_test/nccl-tests/build
./all_reduce_perf -b 8 -e 256M -f 2 -g 1 2>&1 | tail -5
```
注意：单 GPU 的 all_reduce 带宽为 0，这是正常的（all_reduce 需要 ≥2 卡才有意义）。用于验证程序能正常运行不崩溃。

### 全量 8 卡测试

```bash
cd ~/work/bandwidth_test/nccl-tests/build

# all_reduce
./all_reduce_perf -b 8 -e 8G -f 2 -g 8 2>&1

# 其他集合操作
./all_gather_perf -b 8 -e 8G -f 2 -g 8 2>&1
./broadcast_perf -b 8 -e 8G -f 2 -g 8 2>&1
./reduce_scatter_perf -b 8 -e 8G -f 2 -g 8 2>&1
./alltoall_perf -b 8 -e 8G -f 2 -g 8 2>&1
./sendrecv_perf -b 8 -e 8G -f 2 -g 8 2>&1
```

### 输出解读

```
     Size      Count  Type   RedOp   Root   AlgoBW (GB/s)  BusBW (GB/s)
  134217728  33554432  float  sum      -1     5986.48        22.42       39.24
```

- **AlgoBW**: 算法带宽（实际传输的数据量/时间）
- **BusBW**: 总线带宽（考虑了 NCCL 内部数据搬运倍数，通常 AlgoBW × 1.7~2.0）
- **Avg bus bandwidth**: 所有 size 的平均总线带宽

### 8× RTX 5090 参考值

| 操作 | 小数据 (< 1MB) | 大数据 (> 128MB) |
|------|---------------|------------------|
| all_reduce | 0.8-3 GB/s | 22-23 GB/s (Algo) / 39-40 GB/s (Bus) |
| (其他操作待补充) | | |

## vLLM fork (jasl/ds4-sm120) 编译与部署

vLLM fork from `https://github.com/jasl/vllm/tree/ds4-sm120`，包含 DeepSeek V4 专用 SM12x sparse MLA 内核优化和 FP8 einsum 路径。

### 环境

- **硬件**: 8× RTX 5090 (Blackwell, CC 12.0), 32GB/卡
- **源码**: `/data/vllm-ds4-sm120/`
- **venv**: `/data/venvs/vllm-ds4/` (Python 3.12)
- **CMake 缓存**: `/data/vllm-ds4-sm120/.deps/` (~2.6GB)
- **PyTorch**: 2.11.0+cu130
- **CMake**: 4.3.2 (pip 安装, 系统 cmake 3.22 太旧)

### 首次编译

```bash
source ~/.bashrc
source /data/venvs/vllm-ds4/bin/activate
export PATH="/usr/local/cuda/bin:/data/venvs/vllm-ds4/bin:$PATH"
export SETUPTOOLS_SCM_PRETEND_VERSION=0.6.0.dev0

cd /data/vllm-ds4-sm120
MAX_JOBS=4 pip install -e . --no-build-isolation \
  -i https://mirrors.aliyun.com/pypi/simple/ \
  --extra-index-url https://download.pytorch.org/whl/cu130
```

### 启动服务

```bash
source ~/.bashrc
source /data/venvs/vllm-ds4/bin/activate

vllm serve /home/jianliu/work/models/deepseekv4_flash \
  --host 0.0.0.0 --port 8000 \
  --tensor-parallel-size 8 \
  --gpu-memory-utilization 0.90 \
  --trust-remote-code \
  --kv-cache-dtype fp8 \
  --block-size 256 \
  --enable-expert-parallel \
  --data-parallel-size 8 \
  --tokenizer-mode deepseek_v4 \
  --tool-call-parser deepseek_v4 \
  --enable-auto-tool-choice \
  --reasoning-parser deepseek_v4 \
  --enforce-eager
```

### 后台运行

```bash
source ~/.bashrc
source /data/venvs/vllm-ds4/bin/activate
nohup vllm serve /home/jianliu/work/models/deepseekv4_flash \
  ...(同上) > /data/vllm_server.log 2>&1 &
```

### 测试 API

```bash
curl http://localhost:8000/v1/models
curl http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "/home/jianliu/work/models/deepseekv4_flash", "messages": [{"role": "user", "content": "Hello"}]}'
```

## Docker vLLM 部署

也可以使用 `vllm/vllm-openai:latest` Docker 镜像直接运行 vLLM 服务，无需源码编译。

### 启动容器

```bash
# 拉取最新镜像
docker pull vllm/vllm-openai:latest

# 启动容器（所有 GPU + 模型目录挂载）
docker run --gpus all \
  -v /home/jianliu/work/models:/models \
  -p 8000:8000 \
  --shm-size=32g \
  vllm/vllm-openai:latest \
  --model /models/deepseekv4_flash \
  --host 0.0.0.0 --port 8000 \
  --tensor-parallel-size 8 \
  --gpu-memory-utilization 0.90 \
  --trust-remote-code \
  --kv-cache-dtype fp8 \
  --block-size 256 \
  --enable-expert-parallel \
  --data-parallel-size 8 \
  --tokenizer-mode deepseek_v4 \
  --tool-call-parser deepseek_v4 \
  --enable-auto-tool-choice \
  --reasoning-parser deepseek_v4
```

### 检查 Docker 容器

```bash
# 查看运行中的容器
docker ps

# 查看容器日志
docker logs <container_id> --tail 100

# 测试 API
curl http://localhost:8000/v1/models
```

### 停止和清理

```bash
# 停止容器
docker stop <container_id>

# 删除容器（保留镜像）
docker rm <container_id>
```

**Docker 方式 vs 源码编译方式对比：**
- Docker：快速启动、隔离环境、无需管理 venv，适合快速验证
- 源码编译：可使用自定义分支（如 `jasl/vllm` ds4-sm120），获得 DeepSeek V4 专用内核优化

一键检查所有关键组件：

```bash
ssh -t jianliu@10.10.70.88 "source ~/.bashrc && \\
  echo '=== GPU ==='; nvidia-smi --query-gpu=name,driver_version --format=csv,noheader | head -1;
  echo '=== CUDA Driver ==='; nvidia-smi -q | grep 'CUDA Version';
  echo '=== nvcc ==='; /usr/local/cuda/bin/nvcc --version 2>&1 | tail -2;
  echo '=== NCCL ==='; awk '/NCCL_(MAJOR|MINOR|PATCH)/{printf \"%s.%s.%s\\n\", \$3, \$3, \$3}' /usr/include/nccl.h;
  echo '=== nccl-tests ==='; ls ~/work/bandwidth_test/nccl-tests/build/*_perf 2>/dev/null | wc -l;
  echo '=== Python torch ==='; python3 -c 'import torch; print(\"torch\", torch.__version__)' 2>/dev/null || echo 'torch not found'
"
```

## 常用快捷命令

| 目的 | 命令 |
|------|------|
| 快速检查状态 | `ssh jianliu@10.10.70.88 "source ~/.bashrc && nvidia-smi --query-gpu=name,driver_version,memory.used --format=csv"` |
| 监控 GPU | `ssh -t jianliu@10.10.70.88 "watch -n 1 nvidia-smi"` |
| 查看日志 | `ssh -t jianliu@10.10.70.88 "journalctl -n 50 -f"` |
| 查看磁盘 | `ssh jianliu@10.10.70.88 "source ~/.bashrc && df -h /"` |
| 网络测试 | `ssh jianliu@10.10.70.88 "source ~/.bashrc && iperf3 -c <server>"` |

## 注意事项

- `-t` 参数对于需要 PTY 的命令（watch、top、sudo 交互）是必须的，否则会报 "Pseudo-terminal will not be allocated"
- sudo 密码通过管道传入时要注意特殊字符转义（如 `!` 在 bash 中有特殊含义，需要用单引号包裹）
- NVIDIA 仓库在中国区域会自动重定向到 `developer.download.nvidia.cn`（镜像加速）
- 不要在 cron job 或非交互式脚本中硬编码密码 — 优先设置 SSH key 免密登录
- nccl-tests 编译时 `make -j8` 利用 8 核并行编译，约 30-60 秒完成