---
title: "Оптимизация Attention Flash"
sidebar_label: "Optimizing Attention Flash"
description: "Оптимизирует внимание трансформера с помощью Flash Attention для ускорения в 2‑4 раза и снижения потребления памяти в 10‑20 раз."
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Оптимизация Flash Attention

Оптимизирует внимание трансформера с помощью Flash Attention, обеспечивая ускорение 2‑4× и снижение потребления памяти 10‑20×. Используй при обучении/запуске трансформеров с длинными последовательностями (>512 токенов), при проблемах с памятью GPU из‑за внимания или когда нужна более быстрая инференция. Поддерживает нативный PyTorch SDPA, библиотеку flash‑attn, H100 FP8 и скользящее окно внимания.

## Метаданные навыка

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

## Ссылка: полный SKILL.md

:::info
Ниже представлено полное определение навыка, которое Hermes загружает при его активации. Это то, что агент видит как инструкции, когда навык активен.
:::

# Flash Attention — Быстрое и Память‑Эффективное Внимание

## Быстрый старт

Flash Attention обеспечивает ускорение 2‑4× и снижение потребления памяти 10‑20× для внимания трансформера за счёт IO‑aware тайлинга и пере‑вычисления.

**Нативный PyTorch (самый простой, PyTorch 2.2+)**:
```python
import torch
import torch.nn.functional as F

q = torch.randn(2, 8, 512, 64, device='cuda', dtype=torch.float16)  # [batch, heads, seq, dim]
k = torch.randn(2, 8, 512, 64, device='cuda', dtype=torch.float16)
v = torch.randn(2, 8, 512, 64, device='cuda', dtype=torch.float16)

# Automatically uses Flash Attention if available
out = F.scaled_dot_product_attention(q, k, v)
```

**Библиотека flash‑attn (больше возможностей)**:
```bash
pip install flash-attn --no-build-isolation
```

```python
from flash_attn import flash_attn_func

# q, k, v: [batch, seqlen, nheads, headdim]
out = flash_attn_func(q, k, v, dropout_p=0.0, causal=True)
```

## Распространённые рабочие процессы

### Рабочий процесс 1: Включить в существующей модели PyTorch

Скопируй этот чек‑лист:
```
Flash Attention Integration:
- [ ] Step 1: Check PyTorch version (≥2.2)
- [ ] Step 2: Enable Flash Attention backend
- [ ] Step 3: Verify speedup with profiling
- [ ] Step 4: Test accuracy matches baseline
```

**Шаг 1: Проверить версию PyTorch**
```bash
python -c "import torch; print(torch.__version__)"
# Should be ≥2.2.0
```

Если < 2.2, обнови:
```bash
pip install --upgrade torch
```

**Шаг 2: Включить бэкенд Flash Attention**

Заменить стандартное внимание:
```python
# Before (standard attention)
attn_weights = torch.softmax(q @ k.transpose(-2, -1) / math.sqrt(d_k), dim=-1)
out = attn_weights @ v

# After (Flash Attention)
import torch.nn.functional as F
out = F.scaled_dot_product_attention(q, k, v, attn_mask=mask)
```

Принудительно использовать бэкенд Flash Attention:
```python
with torch.backends.cuda.sdp_kernel(
    enable_flash=True,
    enable_math=False,
    enable_mem_efficient=False
):
    out = F.scaled_dot_product_attention(q, k, v)
```

**Шаг 3: Проверить ускорение с помощью профилирования**
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

Ожидается ускорение 2‑4× для последовательностей > 512 токенов.

**Шаг 4: Проверить, что точность совпадает с базовой**
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

### Рабочий процесс 2: Использовать библиотеку flash‑attn для продвинутых функций

Для multi‑query attention, скользящего окна или H100 FP8.
Скопируй этот чек‑лист:
```
flash-attn Library Setup:
- [ ] Step 1: Install flash-attn library
- [ ] Step 2: Modify attention code
- [ ] Step 3: Enable advanced features
- [ ] Step 4: Benchmark performance
```

**Шаг 1: Установить библиотеку flash‑attn**
```bash
# NVIDIA GPUs (CUDA 12.0+)
pip install flash-attn --no-build-isolation

# Verify installation
python -c "from flash_attn import flash_attn_func; print('Success')"
```

**Шаг 2: Изменить код внимания**
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

**Шаг 3: Включить продвинутые функции**

Multi‑query attention (общие K/V между головами):
```python
from flash_attn import flash_attn_func

# q: [batch, seq, num_q_heads, dim]
# k, v: [batch, seq, num_kv_heads, dim]  # Fewer KV heads
out = flash_attn_func(q, k, v)  # Automatically handles MQA
```

Sliding‑window attention (локальное внимание):
```python
# Only attend to window of 256 tokens before/after
out = flash_attn_func(
    q, k, v,
    window_size=(256, 256),  # (left, right) window
    causal=True
)
```

