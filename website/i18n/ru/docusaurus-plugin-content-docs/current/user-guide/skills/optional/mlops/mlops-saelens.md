---
title: "Обучение разреженного автокодировщика"
sidebar_label: "Sparse Autoencoder Training"
description: "Предоставляет руководство по обучению и анализу разреженных автокодировщиков (SAEs) с использованием SAELens для разложения активаций нейронных сетей на интерпретируемые признаки"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Обучение разрежённых автокодировщиков

Предоставляет руководство по обучению и анализу разрежённых автокодировщиков (SAE) с использованием SAELens для разложения активаций нейронных сетей на интерпретируемые признаки. Используй при обнаружении интерпретируемых признаков, анализе суперпозиции или изучении моносемантических представлений в языковых моделях.

## Метаданные навыка

| | |
|---|---|
| Source | Optional — install with `hermes skills install official/mlops/saelens` |
| Path | `optional-skills/mlops/saelens` |
| Version | `1.0.0` |
| Author | Orchestra Research |
| License | MIT |
| Dependencies | `sae-lens>=6.0.0`, `transformer-lens>=2.0.0`, `torch>=2.0.0` |
| Platforms | linux, macos, windows |
| Tags | `Sparse Autoencoders`, `SAE`, `Mechanistic Interpretability`, `Feature Discovery`, `Superposition` |

## Ссылка: полный SKILL.md

:::info
Ниже приведено полное определение навыка, которое Hermes загружает при срабатывании этого навыка. Это то, что агент видит как инструкции, когда навык активен.
:::

# SAELens: разрежённые автокодировщики для механистической интерпретируемости

SAELens — основная библиотека для обучения и анализа разрежённых автокодировщиков (SAE) — техники разложения полисемантических активаций нейронных сетей на разреженные, интерпретируемые признаки. Основана на новаторских исследованиях Anthropic о моносемантичности.

