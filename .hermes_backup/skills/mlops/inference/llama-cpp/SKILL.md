---
name: llama-cpp
description: llama.cpp local GGUF inference + HF Hub model discovery.
version: 2.1.2
author: Orchestra Research
license: MIT
dependencies: [llama-cpp-python>=0.2.0]
metadata:
  hermes:
    tags: [llama.cpp, GGUF, Quantization, Hugging Face Hub, CPU Inference, Apple Silicon, Edge Deployment, AMD GPUs, Intel GPUs, NVIDIA, URL-first]
---

# llama.cpp + GGUF

Use this skill for local GGUF inference, quant selection, or Hugging Face repo discovery for llama.cpp.

## When to use

- Run local models on CPU, Apple Silicon, CUDA, ROCm, or Intel GPUs
- Find the right GGUF for a specific Hugging Face repo
- Build a `llama-server` or `llama-cli` command from the Hub
- Search the Hub for models that already support llama.cpp
- Enumerate available `.gguf` files and sizes for a repo
- Decide between Q4/Q5/Q6/IQ variants for the user's RAM or VRAM
- **Build llama.cpp from source** with GPU (CUDA/ROCm/Metal) support
- **Convert a Hugging Face model** to GGUF format
- **Assess whether a model architecture is supported** by llama.cpp, and what it would take to add support
- **Handle network-restricted environments** (China/air-gapped) — use mirrors for git clone and pip

## Model Discovery workflow

Prefer URL workflows before asking for `hf`, Python, or custom scripts.

1. Search for candidate repos on the Hub:
   - Base: `https://huggingface.co/models?apps=llama.cpp&sort=trending`
   - Add `search=<term>` for a model family
   - Add `num_parameters=min:0,max:24B` or similar when the user has size constraints
2. Open the repo with the llama.cpp local-app view:
   - `https://huggingface.co/<repo>?local-app=llama.cpp`
3. Treat the local-app snippet as the source of truth when it is visible:
   - copy the exact `llama-server` or `llama-cli` command
   - report the recommended quant exactly as HF shows it
4. Read the same `?local-app=llama.cpp` URL as page text or HTML and extract the section under `Hardware compatibility`:
   - prefer its exact quant labels and sizes over generic tables
   - keep repo-specific labels such as `UD-Q4_K_M` or `IQ4_NL_XL`
   - if that section is not visible in the fetched page source, say so and fall back to the tree API plus generic quant guidance
5. Query the tree API to confirm what actually exists:
   - `https://huggingface.co/api/models/<repo>/tree/main?recursive=true`
   - keep entries where `type` is `file` and `path` ends with `.gguf`
   - use `path` and `size` as the source of truth for filenames and byte sizes
   - separate quantized checkpoints from `mmproj-*.gguf` projector files and `BF16/` shard files
   - use `https://huggingface.co/<repo>/tree/main` only as a human fallback
6. If the local-app snippet is not text-visible, reconstruct the command from the repo plus the chosen quant:
   - shorthand quant selection: `llama-server -hf <repo>:<QUANT>`
   - exact-file fallback: `llama-server --hf-repo <repo> --hf-file <filename.gguf>`
7. Only suggest conversion from Transformers weights if the repo does not already expose GGUF files.

## Quick start

### Install llama.cpp

```bash
# macOS / Linux (simplest)
brew install llama.cpp
```

```bash
winget install llama.cpp
```

```bash
# Linux / general — from source
git clone https://github.com/ggml-org/llama.cpp
cd llama.cpp
cmake -B build
cmake --build build --config Release
```

### Build from source with GPU support

