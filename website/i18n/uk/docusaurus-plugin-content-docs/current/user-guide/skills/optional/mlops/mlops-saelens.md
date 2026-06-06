---
title: "Навчання розрідженого автокодера"
sidebar_label: "Sparse Autoencoder Training"
description: "Надає рекомендації щодо навчання та аналізу Sparse Autoencoders (SAEs) за допомогою SAELens для розкладання активацій нейронної мережі на інтерпретовані ознаки"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Навчання розріджених автокодерів

Надає рекомендації щодо навчання та аналізу розріджених автокодерів (SAE) за допомогою SAELens для розкладання активацій нейронних мереж на інтерпретовані ознаки. Використовуй, коли потрібно виявляти інтерпретовані ознаки, аналізувати суперпозицію або досліджувати моносемантичні представлення в мовних моделях.

## Метадані навички

| | |
|---|---|
| Джерело | Optional — install with `hermes skills install official/mlops/saelens` |
| Шлях | `optional-skills/mlops/saelens` |
| Версія | `1.0.0` |
| Автор | Orchestra Research |
| Ліцензія | MIT |
| Залежності | `sae-lens>=6.0.0`, `transformer-lens>=2.0.0`, `torch>=2.0.0` |
| Платформи | linux, macos, windows |
| Теги | `Sparse Autoencoders`, `SAE`, `Mechanistic Interpretability`, `Feature Discovery`, `Superposition` |

## Довідка: повний SKILL.md

:::info
Нижче наведено повне визначення навички, яке Hermes завантажує, коли ця навичка активована. Це те, що агент бачить як інструкції під час роботи навички.
:::

# SAELens: розріджені автокодери для механістичної інтерпретативності

SAELens — це основна бібліотека для навчання та аналізу розріджених автокодерів (SAE) — техніки розкладання полісемантичних активацій нейронної мережі на розріджені, інтерпретовані ознаки. Засновано на новаторських дослідженнях Anthropic щодо моносемантичності.

