---
title: "Оптимізація Attention Flash"
sidebar_label: "Optimizing Attention Flash"
description: "Оптимізує увагу трансформера за допомогою Flash Attention для 2‑4‑х кратного прискорення та 10‑20‑х скорочення пам’яті"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Оптимізація Flash Attention

Оптимізує увагу трансформера за допомогою Flash Attention для 2‑4× прискорення та 10‑20× зменшення використання пам’яті. Використовуй, коли навчаєш/запускаєш трансформери з довгими послідовностями (>512 токенів), стикаєшся з проблемами пам’яті GPU під час уваги або потрібна швидша інференція. Підтримує нативний PyTorch SDPA, бібліотеку flash‑attn, H100 FP8 та віконну (sliding‑window) увагу.

## Метадані навички

| | |
|---|---|
| Source | Optional — install with `hermes skills install official/mlops/flash-attention` |
| Path | `optional-skills/mlops/flash-attention` |
| Version | `1.0.0` |
| Author | Orchestra Research |
| License | MIT |
| Dependencies | `flash-attn`, `torch`, `transformers` |
| Platforms | linux, macos |
| Tags | `Optimization`, `Flash Attention`, `Attention Optimization`, `Memory Efficiency`, `Speed Optimization`, `Long Context`, `PyTorch`, `SDPA`, `H100`, `FP8`, `Transformers` |

## Reference: full SKILL.md

:::info
The following is the complete skill definition that Hermes loads when this skill is triggered. This is what the agent sees as instructions when the skill is active.
:::

# Flash Attention — швидка пам’яттє‑ефективна увага

## Швидкий старт

Flash Attention забезпечує 2‑4× прискорення та 10‑20× зменшення використання пам’яті для уваги трансформера завдяки IO‑aware тайлінгу та переобчисленню.

**PyTorch native (найпростіший, PyTorch 2.2+)**:
```python
import torch
import torch.nn.functional as F

q = torch.randn(2, 8, 512, 64, device='cuda', dtype=torch.float16)  # [batch, heads, seq, dim]
k = torch.randn(2, 8, 512, 64, device='cuda', dtype=torch.float16)
v = torch.randn(2, 8, 512, 64, device='cuda', dtype=torch.float16)

# Automatically uses Flash Attention if available
out = F.scaled_dot_product_attention(q, k, v)
```

**flash‑attn library (більше функцій)**:
```bash
pip install flash-attn --no-build-isolation
```

```python
from flash_attn import flash_attn_func

# q, k, v: [batch, seqlen, nheads, headdim]
out = flash_attn_func(q, k, v, dropout_p=0.0, causal=True)
```

## Типові робочі процеси

### Робочий процес 1: Увімкнути в існуючій моделі PyTorch

Скопіюй цей чек‑ліст:

```
Flash Attention Integration:
- [ ] Step 1: Check PyTorch version (≥2.2)
- [ ] Step 2: Enable Flash Attention backend
- [ ] Step 3: Verify speedup with profiling
- [ ] Step 4: Test accuracy matches baseline
```

**Крок 1: Перевірка версії PyTorch**

```bash
python -c "import torch; print(torch.__version__)"
# Should be ≥2.2.0
```

Якщо < 2.2, онови:
```bash
pip install --upgrade torch
```

**Крок 2: Увімкнути бекенд Flash Attention**

Замінити стандартну увагу:
```python
# Before (standard attention)
attn_weights = torch.softmax(q @ k.transpose(-2, -1) / math.sqrt(d_k), dim=-1)
out = attn_weights @ v

# After (Flash Attention)
import torch.nn.functional as F
out = F.scaled_dot_product_attention(q, k, v, attn_mask=mask)
```

Примусово використати бекенд Flash Attention:
```python
with torch.backends.cuda.sdp_kernel(
    enable_flash=True,
    enable_math=False,
    enable_mem_efficient=False
):
    out = F.scaled_dot_product_attention(q, k, v)
```

**Крок 3: Перевірити прискорення за допомогою профілювання**

```python
import torch.utils.benchmark as benchmark

def test_attention(use_flash):
    q, k, v = [torch.randn(2, 8, 2048, 64, device='cuda', dtype=torch.float16) for _ in range(3)]

    if use_flash:
        with torch.backends.cuda.sdp_kernel(enable_flash=True):
            return F.scaled_dot_product_attention(q, k, v)
    else:
        attn = (q @ k.transpose(-2, -1) / 8.0).softmax(dim=-1)
        return attn @ v

# Benchmark
t_flash = benchmark.Timer(stmt='test_attention(True)', globals=globals())
t_standard = benchmark.Timer(stmt='test_attention(False)', globals=globals())

print(f"Flash: {t_flash.timeit(100).mean:.3f}s")
print(f"Standard: {t_standard.timeit(100).mean:.3f}s")
```