```bash
# Prerequisites
# - CUDA Toolkit (nvcc + cuBLAS) or ROCm
# - cmake, make, gcc/g++

# CUDA build
git clone https://github.com/ggml-org/llama.cpp
cd llama.cpp
mkdir -p build && cd build
cmake .. -DGGML_CUDA=ON -DCMAKE_BUILD_TYPE=Release
make -j$(nproc)
# Binaries in build/bin/: llama-cli, llama-server

# If cmake fails with "Target 'ggml-cuda' links to target 'CUDA::cublas' but the
# target was not found":
#   1. Install cuda-toolkit-<ver> via apt (e.g. cuda-toolkit-13-0) for full CUDA
#   2. OR use conda/PyTorch's bundled cuBLAS:
#      export CMAKE_PREFIX_PATH=$CONDA_PREFIX/lib/python3.x/site-packages/nvidia/cu13:$CMAKE_PREFIX_PATH
#      cmake .. -DGGML_CUDA=ON -DCUDAToolkit_ROOT=/usr/local/cuda
#   3. OR install cublas via the NVIDIA repo: sudo apt install cuda-toolkit-13-0

# ROCm / AMD GPU build
cmake .. -DGGML_HIPBLAS=ON -DCMAKE_BUILD_TYPE=Release

# Metal / Apple Silicon build
cmake .. -DGGML_METAL=ON -DCMAKE_BUILD_TYPE=Release

# Verify
./build/bin/llama-cli -h

# Verify GPU detection
./build/bin/llama-cli -h 2>&1 | grep -i "device\|gpu\|cuda"
```

### China network — use mirrors

When GitHub is unreachable (common in China/air-gapped environments), try these mirrors in order:

```bash
# Git clone via proxy (when github.com is unreachable)
# Try these in order, some may be blocked or slow depending on ISP:

# 1. gitclone.com — works for many but can be slow
git clone --depth 1 https://gitclone.com/github.com/ggml-org/llama.cpp.git

# 2. githubfast.com — faster but may timeout on large repos
git clone --depth 1 https://githubfast.com/ggml-org/llama.cpp.git

# 3. Gitee mirror (check if it exists first)
curl -s --connect-timeout 5 https://gitee.com/mirrors/llama.cpp | grep -q 'repo' && \
  git clone --depth 1 https://gitee.com/mirrors/llama.cpp.git

# 4. If all git clones fail, fall back to tarball download
curl -sL --connect-timeout 30 \
  -o /tmp/llamacpp.tar.gz \
  'https://githubfast.com/ggml-org/llama.cpp/archive/refs/heads/master.tar.gz' && \
  mkdir -p ~/work/llama.cpp && \
  tar -xzf /tmp/llamacpp.tar.gz -C ~/work/llama.cpp --strip-components=1

# 5. Last resort: download tarball on a machine with GitHub access and scp/rsync over
#    On accessible machine:
#    wget https://github.com/ggml-org/llama.cpp/archive/refs/heads/master.tar.gz
#    scp master.tar.gz user@server:~/work/
#    On server: tar -xzf ~/work/master.tar.gz -C ~/work/llama.cpp --strip-components=1

# Diagnosis: check which mirrors are reachable
for url in \
  "https://github.com" \
  "https://gitclone.com" \
  "https://githubfast.com" \
  "https://gitee.com" \
  "https://hf-mirror.com"; do
  code=$(curl -s -o /dev/null -w '%{http_code}' --connect-timeout 5 "$url" 2>/dev/null || echo '000')
  echo "$code $url"
done

# pip with Tsinghua mirror
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple --default-timeout=60 <package>

# Enable mirror permanently
pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
```

### Run directly from the Hugging Face Hub

```bash
llama-cli -hf bartowski/Llama-3.2-3B-Instruct-GGUF:Q8_0
```

```bash
llama-server -hf bartowski/Llama-3.2-3B-Instruct-GGUF:Q8_0
```

### Run an exact GGUF file from the Hub

Use this when the tree API shows custom file naming or the exact HF snippet is missing.

```bash
llama-server \
    --hf-repo microsoft/Phi-3-mini-4k-instruct-gguf \
    --hf-file Phi-3-mini-4k-instruct-q4.gguf \
    -c 4096
```

### OpenAI-compatible server check

```bash
curl http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "Write a limerick about Python exceptions"}
    ]
  }'
```

## Python bindings (llama-cpp-python)

`pip install llama-cpp-python` (CUDA: `CMAKE_ARGS="-DGGML_CUDA=on" pip install llama-cpp-python --force-reinstall --no-cache-dir`; Metal: `CMAKE_ARGS="-DGGML_METAL=on" ...`).