**Шаг 4: Провести бенчмарк производительности**
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

### Рабочий процесс 3: Оптимизация H100 FP8 (FlashAttention‑3)

Для максимальной производительности на GPU H100.
```
FP8 Setup:
- [ ] Step 1: Verify H100 GPU available
- [ ] Step 2: Install flash-attn with FP8 support
- [ ] Step 3: Convert inputs to FP8
- [ ] Step 4: Run with FP8 attention
```

**Шаг 1: Проверить наличие GPU H100**
```bash
nvidia-smi --query-gpu=name --format=csv
# Should show "H100" or "H800"
```

**Шаг 2: Установить flash‑attn с поддержкой FP8**
```bash
pip install flash-attn --no-build-isolation
# FP8 support included for H100
```

**Шаг 3: Преобразовать входы в FP8**
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

**Шаг 4: Запустить с вниманием FP8**
```python
from flash_attn import flash_attn_func

# FlashAttention-3 automatically uses FP8 kernels on H100
out = flash_attn_func(q_fp8, k_fp8, v_fp8)
# Result: ~1.2 PFLOPS, 1.5-2x faster than FP16
```

## Когда использовать vs альтернативы

**Используй Flash Attention, когда:**
- Обучаешь трансформеры с последовательностями > 512 токенов
- Запускаешь инференцию с длинным контекстом (> 2 K токенов)
- Память GPU ограничена (OOM при стандартном внимании)
- Нужен ускорение 2‑4× без потери точности
- Есть PyTorch 2.2+ или возможность установить flash‑attn

**Выбирай альтернативы вместо него:**
- **Стандартное внимание**: последовательности < 256 токенов (накладные расходы не оправданы)
- **xFormers**: нужны дополнительные варианты внимания (не только скорость)
- **Memory‑efficient attention**: инференция на CPU (Flash Attention требует GPU)

## Распространённые проблемы

**Проблема: ImportError: cannot import flash_attn**

Установи с флагом `no-build-isolation`:
```bash
pip install flash-attn --no-build-isolation
```

Или сначала установить набор инструментов CUDA:
```bash
conda install cuda -c nvidia
pip install flash-attn --no-build-isolation
```

**Проблема: Медленнее, чем ожидалось (нет ускорения)**

Преимущества Flash Attention растут с длиной последовательности:
- < 512 токенов: минимальное ускорение (10‑20 %)
- 512‑2 K токенов: ускорение 2‑3×
- > 2 K токенов: ускорение 3‑4×

Проверь, что длина последовательности достаточна.

**Проблема: RuntimeError: CUDA error**

Убедись, что GPU поддерживает Flash Attention:
```python
import torch
print(torch.cuda.get_device_capability())
# Should be ≥(7, 5) for Turing+
```

Требования Flash Attention:
- Ampere (A100, A10, A30): ✅ Полная поддержка
- Turing (T4): ✅ Поддерживается
- Volta (V100): ❌ Не поддерживается

**Проблема: Падение точности**

Проверь, что тип данных — float16 или bfloat16 (не float32):
```python
q = q.to(torch.float16)  # Or torch.bfloat16
```

Flash Attention использует float16/bfloat16 для скорости. Float32 не поддерживается.

## Продвинутые темы

**Интеграция с HuggingFace Transformers**: см. [references/transformers-integration.md](https://github.com/NousResearch/hermes-agent/blob/main/optional-skills/mlops/flash-attention/references/transformers-integration.md) для включения Flash Attention в модели BERT, GPT, Llama.

**Бенчмарки производительности**: см. [references/benchmarks.md](https://github.com/NousResearch/hermes-agent/blob/main/optional-skills/mlops/flash-attention/references/benchmarks.md) для детального сравнения скорости и памяти на разных GPU и длинах последовательностей.

## Требования к оборудованию

- **GPU**: NVIDIA Ampere+ (A100, A10, A30) или AMD MI200+
- **VRAM**: такая же, как у стандартного внимания (Flash Attention не увеличивает потребление памяти)
- **CUDA**: 12.0+ (минимум 11.8)
- **PyTorch**: 2.2+ для нативной поддержки

**Не поддерживается**: V100 (Volta), инференция на CPU

## Ресурсы

- Статья: “FlashAttention: Fast and Memory-Efficient Exact Attention with IO-Awareness” (NeurIPS 2022)
- Статья: “FlashAttention-2: Faster Attention with Better Parallelism and Work Partitioning” (ICLR 2024)
- Блог: https://tridao.me/blog/2024/flash3/
- GitHub: https://github.com/Dao-AILab/flash-attention
- Документация PyTorch: https://pytorch.org/docs/stable/generated/torch.nn.functional.scaled_dot_product_attention.html