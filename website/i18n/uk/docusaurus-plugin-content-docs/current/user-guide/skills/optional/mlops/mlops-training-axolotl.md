---
title: "Axolotl — Axolotl: YAML LLM тонке налаштування (LoRA, DPO, GRPO)"
sidebar_label: "Axolotl"
description: "Axolotl: YAML тонке налаштування LLM (LoRA, DPO, GRPO)"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Axolotl

Axolotl: YAML LLM fine-tuning (LoRA, DPO, GRPO).

## Метадані навички

| | |
|---|---|
| Source | Optional — install with `hermes skills install official/mlops/axolotl` |
| Path | `optional-skills/mlops/training/axolotl` |
| Version | `1.0.0` |
| Author | Orchestra Research |
| License | MIT |
| Dependencies | `axolotl`, `torch`, `transformers`, `datasets`, `peft`, `accelerate`, `deepspeed` |
| Platforms | linux, macos |
| Tags | `Fine-Tuning`, `Axolotl`, `LLM`, `LoRA`, `QLoRA`, `DPO`, `KTO`, `ORPO`, `GRPO`, `YAML`, `HuggingFace`, `DeepSpeed`, `Multimodal` |

## Довідка: повний SKILL.md

:::info
Нижче наведено повне визначення навички, яке Hermes завантажує, коли ця навичка активується. Це те, що агент бачить як інструкції, коли навичка активна.
:::

# Навичка Axolotl

## Що всередині

Експертні рекомендації щодо тонкого налаштування LLM за допомогою Axolotl — YAML‑конфіги, 100+ моделей, LoRA/QLoRA, DPO/KTO/ORPO/GRPO, підтримка мультимодальності.

Всеосяжна допомога у розробці Axolotl, згенерована з офіційної документації.

## Коли використовувати цю навичку

Цю навичку слід активувати, коли:
- Працюєш з Axolotl
- Питаєш про функції або API Axolotl
- Реалізуєш рішення на базі Axolotl
- Налагоджуєш код Axolotl
- Вивчаєш кращі практики Axolotl

## Швидка довідка

### Поширені шаблони

**Шаблон 1:** Щоб перевірити, чи існують прийнятні швидкості передачі даних для вашого навчального завдання, запуск NCCL Tests може допомогти виявити вузькі місця, наприклад:

```
./build/all_reduce_perf -b 8 -e 128M -f 2 -g 3
```

**Шаблон 2:** Налаштуйте вашу модель на використання FSDP у yaml‑файлі Axolotl. Наприклад:

```
fsdp_version: 2
fsdp_config:
  offload_params: true
  state_dict_type: FULL_STATE_DICT
  auto_wrap_policy: TRANSFORMER_BASED_WRAP
  transformer_layer_cls_to_wrap: LlamaDecoderLayer
  reshard_after_forward: true
```

**Шаблон 3:** `context_parallel_size` має бути дільником загальної кількості GPU. Наприклад:

```
context_parallel_size
```

**Шаблон 4:** Приклад:
- При 8 GPU і без паралелізму послідовностей: 8 різних батчів обробляються за крок.
- При 8 GPU і `context_parallel_size=4`: лише 2 різних батчі обробляються за крок (кожен розподілений між 4 GPU).
- Якщо ваш `micro_batch_size` на GPU дорівнює 2, глобальний розмір батчу зменшується з 16 до 4.

```
context_parallel_size=4
```

**Шаблон 5:** Встановлення `save_compressed: true` у вашій конфігурації дозволяє зберігати моделі у стисненому форматі, що:
- Зменшує використання дискового простору приблизно на 40 %
- Підтримує сумісність з vLLM для прискореного інференсу
- Підтримує сумісність з llmcompressor для подальшої оптимізації (наприклад, квантування)

```
save_compressed: true
```

**Шаблон 6:** Примітка: не обов’язково розміщувати вашу інтеграцію у папці `integrations`. Вона може бути в будь‑якому місці, доки встановлена в пакеті вашого python‑середовища. Приклад можна знайти в цьому репозиторії: https://github.com/axolotl-ai-cloud/diff-transformer

```
integrations
```

**Шаблон 7:** Обробка як одиничних прикладів, так і батчованих даних.
- Одиничний приклад: `sample[‘input_ids’]` — це `list[int]`
- Батчовані дані: `sample[‘input_ids’]` — це `list[list[int]]`

```
utils.trainer.drop_long_seq(sample, sequence_len=2048, min_sequence_len=2)
```

### Приклади коду

**Приклад 1** (python):
```python
cli.cloud.modal_.ModalCloud(config, app=None)
```

**Приклад 2** (python):
```python
cli.cloud.modal_.run_cmd(cmd, run_folder, volumes=None)
```

**Приклад 3** (python):
```python
core.trainers.base.AxolotlTrainer(
    *_args,
    bench_data_collator=None,
    eval_data_collator=None,
    dataset_tags=None,
    **kwargs,
)
```

**Приклад 4** (python):
```python
core.trainers.base.AxolotlTrainer.log(logs, start_time=None)
```

**Приклад 5** (python):
```python
prompt_strategies.input_output.RawInputOutputPrompter()
```

## Довідкові файли

Ця навичка включає всеосяжну документацію у `references/`:

- **api.md** — документація API
- **dataset-formats.md** — документація форматів наборів даних
- **other.md** — інша документація

Використовуй `view` для читання конкретних довідкових файлів, коли потрібна детальна інформація.

## Робота з цією навичкою

### Для початківців
Почни з файлів довідки `getting_started` або `tutorials` для базових концепцій.

### Для конкретних функцій
Використовуй відповідний файл довідки за категорією (api, guides тощо) для детальної інформації.

### Для прикладів коду
Розділ швидкої довідки вище містить поширені шаблони, витягнуті з офіційної документації.

## Ресурси

### references/
Організована документація, витягнута з офіційних джерел. Ці файли містять:
- Детальні пояснення
- Приклади коду з позначенням мови
- Посилання на оригінальну документацію
- Зміст для швидкої навігації

### scripts/
Додай допоміжні скрипти тут для типових автоматизаційних завдань.

### assets/
Додай шаблони, boilerplate або прикладні проекти тут.

## Примітки

- Ця навичка була автоматично згенерована з офіційної документації
- Довідкові файли зберігають структуру та приклади з вихідних документів
- Приклади коду включають визначення мови для кращого підсвічування синтаксису
- Шаблони швидкої довідки витягнуті з типових прикладів використання в документації

## Оновлення

Щоб оновити цю навичку новою документацією:
1. Перезапусти скрейпер з тією ж конфігурацією
2. Навичка буде перебудована з останньою інформацією