### Basic generation

```python
from llama_cpp import Llama

llm = Llama(
    model_path="./model-q4_k_m.gguf",
    n_ctx=4096,
    n_gpu_layers=35,     # 0 for CPU, 99 to offload everything
    n_threads=8,
)

out = llm("What is machine learning?", max_tokens=256, temperature=0.7)
print(out["choices"][0]["text"])
```

### Chat + streaming

```python
llm = Llama(
    model_path="./model-q4_k_m.gguf",
    n_ctx=4096,
    n_gpu_layers=35,
    chat_format="llama-3",   # or "chatml", "mistral", etc.
)

resp = llm.create_chat_completion(
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "What is Python?"},
    ],
    max_tokens=256,
)
print(resp["choices"][0]["message"]["content"])

# Streaming
for chunk in llm("Explain quantum computing:", max_tokens=256, stream=True):
    print(chunk["choices"][0]["text"], end="", flush=True)
```

### Embeddings

```python
llm = Llama(model_path="./model-q4_k_m.gguf", embedding=True, n_gpu_layers=35)
vec = llm.embed("This is a test sentence.")
print(f"Embedding dimension: {len(vec)}")
```

You can also load a GGUF straight from the Hub:

```python
llm = Llama.from_pretrained(
    repo_id="bartowski/Llama-3.2-3B-Instruct-GGUF",
    filename="*Q4_K_M.gguf",
    n_gpu_layers=35,
)
```

## Choosing a quant

Use the Hub page first, generic heuristics second.

- Prefer the exact quant that HF marks as compatible for the user's hardware profile.
- For general chat, start with `Q4_K_M`.
- For code or technical work, prefer `Q5_K_M` or `Q6_K` if memory allows.
- For very tight RAM budgets, consider `Q3_K_M`, `IQ` variants, or `Q2` variants only if the user explicitly prioritizes fit over quality.
- For multimodal repos, mention `mmproj-*.gguf` separately. The projector is not the main model file.
- Do not normalize repo-native labels. If the page says `UD-Q4_K_M`, report `UD-Q4_K_M`.

## Extracting available GGUFs from a repo

When the user asks what GGUFs exist, return:

- filename
- file size
- quant label
- whether it is a main model or an auxiliary projector

Ignore unless requested:

- README
- BF16 shard files
- imatrix blobs or calibration artifacts

Use the tree API for this step:

- `https://huggingface.co/api/models/<repo>/tree/main?recursive=true`

For a repo like `unsloth/Qwen3.6-35B-A3B-GGUF`, the local-app page can show quant chips such as `UD-Q4_K_M`, `UD-Q5_K_M`, `UD-Q6_K`, and `Q8_0`, while the tree API exposes exact file paths such as `Qwen3.6-35B-A3B-UD-Q4_K_M.gguf` and `Qwen3.6-35B-A3B-Q8_0.gguf` with byte sizes. Use the tree API to turn a quant label into an exact filename.

## Search patterns

Use these URL shapes directly:

```text
https://huggingface.co/models?apps=llama.cpp&sort=trending
https://huggingface.co/models?search=<term>&apps=llama.cpp&sort=trending
https://huggingface.co/models?search=<term>&apps=llama.cpp&num_parameters=min:0,max:24B&sort=trending
https://huggingface.co/<repo>?local-app=llama.cpp
https://huggingface.co/api/models/<repo>/tree/main?recursive=true
https://huggingface.co/<repo>/tree/main
```

## Output format

When answering discovery requests, prefer a compact structured result like:

```text
Repo: <repo>
Recommended quant from HF: <label> (<size>)
llama-server: <command>
Other GGUFs:
- <filename> - <size>
- <filename> - <size>
Source URLs:
- <local-app URL>
- <tree API URL>
```

## Converting Hugging Face models to GGUF

### Basic conversion workflow