**GitHub**: [jbloomAus/SAELens](https://github.com/jbloomAus/SAELens) (1,100+ stars)

## Проблема: полісемантичність та суперпозиція

Окремі нейрони в нейронних мережах **полісемантичні** — вони активуються в різних, семантично різних контекстах. Це відбувається тому, що моделі використовують **суперпозицію** для представлення більшої кількості ознак, ніж мають нейронів, що ускладнює інтерпретативність.

**SAE вирішують це**, розкладаючи щільні активації на розріджені, моносемантичні ознаки — зазвичай лише невелика кількість ознак активується для будь‑якого вхідного сигналу, і кожна ознака відповідає інтерпретованій концепції.

## Коли використовувати SAELens

**Використовуй SAELens, коли потрібно:**
- Виявляти інтерпретовані ознаки в активаціях моделі
- Розуміти, які концепції модель вивчила
- Досліджувати суперпозицію та геометрію ознак
- Виконувати керування на основі ознак або абляцію
- Аналізувати ознаки, важливі для безпеки (обман, упередженість, шкідливий контент)

**Розглядай альтернативи, коли:**
- Потрібен базовий аналіз активацій → використай **TransformerLens** безпосередньо
- Потрібні експерименти з каузальними втручаннями → використай **pyvene** або **TransformerLens**
- Потрібне виробниче керування → розглянь пряме інженерування активацій

## Встановлення

```bash
pip install sae-lens
```

Вимоги: Python 3.10+, transformer-lens>=2.0.0

## Основні концепції

### Чого навчаються SAE

SAE навчаються відтворювати активації моделі через розріджений вузький прохід:

```
Input Activation → Encoder → Sparse Features → Decoder → Reconstructed Activation
    (d_model)       ↓        (d_sae >> d_model)    ↓         (d_model)
                 sparsity                      reconstruction
                 penalty                          loss
```

**Функція втрат**: `MSE(original, reconstructed) + L1_coefficient × L1(features)`

### Ключова валідація (дослідження Anthropic)

У статті «Towards Monosemanticity» людські оцінювачі виявили, що **70 % ознак SAE справді інтерпретовані**. Виявлені ознаки включають:
- ДНК‑послідовності, юридичну мову, HTTP‑запити
- Єврейський текст, заяви про харчування, синтаксис коду
- Сентимент, іменовані сутності, граматичні структури

## Робочий процес 1: Завантаження та аналіз попередньо навчених SAE

### Крок за кроком

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

### Доступні попередньо навчені SAE

| Реліз | Модель | Шари |
|---------|-------|--------|
| `gpt2-small-res-jb` | GPT-2 Small | Кілька залишкових потоків |
| `gemma-2b-res` | Gemma 2B | Залишкові потоки |
| Various on HuggingFace | Search tag `saelens` | Various |

### Чек‑лист
- [ ] Завантажити модель за допомогою TransformerLens
- [ ] Завантажити відповідний SAE для цільового шару
- [ ] Закодувати активації у розріджені ознаки
- [ ] Визначити топ‑активні ознаки для кожного токену
- [ ] Перевірити якість відтворення

## Робочий процес 2: Навчання власного SAE

### Крок за кроком

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

### Ключові гіперпараметри

| Параметр | Типове значення | Ефект |
|-----------|---------------|--------|
| `d_sae` | 4‑16× d_model | Більше ознак, вища місткість |
| `l1_coefficient` | 5e-5 to 1e-4 | Вище = розрідженіше, менш точно |
| `lr` | 1e-4 to 1e-3 | Стандартна швидкість оптимізатора |
| `l1_warm_up_steps` | 500‑2000 | Запобігає ранньому «вмиранню» ознак |

### Метрики оцінки

| Метрика | Ціль | Значення |
|--------|--------|---------|
| **L0** | 50‑200 | Середня кількість активних ознак на токен |
| **CE Loss Score** | 80‑95 % | Відновлення крос‑ентропії порівняно з оригіналом |
| **Dead Features** | <5 % | ОЗнаки, які ніколи не активуються |
| **Explained Variance** | >90 % | Якість відтворення |

### Чек‑лист
- [ ] Обрати цільовий шар і точку хука
- [ ] Встановити фактор розширення (d_sae = 4‑16× d_model)
- [ ] Налаштувати коефіцієнт L1 для потрібної розрідженості
- [ ] Увімкнути L1 warm‑up, щоб уникнути «мертвих» ознак
- [ ] Моніторити метрики під час навчання (W&B)
- [ ] Перевірити L0 та відновлення CE‑втрати
- [ ] Перевірити частку «мертвих» ознак

## Робочий процес 3: Аналіз ознак та керування

### Аналіз окремих ознак

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

### Керування ознаками

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

### Атрибуція ознак

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

## Поширені проблеми та рішення

### Проблема: висока частка «мертвих» ознак
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

### Проблема: погане відтворення (низьке відновлення CE)
```python
# Reduce sparsity penalty
cfg = LanguageModelSAERunnerConfig(
    l1_coefficient=5e-5,  # Lower = better reconstruction
    d_sae=768 * 16,       # More capacity
)
```

### Проблема: ознаки не інтерпретовані
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

### Проблема: помилки пам’яті під час навчання
```python
cfg = LanguageModelSAERunnerConfig(
    train_batch_size_tokens=2048,  # Reduce batch size
    store_batch_size_prompts=4,    # Fewer prompts in buffer
    n_batches_in_buffer=8,         # Smaller activation buffer
)
```

## Інтеграція з Neuronpedia

Переглядай попередньо навчені ознаки SAE на [neuronpedia.org](https://neuronpedia.org):

```python
# Features are indexed by SAE ID
# Example: gpt2-small layer 8 feature 1234
# → neuronpedia.org/gpt2-small/8-res-jb/1234
```

## Довідка по ключових класах

| Клас | Призначення |
|-------|---------|
| `SAE` | Модель розрідженого автокодера |
| `LanguageModelSAERunnerConfig` | Конфігурація навчання |
| `SAETrainingRunner` | Менеджер циклу навчання |
| `ActivationsStore` | Збір та батчинг активацій |
| `HookedSAETransformer` | Інтеграція TransformerLens + SAE |

## Довідкова документація

Для докладної API‑документації, підручників та розширеного використання дивись папку `references/`:

| Файл | Вміст |
|------|----------|
| [references/README.md](https://github.com/NousResearch/hermes-agent/blob/main/optional-skills/mlops/saelens/references/README.md) | Огляд та швидкий старт |
| [references/api.md](https://github.com/NousResearch/hermes-agent/blob/main/optional-skills/mlops/saelens/references/api.md) | Повна API‑довідка для SAE, TrainingSAE, конфігурацій |
| [references/tutorials.md](https://github.com/NousResearch/hermes-agent/blob/main/optional-skills/mlops/saelens/references/tutorials.md) | Покрокові підручники з навчання, аналізу, керування |

## Зовнішні ресурси

### Підручники
- [Basic Loading & Analysis](https://github.com/jbloomAus/SAELens/blob/main/tutorials/basic_loading_and_analysing.ipynb)
- [Training a Sparse Autoencoder](https://github.com/jbloomAus/SAELens/blob/main/tutorials/training_a_sparse_autoencoder.ipynb)
- [ARENA SAE Curriculum](https://www.lesswrong.com/posts/LnHowHgmrMbWtpkxx/intro-to-superposition-and-sparse-autoencoders-colab)

### Папери
- [Towards Monosemanticity](https://transformer-circuits.pub/2023/monosemantic-features) – Anthropic (2023)
- [Scaling Monosemanticity](https://transformer-circuits.pub/2024/scaling-monosemanticity/) – Anthropic (2024)
- [Sparse Autoencoders Find Highly Interpretable Features](https://arxiv.org/abs/2309.08600) – Cunningham et al. (ICLR 2024)

### Офіційна документація
- [SAELens Docs](https://jbloomaus.github.io/SAELens/)
- [Neuronpedia](https://neuronpedia.org) – браузер ознак

## Архітектури SAE

| Архітектура | Опис | Випадок використання |
|--------------|-------------|----------|
| **Standard** | ReLU + L1 penalty | Загальне призначення |
| **Gated** | Learned gating mechanism | Кращий контроль розрідженості |
| **TopK** | Exactly K active features | Стабільна розрідженість |

```python
# TopK SAE (exactly 50 features active)
cfg = LanguageModelSAERunnerConfig(
    architecture="topk",
    activation_fn="topk",
    activation_fn_kwargs={"k": 50},
)
```