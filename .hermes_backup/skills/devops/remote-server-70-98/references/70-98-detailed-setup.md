# 10.10.70.98 (oem98) — NVIDIA RTX PRO 6000 Blackwell Server Edition Detailed Setup

## Installed Software (2026-05-18)

| Package | Version | Notes |
|---------|---------|-------|
| CUDA Driver | 13.2 (595.58.03) | nvidia-driver-595-open |
| CUDA Toolkit (nvcc) | 13.2.78 | cuda-nvcc-13-2 |
| Python | 3.12.13 | From deadsnakes PPA |
| python3.12-dev | 3.12.13 | Headers for C extension builds |
| NCCL | 2.30.4-1+cuda13.2 | libnccl2 + libnccl-dev |
| build-essential | 12.9ubuntu3 | g++, make, etc. |

## Python venv: /data/venvs/vllm-ds4/

Created on 2026-05-18 to match 70.88's /data/venvs/vllm-ds4/ setup.
- 183 total packages (86 matching 70.88's freeze list)
- Size: 7.4 GB

### Key pip packages

| Package | Version | Purpose |
|---------|---------|---------|
| torch | 2.11.0+cu130 | Core ML (CUDA 13.0 compat) |
| torchvision | 0.26.0+cu130 | Vision |
| torchaudio | 2.11.0+cu130 | Audio |
| transformers | 5.8.0 | HuggingFace models |
| huggingface_hub | 1.13.0 | Model hub |
| flashinfer | 0.6.8.post1 | Flash attention kernels |
| xgrammar | 0.2.0 | Grammar-guided generation |
| outlines_core | 0.2.14 | Structured output |
| llguidance | 1.3.0 | LLM guidance |
| lm-format-enforcer | 0.11.3 | Format enforcer |
| fastapi | 0.136.1 | API serving |
| uvicorn | 0.46.0 | ASGI server |
| tokenizers | 0.22.2 | Tokenizers |
| sentencepiece | 0.2.1 | Tokenizers |
| tiktoken | 0.12.0 | OpenAI tokenizer |
| compressed-tensors | 0.15.0.1 | Model compression |
| vllm | 0.1.dev1+gb709b75b4 (ds4-sm120) | Editable install from copied fork |
| cmake | 4.3.2 | From pip package, set as system default |
| ninja-build | 1.10.1 | System package |

## Build Notes

### Initial installation encountered these issues (resolved):

1. **`pyproject.toml` license validation** — setuptools 70.2.0 was too old. Upgraded to setuptools 80.10.2 to match vLLM's build-system requirement (`setuptools>=77.0.3,<81.0.0`).
2. **CUDA_nvrtc_LIBRARY not found** — needed `cuda-nvrtc-13-2` and `cuda-nvrtc-dev-13-2`.
3. **cublas_v2.h / cusparse.h not found** — needed `cuda-libraries-dev-13-2` meta-package.
4. **cmake 3.22.1 too old** — vLLM requires cmake >= 3.26. Installed pip's `cmake` (4.3.2) and set it as system default via `update-alternatives`.
5. **Ninja not installed** — needed `ninja-build` system package.
6. **numba version mismatch** — requirements listed `numba==0.65.0` but pip installed `0.65.1`. Pip resolved this during the editable install (downgraded to 0.65.0).

### Note on CUDA version mismatch

70.88 uses CUDA 13.0 (torch compiled for `+cu130`). 70.98 has CUDA 13.2 driver + nvcc. This works because CUDA 13.x is backward compatible — torch 2.11.0+cu130 runs fine on CUDA 13.2 runtime.

### DeepSeek-V4-Pro 2-Node Benchmark (TP=8, PP=2, EP=8)

| Metric | Cache 0% (c32) | Cache 50% (c32) | Cache 100% (c32) | Cache 0% (c64) | Cache 40% (c64) | Cache 80% (c64) |
|-------|:---:|:---:|:---:|:---:|:---:|:---:|
| Wall time | 199.8s | 130.6s | 77.9s | 255.5s | 259.0s | 178.1s |
| Total tok/s | 423.9 | 643.3 | 1079.8 | 663.2 | 651.2 | 938.1 |
| Output tok/s | 80.1 | 122.5 | 203.6 | 125.3 | 123.5 | 179.7 |
| P50 latency | 193.6s | 127.5s | 77.6s | 238.9s | 248.7s | 173.7s |
| P99 latency | 199.7s | 130.6s | 77.9s | 255.3s | 258.9s | 178.0s |

### Not installed (still needs setup)

- vLLM fork (jasl/vllm ds4-sm120)
- Docker
- NVIDIA Container Toolkit
- nccl-tests