```bash
# Prerequisites
conda activate my_env  # or source venv/bin/activate
pip install -r requirements.txt
pip install -e gguf-py   # install the gguf Python package

# Convert a supported HF model
python convert_hf_to_gguf.py /path/to/hf/model/dir \
    --outtype f16 \
    --outfile model-f16.gguf

# Quantize to Q4_K_M
./build/bin/llama-quantize \
    model-f16.gguf \
    model-Q4_K_M.gguf \
    Q4_K_M
```

### Dependencies

```bash
# Core deps
pip install torch safetensors sentencepiece numpy

# All llama.cpp Python script deps
pip install -r requirements.txt

# gguf Python package (needed by convert script)
pip install -e gguf-py

# China mirror
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple --default-timeout=60 \
    torch safetensors sentencepiece
```

### Checking if a model is supported

```bash
# 1. Try conversion — the script prints the error if unsupported
python convert_hf_to_gguf.py /path/to/model

# 2. Check registered architectures in the convert script
grep -n '@ModelBase.register' convert_hf_to_gguf.py | grep -i '<partial model name>'

# 3. Check the C++ side for architecture support
grep -n 'DEEPSEEK\|LLM_ARCH' src/llama-arch.h

# 4. Check the gguf-py constants for architecture enum
grep -n 'DEEPSEEK\|deepseek' gguf-py/gguf/constants.py

# 5. Search upstream commits for pending support
git log --all --oneline --grep='<model name>' | head -10
git fetch upstream && git branch -r | grep -i '<model name>'
```

### Assessing feasibility for an unsupported model

When `convert_hf_to_gguf.py` says "Model X is not supported", assess what's needed:

1. **Check the model config** (`config.json`):
   ```bash
   python3 -c "import json; c=json.load(open('config.json')); print('Arch:', c.get('architectures'), 'Type:', c.get('model_type'))"
   ```
   - If `model_type` matches a known architecture (e.g. `deepseek_v4` vs existing `deepseek_v2`), it may be a derivative

2. **Check weight key naming** — compare with existing supported models:
   ```bash
   python3 -c "
   import safetensors, os
   model_dir = '.'
   files = sorted([f for f in os.listdir(model_dir) if f.endswith('.safetensors')])
   with safetensors.safe_open(os.path.join(model_dir, files[0]), framework='pt') as f:
       for k in sorted(f.keys())[:20]: print(k)
   "
   ```
   - **MLA attention**: keys like `wq_a`, `wq_b`, `wkv`, `wo_a`, `wo_b` indicate Multi-head Latent Attention. Already supported by DeepSeekV2 class.
   - **Standard attention**: keys like `q_proj`, `k_proj`, `v_proj`, `o_proj` — widely supported.
   - **MoE FFN**: keys like `experts.N.w1/w2/w3` + `gate.weight` — supported by DeepSeekV2 and Mixtral classes.

3. **Check quantization format**:
   ```bash
   python3 -c "
   import json
   c = json.load(open('config.json'))
   qc = c.get('quantization_config', {})
   print('Quant method:', qc.get('quant_method'))
   print('Weight dtype:', qc.get('fmt'))
   print('Weight block size:', qc.get('weight_block_size'))
   "
   ```
   - **FP8** (`e4m3` / `fp8`): llama.cpp supports dequantization from FP8 in the convert script.
   - **FP4** (`fp4` / `nvfp4`): llama.cpp has experimental NVFP4 support (`_is_nvfp4` flag). May need converter work.
   - **INT4/INT8/AWQ/GPTQ**: llama.cpp's `convert_hf_to_gguf.py` has `dequant_simple()` for block-wise dequant.
   - **BF16/FP16 weights**: straightforward, no special handling needed.

4. **Check for architectural features that may not be supported**:
   - MLA (Multi-head Latent Attention) — DeepSeekV2 already supports this
   - MTP (Multi-Token Prediction) — skip via `skip_mtp = True`
   - Hash layers / indexer / compressor — these are DeepSeekV4-specific and likely NOT supported
   - Expert FP4 dtype — llama.cpp's NVFP4 support may be incomplete
   - SwiGLU limit / routed scaling — might need C++ side changes