Очікується: 2‑4× прискорення для послідовностей > 512 токенів.

**Крок 4: Перевірити, що точність відповідає базовій**

```python
# Compare outputs
q, k, v = [torch.randn(1, 8, 512, 64, device='cuda', dtype=torch.float16) for _ in range(3)]

# Flash Attention
out_flash = F.scaled_dot_product_attention(q, k, v)

# Standard attention
attn_weights = torch.softmax(q @ k.transpose(-2, -1) / 8.0, dim=-1)
out_standard = attn_weights @ v

# Check difference
diff = (out_flash - out_standard).abs().max()
print(f"Max difference: {diff:.6f}")
# Should be <1e-3 for float16
```

### Робочий процес 2: Використати бібліотеку flash‑attn для розширених можливостей

Для multi‑query attention, віконної уваги або H100 FP8.

Скопіюй цей чек‑ліст:

```
flash-attn Library Setup:
- [ ] Step 1: Install flash-attn library
- [ ] Step 2: Modify attention code
- [ ] Step 3: Enable advanced features
- [ ] Step 4: Benchmark performance
```

**Крок 1: Встановити бібліотеку flash‑attn**

```bash
# NVIDIA GPUs (CUDA 12.0+)
pip install flash-attn --no-build-isolation

# Verify installation
python -c "from flash_attn import flash_attn_func; print('Success')"
```

**Крок 2: Змінити код уваги**

```python
from flash_attn import flash_attn_func

# Input: [batch_size, seq_len, num_heads, head_dim]
# Transpose from [batch, heads, seq, dim] if needed
q = q.transpose(1, 2)  # [batch, seq, heads, dim]
k = k.transpose(1, 2)
v = v.transpose(1, 2)

out = flash_attn_func(
    q, k, v,
    dropout_p=0.1,
    causal=True,  # For autoregressive models
    window_size=(-1, -1),  # No sliding window
    softmax_scale=None  # Auto-scale
)

out = out.transpose(1, 2)  # Back to [batch, heads, seq, dim]
```

**Крок 3: Увімкнути розширені функції**

Multi‑query attention (спільні K/V між головами):
```python
from flash_attn import flash_attn_func

# q: [batch, seq, num_q_heads, dim]
# k, v: [batch, seq, num_kv_heads, dim]  # Fewer KV heads
out = flash_attn_func(q, k, v)  # Automatically handles MQA
```

Sliding‑window attention (локальна увага):
```python
# Only attend to window of 256 tokens before/after
out = flash_attn_func(
    q, k, v,
    window_size=(256, 256),  # (left, right) window
    causal=True
)
```

**Крок 4: Провести бенчмарк продуктивності**

```python
import torch
from flash_attn import flash_attn_func
import time

q, k, v = [torch.randn(4, 4096, 32, 64, device='cuda', dtype=torch.float16) for _ in range(3)]

# Warmup
for _ in range(10):
    _ = flash_attn_func(q, k, v)

# Benchmark
torch.cuda.synchronize()
start = time.time()
for _ in range(100):
    out = flash_attn_func(q, k, v)
    torch.cuda.synchronize()
end = time.time()

print(f"Time per iteration: {(end-start)/100*1000:.2f}ms")
print(f"Memory allocated: {torch.cuda.max_memory_allocated()/1e9:.2f}GB")
```

### Робочий процес 3: Оптимізація H100 FP8 (FlashAttention‑3)

Для максимальної продуктивності на GPU H100.

```
FP8 Setup:
- [ ] Step 1: Verify H100 GPU available
- [ ] Step 2: Install flash-attn with FP8 support
- [ ] Step 3: Convert inputs to FP8
- [ ] Step 4: Run with FP8 attention
```

**Крок 1: Перевірити GPU H100**

```bash
nvidia-smi --query-gpu=name --format=csv
# Should show "H100" or "H800"
```

**Крок 2: Встановити flash‑attn з підтримкою FP8**

```bash
pip install flash-attn --no-build-isolation
# FP8 support included for H100
```

**Крок 3: Перетворити вхідні дані у FP8**