**GitHub**: [jbloomAus/SAELens](https://github.com/jbloomAus/SAELens) (1 100+ stars)

## Проблема: полисемантичность и суперпозиция

Отдельные нейроны в нейронных сетях **полисемантичны** — они активируются в нескольких семантически разных контекстах. Это происходит потому, что модели используют **суперпозицию** для представления большего количества признаков, чем у них нейронов, что усложняет интерпретируемость.

**SAE решают эту проблему**, разлагая плотные активации на разреженные, моносемантические признаки — обычно лишь небольшое число признаков активируется для любого входа, и каждый признак соответствует интерпретируемой концепции.

## Когда использовать SAELens

**Используй SAELens, когда нужно:**
- Обнаружить интерпретируемые признаки в активациях модели
- Понять, какие концепции выучила модель
- Изучать суперпозицию и геометрию признаков
- Выполнять управление на основе признаков или абляцию
- Анализировать признаки, важные для безопасности (обман, предвзятость, вредоносный контент)

**Рассматривай альтернативы, когда:**
- Нужен базовый анализ активаций → используй **TransformerLens** напрямую
- Требуются эксперименты с каузальными вмешательствами → используй **pyvene** или **TransformerLens**
- Необходимо производственное управление → рассматривай прямую инженерию активаций

## Установка

```bash
pip install sae-lens
```

Требования: Python 3.10+, transformer-lens>=2.0.0

## Основные концепции

### Что изучают SAE

SAE обучаются восстанавливать активации модели через разрежённое «узкое место»:

```
Input Activation → Encoder → Sparse Features → Decoder → Reconstructed Activation
    (d_model)       ↓        (d_sae >> d_model)    ↓         (d_model)
                 sparsity                      reconstruction
                 penalty                          loss
```

**Функция потерь**: `MSE(original, reconstructed) + L1_coefficient × L1(features)`

### Ключевая валидация (исследования Anthropic)

В работе «Towards Monosemanticity» человеческие оценщики обнаружили, что **70 % признаков SAE действительно интерпретируемы**. Обнаруженные признаки включают:
- ДНК‑последовательности, юридический язык, HTTP‑запросы
- Еврейский текст, заявления о питании, синтаксис кода
- Настроение, именованные сущности, грамматические структуры

## Рабочий процесс 1: загрузка и анализ предобученных SAE

### Пошагово

```python
from transformer_lens import HookedTransformer
from sae_lens import SAE

# 1. Load model and pre-trained SAE
model = HookedTransformer.from_pretrained("gpt2-small", device="cuda")
sae, cfg_dict, sparsity = SAE.from_pretrained(
    release="gpt2-small-res-jb",
    sae_id="blocks.8.hook_resid_pre",
    device="cuda"
)

# 2. Get model activations
tokens = model.to_tokens("The capital of France is Paris")
_, cache = model.run_with_cache(tokens)
activations = cache["resid_pre", 8]  # [batch, pos, d_model]

# 3. Encode to SAE features
sae_features = sae.encode(activations)  # [batch, pos, d_sae]
print(f"Active features: {(sae_features > 0).sum()}")

# 4. Find top features for each position
for pos in range(tokens.shape[1]):
    top_features = sae_features[0, pos].topk(5)
    token = model.to_str_tokens(tokens[0, pos:pos+1])[0]
    print(f"Token '{token}': features {top_features.indices.tolist()}")

# 5. Reconstruct activations
reconstructed = sae.decode(sae_features)
reconstruction_error = (activations - reconstructed).norm()
```

### Доступные предобученные SAE

| Release | Model | Layers |
|---------|-------|--------|
| `gpt2-small-res-jb` | GPT-2 Small | Multiple residual streams |
| `gemma-2b-res` | Gemma 2B | Residual streams |
| Various on HuggingFace | Search tag `saelens` | Various |

### Чеклист
- [ ] Загрузить модель с помощью TransformerLens
- [ ] Загрузить соответствующий SAE для целевого слоя
- [ ] Закодировать активации в разреженные признаки
- [ ] Выявить топ‑активирующие признаки для каждого токена
- [ ] Проверить качество восстановления

## Рабочий процесс 2: обучение собственного SAE

### Пошагово

```python
from sae_lens import SAE, LanguageModelSAERunnerConfig, SAETrainingRunner

# 1. Configure training
cfg = LanguageModelSAERunnerConfig(
    # Model
    model_name="gpt2-small",
    hook_name="blocks.8.hook_resid_pre",
    hook_layer=8,
    d_in=768,  # Model dimension

    # SAE architecture
    architecture="standard",  # or "gated", "topk"
    d_sae=768 * 8,  # Expansion factor of 8
    activation_fn="relu",

    # Training
    lr=4e-4,
    l1_coefficient=8e-5,  # Sparsity penalty
    l1_warm_up_steps=1000,
    train_batch_size_tokens=4096,
    training_tokens=100_000_000,

    # Data
    dataset_path="monology/pile-uncopyrighted",
    context_size=128,

    # Logging
    log_to_wandb=True,
    wandb_project="sae-training",

    # Checkpointing
    checkpoint_path="checkpoints",
    n_checkpoints=5,
)

# 2. Train
trainer = SAETrainingRunner(cfg)
sae = trainer.run()

# 3. Evaluate
print(f"L0 (avg active features): {trainer.metrics['l0']}")
print(f"CE Loss Recovered: {trainer.metrics['ce_loss_score']}")
```

### Ключевые гиперпараметры

| Parameter | Typical Value | Effect |
|-----------|---------------|--------|
| `d_sae` | 4-16× d_model | Больше признаков, большая ёмкость |
| `l1_coefficient` | 5e-5 to 1e-4 | Выше = разрежнее, менее точно |
| `lr` | 1e-4 to 1e-3 | Стандартный LR оптимизатора |
| `l1_warm_up_steps` | 500-2000 | Предотвращает раннюю «смерть» признаков |

### Метрики оценки

| Metric | Target | Meaning |
|--------|--------|---------|
| **L0** | 50-200 | Среднее число активных признаков на токен |
| **CE Loss Score** | 80-95% | Восстановленная кросс‑энтропия по сравнению с оригиналом |
| **Dead Features** | &lt;5% | Признаки, которые никогда не активируются |
| **Explained Variance** | >90% | Качество восстановления |

### Чеклист
- [ ] Выбрать целевой слой и точку хука
- [ ] Установить коэффициент расширения (d_sae = 4-16× d_model)
- [ ] Настроить коэффициент L1 для желаемой разреженности
- [ ] Включить разогрев L1, чтобы избежать «мертвых» признаков
- [ ] Мониторить метрики во время обучения (W&B)
- [ ] Проверить L0 и восстановление CE‑потери
- [ ] Проверить долю «мёртвых» признаков

## Рабочий процесс 3: анализ признаков и управление

### Анализ отдельных признаков

```python
from transformer_lens import HookedTransformer
from sae_lens import SAE
import torch

model = HookedTransformer.from_pretrained("gpt2-small", device="cuda")
sae, _, _ = SAE.from_pretrained(
    release="gpt2-small-res-jb",
    sae_id="blocks.8.hook_resid_pre",
    device="cuda"
)

# Find what activates a specific feature
feature_idx = 1234
test_texts = [
    "The scientist conducted an experiment",
    "I love chocolate cake",
    "The code compiles successfully",
    "Paris is beautiful in spring",
]

for text in test_texts:
    tokens = model.to_tokens(text)
    _, cache = model.run_with_cache(tokens)
    features = sae.encode(cache["resid_pre", 8])
    activation = features[0, :, feature_idx].max().item()
    print(f"{activation:.3f}: {text}")
```

### Управление признаками

```python
def steer_with_feature(model, sae, prompt, feature_idx, strength=5.0):
    """Add SAE feature direction to residual stream."""
    tokens = model.to_tokens(prompt)

    # Get feature direction from decoder
    feature_direction = sae.W_dec[feature_idx]  # [d_model]

    def steering_hook(activation, hook):
        # Add scaled feature direction at all positions
        activation += strength * feature_direction
        return activation

    # Generate with steering
    output = model.generate(
        tokens,
        max_new_tokens=50,
        fwd_hooks=[("blocks.8.hook_resid_pre", steering_hook)]
    )
    return model.to_string(output[0])
```

### Атрибуция признаков

```python
# Which features most affect a specific output?
tokens = model.to_tokens("The capital of France is")
_, cache = model.run_with_cache(tokens)

# Get features at final position
features = sae.encode(cache["resid_pre", 8])[0, -1]  # [d_sae]

# Get logit attribution per feature
# Feature contribution = feature_activation × decoder_weight × unembedding
W_dec = sae.W_dec  # [d_sae, d_model]
W_U = model.W_U    # [d_model, vocab]

# Contribution to "Paris" logit
paris_token = model.to_single_token(" Paris")
feature_contributions = features * (W_dec @ W_U[:, paris_token])

top_features = feature_contributions.topk(10)
print("Top features for 'Paris' prediction:")
for idx, val in zip(top_features.indices, top_features.values):
    print(f"  Feature {idx.item()}: {val.item():.3f}")
```

## Распространённые проблемы и решения

### Проблема: высокий процент «мёртвых» признаков
```python
# WRONG: No warm-up, features die early
cfg = LanguageModelSAERunnerConfig(
    l1_coefficient=1e-4,
    l1_warm_up_steps=0,  # Bad!
)

# RIGHT: Warm-up L1 penalty
cfg = LanguageModelSAERunnerConfig(
    l1_coefficient=8e-5,
    l1_warm_up_steps=1000,  # Gradually increase
    use_ghost_grads=True,   # Revive dead features
)
```

### Проблема: плохое восстановление (низкое восстановление CE)
```python
# Reduce sparsity penalty
cfg = LanguageModelSAERunnerConfig(
    l1_coefficient=5e-5,  # Lower = better reconstruction
    d_sae=768 * 16,       # More capacity
)
```

### Проблема: признаки не интерпретируемы
```python
# Increase sparsity (higher L1)
cfg = LanguageModelSAERunnerConfig(
    l1_coefficient=1e-4,  # Higher = sparser, more interpretable
)
# Or use TopK architecture
cfg = LanguageModelSAERunnerConfig(
    architecture="topk",
    activation_fn_kwargs={"k": 50},  # Exactly 50 active features
)
```

### Проблема: ошибки памяти во время обучения
```python
cfg = LanguageModelSAERunnerConfig(
    train_batch_size_tokens=2048,  # Reduce batch size
    store_batch_size_prompts=4,    # Fewer prompts in buffer
    n_batches_in_buffer=8,         # Smaller activation buffer
)
```

## Интеграция с Neuronpedia

Просматривай предобученные признаки SAE на [neuronpedia.org](https://neuronpedia.org):

```python
# Features are indexed by SAE ID
# Example: gpt2-small layer 8 feature 1234
# → neuronpedia.org/gpt2-small/8-res-jb/1234
```

## Справочник ключевых классов

| Class | Purpose |
|-------|---------|
| `SAE` | Sparse Autoencoder model |
| `LanguageModelSAERunnerConfig` | Training configuration |
| `SAETrainingRunner` | Training loop manager |
| `ActivationsStore` | Activation collection and batching |
| `HookedSAETransformer` | TransformerLens + SAE integration |

## Справочная документация

Для подробного описания API, учебных материалов и продвинутого использования смотри папку `references/`:

| File | Contents |
|------|----------|
| [references/README.md](https://github.com/NousResearch/hermes-agent/blob/main/optional-skills/mlops/saelens/references/README.md) | Overview and quick start guide |
| [references/api.md](https://github.com/NousResearch/hermes-agent/blob/main/optional-skills/mlops/saelens/references/api.md) | Complete API reference for SAE, TrainingSAE, configurations |
| [references/tutorials.md](https://github.com/NousResearch/hermes-agent/blob/main/optional-skills/mlops/saelens/references/tutorials.md) | Step-by-step tutorials for training, analysis, steering |

## Внешние ресурсы

### Учебные материалы
- [Basic Loading & Analysis](https://github.com/jbloomAus/SAELens/blob/main/tutorials/basic_loading_and_analysing.ipynb)
- [Training a Sparse Autoencoder](https://github.com/jbloomAus/SAELens/blob/main/tutorials/training_a_sparse_autoencoder.ipynb)
- [ARENA SAE Curriculum](https://www.lesswrong.com/posts/LnHowHgmrMbWtpkxx/intro-to-superposition-and-sparse-autoencoders-colab)

### Статьи
- [Towards Monosemanticity](https://transformer-circuits.pub/2023/monosemantic-features) - Anthropic (2023)
- [Scaling Monosemanticity](https://transformer-circuits.pub/2024/scaling-monosemanticity/) - Anthropic (2024)
- [Sparse Autoencoders Find Highly Interpretable Features](https://arxiv.org/abs/2309.08600) - Cunningham et al. (ICLR 2024)

### Официальная документация
- [SAELens Docs](https://jbloomaus.github.io/SAELens/)
- [Neuronpedia](https://neuronpedia.org) - Feature browser

## Архитектуры SAE

| Architecture | Description | Use Case |
|--------------|-------------|----------|
| **Standard** | ReLU + L1 penalty | General purpose |
| **Gated** | Learned gating mechanism | Better sparsity control |
| **TopK** | Exactly K active features | Consistent sparsity |

```python
# TopK SAE (exactly 50 features active)
cfg = LanguageModelSAERunnerConfig(
    architecture="topk",
    activation_fn="topk",
    activation_fn_kwargs={"k": 50},
)
```