5. **Estimate if adding support is feasible**:
   - **Quick win (1-2 hours)**: Model is architecturally identical to a supported model, just needs `@ModelBase.register("NewName")` added to the existing class.
   - **Moderate work (1-2 days)**: New architecture but uses known building blocks (MLA + MoE). Needs new Python class + C++ model code.
   - **Major work (1+ weeks)**: Novel architecture with custom ops (new attention mechanism, exotic quantization). Needs both converter and C++ inference code.

### Quick architecture registration (when model is a derivative)

If the model is structurally identical to a supported one but uses a different `model_type` name:

```bash
# Backup and edit convert_hf_to_gguf.py
cp convert_hf_to_gguf.py convert_hf_to_gguf.py.bak
# Find the parent class registration and add the new model name
# e.g. for DeepSeekV4 that's structurally similar to DeepSeekV2:
# @ModelBase.register(
#     "DeepseekV2ForCausalLM",
#     "DeepseekV3ForCausalLM",
#     "DeepseekV4ForCausalLM",   <-- add this line
# )
```

Then also check whether the C++ side (`src/llama-*.h`, `src/llama-model-*.cpp`) needs an architecture entry. If it uses `LLM_ARCH_DEEPSEEK2` internally via the Python class setting `model_arch = gguf.MODEL_ARCH.DEEPSEEK2`, no C++ changes are needed.

### Known model support caveats (as of 2026-04)

| Model | `model_type` | Support status | Risk factors |
|-------|-------------|----------------|--------------|
| DeepSeekV2/V3 | `deepseek_v2`, `deepseek_v3` | ✅ Supported | — |
| **DeepSeekV4** | **`deepseek_v4`** | ❌ **Not yet** | FP4 weights, MTP heads, hash layers, compressor, indexer — all new. Would need significant C++ work. |
| Qwen3 | `qwen3` | Depends on variant | Check if MLA or standard attention |

### Troubleshooting conversion

**"Model X is not supported"**:
- The architecture is not registered in `convert_hf_to_gguf.py`
- Follow the assessment flow above to decide if it's a quick registration or a major porting effort

**"safetensors not found"**:
```bash
pip install safetensors
```

**"ModuleNotFoundError: No module named 'transformers'"**:
```bash
pip install transformers
```

**"Error loading model config" + Transformers doesn't recognize model_type**:
- The HF `transformers` library doesn't know about this model yet
- The convert script falls back to `config.json` for its own parsing
- If the script still fails, you may need to bypass `AutoConfig` loading

## References

- **[hub-discovery.md](references/hub-discovery.md)** - URL-only Hugging Face workflows, search patterns, GGUF extraction, and command reconstruction
- **[advanced-usage.md](references/advanced-usage.md)** — speculative decoding, batched inference, grammar-constrained generation, LoRA, multi-GPU, custom builds, benchmark scripts
- **[quantization.md](references/quantization.md)** — quant quality tradeoffs, when to use Q4/Q5/Q6/IQ, model size scaling, imatrix
- **[server.md](references/server.md)** — direct-from-Hub server launch, OpenAI API endpoints, Docker deployment, NGINX load balancing, monitoring
- **[optimization.md](references/optimization.md)** — CPU threading, BLAS, GPU offload heuristics, batch tuning, benchmarks
- **[troubleshooting.md](references/troubleshooting.md)** — install/convert/quantize/inference/server issues, Apple Silicon, debugging

## Resources

- **GitHub**: https://github.com/ggml-org/llama.cpp
- **Hugging Face GGUF + llama.cpp docs**: https://huggingface.co/docs/hub/gguf-llamacpp
- **Hugging Face Local Apps docs**: https://huggingface.co/docs/hub/main/local-apps
- **Hugging Face Local Agents docs**: https://huggingface.co/docs/hub/agents-local
- **Example local-app page**: https://huggingface.co/unsloth/Qwen3.6-35B-A3B-GGUF?local-app=llama.cpp
- **Example tree API**: https://huggingface.co/api/models/unsloth/Qwen3.6-35B-A3B-GGUF/tree/main?recursive=true
- **Example llama.cpp search**: https://huggingface.co/models?num_parameters=min:0,max:24B&apps=llama.cpp&sort=trending
- **License**: MIT