```python
import torch

q = torch.randn(2, 4096, 32, 64, device='cuda', dtype=torch.float16)
k = torch.randn(2, 4096, 32, 64, device='cuda', dtype=torch.float16)
v = torch.randn(2, 4096, 32, 64, device='cuda', dtype=torch.float16)

# Convert to float8_e4m3 (FP8)
q_fp8 = q.to(torch.float8_e4m3fn)
k_fp8 = k.to(torch.float8_e4m3fn)
v_fp8 = v.to(torch.float8_e4m3fn)
```

**Крок 4: Запустити з FP8‑увагою**

```python
from flash_attn import flash_attn_func

# FlashAttention-3 automatically uses FP8 kernels on H100
out = flash_attn_func(q_fp8, k_fp8, v_fp8)
# Result: ~1.2 PFLOPS, 1.5-2x faster than FP16
```

## Коли використовувати vs альтернативи

**Використовуй Flash Attention, коли:**
- Навчаєш трансформери з послідовностями > 512 токенів
- Запускаєш інференцію з довгим контекстом (> 2 K токенів)
- Пам’ять GPU обмежена (OOM зі стандартною увагою)
- Потрібне 2‑4× прискорення без втрати точності
- Використовуєш PyTorch 2.2+ або можеш встановити flash‑attn

**Використовуй альтернативи замість:**
- **Standard attention**: послідовності < 256 токенів (накладні витрати не виправдані)
- **xFormers**: потрібні інші варіанти уваги (не лише швидкість)
- **Memory‑efficient attention**: CPU‑інференція (Flash Attention потребує GPU)

## Поширені проблеми

**Проблема: ImportError: cannot import flash_attn**

Встанови з прапорцем `no-build-isolation`:
```bash
pip install flash-attn --no-build-isolation
```

Або спочатку встанови CUDA toolkit:
```bash
conda install cuda -c nvidia
pip install flash-attn --no-build-isolation
```

**Проблема: Повільніше, ніж очікувалося (немає прискорення)**

Переваги Flash Attention зростають зі збільшенням довжини послідовності:
- < 512 токенів: мінімальне прискорення (10‑20 %)
- 512‑2 K токенів: 2‑3× прискорення
- > 2 K токенів: 3‑4× прискорення

Перевір, чи довжина послідовності достатня.

**Проблема: RuntimeError: CUDA error**

Переконайся, що GPU підтримує Flash Attention:
```python
import torch
print(torch.cuda.get_device_capability())
# Should be ≥(7, 5) for Turing+
```

Flash Attention вимагає:
- Ampere (A100, A10): ✅ повна підтримка
- Turing (T4): ✅ підтримується
- Volta (V100): ❌ не підтримується

**Проблема: Падіння точності**

Перевір, чи dtype — `float16` або `bfloat16` (не `float32`):
```python
q = q.to(torch.float16)  # Or torch.bfloat16
```

Flash Attention використовує `float16`/`bfloat16` для швидкості. `float32` не підтримується.

## Розширені теми

**Інтеграція з HuggingFace Transformers**: Дивись [references/transformers-integration.md](https://github.com/NousResearch/hermes-agent/blob/main/optional-skills/mlops/flash-attention/references/transformers-integration.md) для увімкнення Flash Attention у моделях BERT, GPT, Llama.

**Бенчмарки продуктивності**: Дивись [references/benchmarks.md](https://github.com/NousResearch/hermes-agent/blob/main/optional-skills/mlops/flash-attention/references/benchmarks.md) для детальних порівнянь швидкості та пам’яті на різних GPU та довжинах послідовностей.

## Апаратурні вимоги

- **GPU**: NVIDIA Ampere+ (A100, A10, A30) або AMD MI200+
- **VRAM**: така ж, як у стандартної уваги (Flash Attention не збільшує використання пам’яті)
- **CUDA**: 12.0+ (мінімум 11.8)
- **PyTorch**: 2.2+ для нативної підтримки

**Не підтримується**: V100 (Volta), CPU‑інференція

## Ресурси

- Paper: “FlashAttention: Fast and Memory-Efficient Exact Attention with IO-Awareness” (NeurIPS 2022)
- Paper: “FlashAttention-2: Faster Attention with Better Parallelism and Work Partitioning” (ICLR 2024)
- Blog: https://tridao.me/blog/2024/flash3/
- GitHub: https://github.com/Dao-AILab/flash-attention
- PyTorch docs: https://pytorch.org/docs/stable/generated/torch.nn.functional.scaled_dot_product_attention.html