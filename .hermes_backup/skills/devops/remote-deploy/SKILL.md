---
name: remote-deploy
description: Deploy code, git repos, and files to a remote machine via SSH — set up passwordless login, transfer repos with rsync/git, check remote environment.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [ssh, rsync, deploy, remote, git, devops]
    related_skills: [github-auth, github-repo-management]
---

# Remote Deploy

Deploy code, git repositories, and files to a remote machine over SSH. Covers SSH passwordless setup via `ssh-copy-id`, git clone + rsync workaround for slow/broken connections, and remote environment checks.

## When to Use

Use this skill when the user wants to:
- Set up passwordless SSH login to a remote machine (`ssh-copy-id`)
- Clone a git repo to a remote machine (especially when direct `git clone` over SSH times out or fails)
- Transfer files or directories to a remote machine
- Check what software/libraries are installed on a remote machine (NCCL, CUDA, Python, etc.)
- Deploy code from the local machine to a remote dev/test server

## Workflow

### Step 1: Set up passwordless SSH login

Check if passwordless login already works:

```bash
ssh -o PasswordAuthentication=no user@host "echo connected" 2>&1
```

If it returns "connected", skip ahead. Otherwise, set it up:

**Check if ssh-askpass is available (needed for interactive password prompt):**

```bash
which ssh-askpass 2>/dev/null || echo "not installed"
```

If `ssh-askpass` is not installed and the environment has no interactive TTY (common in agent sessions), standard `ssh-copy-id` will fail with `ssh_askpass: exec(/usr/bin/ssh-askpass): No such file or directory`.

**Solutions:**

A) **First accept the host key, then tell user to run ssh-copy-id manually:**
```bash
ssh -o StrictHostKeyChecking=accept-new user@host "echo host key added"
```
Then tell the user:
```
ssh-copy-id user@host
```
They'll be prompted for their password once.

B) **Use sshpass (if you have the password):**
```bash
sshpass -p 'PASSWORD' ssh-copy-id -o StrictHostKeyChecking=accept-new user@host
```
(Only use if password is provided by the user.)

C) **Manually append the public key to remote authorized_keys:**
If you can SSH in with a password interactively, pipe the key:
```bash
cat ~/.ssh/id_rsa.pub | ssh user@host "mkdir -p ~/.ssh && cat >> ~/.ssh/authorized_keys"
```

### Step 2: Transfer a git repo to remote

**Option A: Direct clone on remote (fast connection)**
```bash
ssh user@host "mkdir -p ~/work && cd ~/work && git clone https://github.com/owner/repo.git"
```

**Option B: Clone locally first, then rsync (slow/unreliable remote)**
```bash
# 1. Clone locally
git clone https://github.com/owner/repo.git /tmp/repo-name

# 2. Rsync to remote (preserves .git, full history)
rsync -av /tmp/repo-name/ user@host:~/work/repo-name/

# 3. Clean up local temp
rm -rf /tmp/repo-name
```

**Option C: Transfer an existing local directory**
```bash
rsync -av /local/path/ user@host:~/remote/path/
```

### Step 3: Check remote environment

**NCCL check — system level vs PyTorch-bundled:**

NCCL can be installed in two ways:
- **System-level** (`libnccl2` / `libnccl-dev` via apt) — needed for compiling C/CUDA programs like nccl-tests
- **PyTorch-bundled** — PyTorch ships its own NCCL library inside conda/pip environments, which is what Python programs use

```bash
# System-level NCCL
ssh user@host "
  echo '=== ldconfig ==='; ldconfig -p 2>/dev/null | grep -i nccl;
  echo '=== dpkg nccl ==='; dpkg -l 2>/dev/null | grep -i 'libnccl';
  echo '=== find nccl libs ==='; find /usr /usr/local /opt -name '*nccl*' -o -name '*NCCL*' 2>/dev/null;
  echo '=== nccl header ==='; find /usr -name 'nccl.h' 2>/dev/null
"
```

**PyTorch-bundled NCCL** (useful even when system-level nccl is absent):
```bash
# Check PyTorch NCCL in a specific conda env
ssh user@host "/path/to/conda/envs/ENV_NAME/bin/python -c 'import torch; print(torch.cuda.nccl.version())'"

# Or find which conda envs have torch with NCCL
ssh user@host "find /home/user/miniconda3 -name 'libnccl*' 2>/dev/null"
```

If the system-level check shows nothing but `python -c "import torch; print(torch.cuda.nccl.version())"` works, NCCL is available through PyTorch's bundled copy — sufficient for Python multi-GPU training but not for compiling C/CUDA programs like nccl-tests. To compile those, install system NCCL: `sudo apt-get install -y libnccl2 libnccl-dev`.

**CUDA check:**
```bash
ssh user@host "nvidia-smi 2>&1 | head -5; nvcc --version 2>&1"
```

**General package check:**
```bash
ssh user@host "dpkg -l | grep -i PACKAGE_NAME"
```

## Pitfalls

- **ssh-askpass missing in agent environments** — Standard `ssh-copy-id` fails silently when there's no GUI askpass and no interactive TTY. Always test with `-o PasswordAuthentication=no` first.
- **Host key verification** — Always use `-o StrictHostKeyChecking=accept-new` on first connection to avoid blocking the script.
- **rsync destination path** — rsync will NOT auto-create missing parent directories on the remote. Always `ssh user@host "mkdir -p ~/work/repo"` first.
- **rsync trailing slash** — `rsync -av src/ dest/` copies contents *into* dest. `rsync -av src dest/` copies the `src` directory itself into dest. The trailing slash matters.

## Verification

After transfer, verify the files are there:

```bash
ssh user@host "ls -la ~/work/repo-name && cd ~/work/repo-name && git log --oneline -1"
```
