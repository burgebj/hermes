---
sidebar_position: 2
title: "安装"
description: "在 Linux、macOS、WSL2、原生 Windows（早期测试版）或通过 Termux 的 Android 上安装 Hermes Agent"
---

# 安装

通过一行安装脚本，在两分钟内让 Hermes Agent 运行起来。

## 快速安装

### Linux / macOS / WSL2

```bash
curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash
```

### Windows（原生 PowerShell）— 早期测试版

:::warning Early BETA
原生 Windows 支持仍处于 **早期测试版**。它可以在常见路径下安装并正常工作，但尚未像 POSIX 安装器那样经过广泛实测。遇到问题请 [提交 issue](https://github.com/NousResearch/hermes-agent/issues)。若想在 Windows 上获得最可靠的体验，建议在 **WSL2** 中使用上面的 Linux/macOS 一行脚本。
:::

打开 PowerShell 并运行：

```powershell
irm https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.ps1 | iex
```

安装程序会处理 **所有** 内容：`uv`、Python 3.11、Node.js 22、`ripgrep`、`ffmpeg`，以及便携的 Git Bash（PortableGit —— 包含 `bash.exe` 与完整的 POSIX 工具链，Hermes 用于 shell 命令；在 32 位 Windows 上安装程序会回退到 MinGit，缺少 bash，终端工具 / agent-browser 功能将被禁用）。它会把仓库克隆到 `%LOCALAPPDATA%\hermes\hermes-agent`，创建 virtualenv，并将 `hermes` 加入 **用户 PATH**。安装后请重新打开终端（或新开一个 PowerShell 窗口）以使 PATH 更新。

**Git 的处理方式：**
1. 若系统已有 `git` 并在 PATH 中，安装程序直接使用该安装。
2. 否则会下载便携的 **PortableGit**（约 50 MB，来自官方 `git-for-windows` 发布页）并解压到 `%LOCALAPPDATA%\hermes\git`。无需管理员权限。完全隔离——不会影响系统中任何 Git 安装（即使已损坏）。（在 32 位 Windows 上会回退到 MinGit，因为 PortableGit 只提供 64 位和 ARM64 资产，依赖 bash 的 Hermes 功能在 32 位主机上将不可用。）

**为何不使用 winget？** 早期设计会通过 `winget install Git.Git` 自动安装 Git，但当系统中已有部分或损坏的 Git 时 winget 往往失败——恰恰是用户最需要安装程序正常工作的时刻。便携 Git 方案规避了 winget、Windows 安装程序注册表以及任何系统 Git。若 Hermes 自带的 Git 安装出现问题，只需 `Remove-Item %LOCALAPPDATA%\hermes\git` 并重新运行安装脚本——对系统毫无影响，也无需卸载烦恼。

安装程序还会设置 `HERMES_GIT_BASH_PATH` 指向相应的 `bash.exe`，从而在全新 shell 中确定性地定位它。

如果你更倾向使用 WSL2，上述 Linux 安装脚本同样可以在 WSL2 中运行；原生 Windows 与 WSL 安装可以并存（原生数据位于 `%LOCALAPPDATA%\hermes`，WSL 数据位于 `~/.hermes`）。

### Android / Termux

Hermes 现在也提供了适配 Termux 的安装路径：

```bash
curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash
```

安装程序会自动检测 Termux 并切换到经过测试的 Android 流程：
- 使用 Termux `pkg` 安装系统依赖（`git`、`python`、`nodejs`、`ripgrep`、`ffmpeg`、构建工具）
- 通过 `python -m venv` 创建 virtualenv
- 自动导出 `ANDROID_API_LEVEL` 以构建 Android wheel
- 首选 `.[termux-all]` 扩展；若编译失败会回退到较小的 `.[termux]`，最终回退到基础安装
- 默认跳过未经测试的浏览器 / WhatsApp 引导

如果想查看更完整的步骤，请参考专门的 [Termux 指南](./termux.md)。

:::note Windows 特性兼容性（早期测试版）
原生 Windows 仍处于 **早期测试版**。除浏览器仪表盘聊天终端外，其他功能均可在 Windows 本地运行：
- **CLI (`hermes chat`、`hermes setup`、`hermes gateway` …)** — 原生，使用默认终端
- **网关（Telegram、Discord、Slack 等）** — 原生，作为后台 PowerShell 进程运行
- **Cron 调度器** — 原生
- **浏览器工具** — 原生（通过 Node.js 的 Chromium）
- **MCP 服务器** — 原生（同时支持 stdio 与 HTTP 传输）
- **仪表盘 `/chat` 终端窗格** — **仅限 WSL2**（使用 POSIX PTY；原生 Windows 暂无等价实现）。仪表盘的其他部分（会话、任务、指标）均可原生运行，仅嵌入的 PTY 终端标签受限。

如果遇到编码相关的 bug，可在环境中设置 `HERMES_DISABLE_WINDOWS_UTF8=1`，以回退到传统的 cp1252 stdio 路径（便于定位问题）。
:::

### 安装程序的工作内容

安装程序全自动完成所有依赖（Python、Node.js、ripgrep、ffmpeg）、仓库克隆、virtualenv 创建、全局 `hermes` 命令配置以及 LLM 提供商的初始化。完成后即可开始聊天。

#### 安装布局

实际文件放置位置取决于是普通用户安装还是 root 安装：

| 安装方式 | 代码所在路径 | `hermes` 二进制 | 数据目录 |
|---|---|---|---|
| 普通用户（非 root） | `~/.hermes/hermes-agent/` | `~/.local/bin/hermes`（符号链接） | `~/.hermes/` |
| root 模式（`sudo curl … | sudo bash`） | `/usr/local/lib/hermes-agent/` | `/usr/local/bin/hermes` | `/root/.hermes/`（或 `$HERMES_HOME`） |

root 模式采用 **FHS 布局**（`/usr/local/lib/...`、`/usr/local/bin/hermes`），与 Linux 上其他系统级开发工具的放置位置一致。适用于共享机器的全局部署。每个用户的配置（认证信息、技能、会话等）仍然位于各自的 `~/.hermes/` 或显式的 `HERMES_HOME` 下。

### 安装后

重新加载 shell 并开始聊天：

```bash
source ~/.bashrc   # 或: source ~/.zshrc
hermes             # 开始聊天！
```

以后若需单独配置某些设置，可使用相应命令：

```bash
hermes model          # 选择你的 LLM 提供商和模型
hermes tools          # 配置启用的工具
hermes gateway setup  # 设置消息平台
hermes config set     # 设置单个配置项
hermes setup          # 或运行完整的设置向导，一次性配置所有内容
```

---

## 前置条件

唯一的前置条件是 **Git**。安装程序会自动处理其余所有依赖：
- **uv**（高速 Python 包管理器）
- **Python 3.11**（通过 uv，无需 sudo）
- **Node.js v22**（用于浏览器自动化和 WhatsApp 桥接）
- **ripgrep**（快速文件搜索）
- **ffmpeg**（音频格式转换，供 TTS 使用）

:::info
你 **不需要** 手动安装 Python、Node.js、ripgrep 或 ffmpeg。安装程序会检测缺失项并自动安装。只要系统中能运行 `git --version` 即可。
:::

:::tip Nix 用户
如果你使用 Nix（在 NixOS、macOS 或 Linux 上），项目提供了专门的 Nix flake、声明式 NixOS 模块以及可选的容器模式。详见 **[Nix & NixOS 设置](./nix-setup.md)** 指南。
:::

---

## 手动 / 开发者安装

如果你想克隆仓库并从源码安装——例如进行贡献、切换到特定分支或完全控制 virtualenv——请参阅贡献指南中的 [开发者设置](../developer-guide/contributing.md#development-setup) 部分。

---

## 非 sudo / 系统服务用户安装

在非特权用户（例如用于 systemd 服务的 `hermes` 用户，或任何没有 `sudo` 权限的用户）下运行 Hermes 是受支持的。唯一真正需要 root 权限的步骤是 Playwright 的 `--with-deps`，它会通过 `apt` 安装 Chromium 所需的共享库（`libnss3`、`libxkbcommon` 等）。安装程序会检测是否可以使用 sudo，并在不可用时优雅降级——它会把 Chromium 二进制放入该服务用户自己的 Playwright 缓存，并打印出管理员需要单独执行的命令。

**在 Debian/Ubuntu 上的推荐做法：**

1. **一次性，以拥有 sudo 的管理员用户**，为 Chromium 安装系统库：
   ```bash
   sudo npx playwright install-deps chromium
   ```
   （可以在任意目录执行，`npx` 会即时下载 Playwright。）

2. **以非特权服务用户** 运行常规安装脚本。它会检测缺少 sudo，跳过 `--with-deps`，并把 Chromium 安装到用户本地的 Playwright 缓存中：
   ```bash
   curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash
   ```

   若想完全跳过 Playwright 步骤（例如只运行无头模式，不需要浏览器自动化），可以传入 `--skip-browser`：
   ```bash
   curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash -s -- --skip-browser
   ```

3. **让 `hermes` 在服务用户的 shell 中可用。** 安装程序会将启动器写入 `~/.local/bin/hermes`。系统服务账户的 PATH 通常不包含此目录。可以：
   - 将其加入用户的环境配置；
   - 或者在系统位置创建符号链接。
   ```bash
   # 方案 A — 添加到服务用户的 profile
   echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc

   # 方案 B — 创建全局软链接（需要管理员）
   sudo ln -s /home/hermes/.hermes/hermes-agent/venv/bin/hermes /usr/local/bin/hermes
   ```

4. **验证：**运行 `hermes doctor` 应当顺利。如果出现 `ModuleNotFoundError: No module named 'dotenv'`，说明你正在使用仓库中的 `hermes` 脚本（`~/.hermes/hermes-agent/hermes`）而不是 virtualenv 启动器（`~/.hermes/hermes-agent/venv/bin/hermes`），请修正第 3 步。

相同模式同样适用于 Arch（installer 使用 pacman 并具备相同的 sudo 检测逻辑）、Fedora/RHEL、openSUSE——这些发行版根本不支持 `--with-deps`，因此管理员始终需要自行安装系统库。对应的 `dnf`/`zypper` 命令会由安装程序打印。

---

## 故障排查

| 问题 | 解决方案 |
|------|----------|
| `hermes: command not found` | 重新加载 shell（`source ~/.bashrc`）或检查 PATH |
| `API key not set` | 运行 `hermes model` 配置提供商，或 `hermes config set OPENROUTER_API_KEY your_key` |
| 更新后缺少配置 | 运行 `hermes config check` 再 `hermes config migrate` |

如需更详细的诊断信息，运行 `hermes doctor` ——它会准确指出缺失项并提供修复方案。
