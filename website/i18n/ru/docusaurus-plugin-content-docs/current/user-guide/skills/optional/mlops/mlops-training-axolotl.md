---
title: "Axolotl — Axolotl: YAML LLM тонкая настройка (LoRA, DPO, GRPO)"
sidebar_label: "Axolotl"
description: "Axolotl: тонкая настройка LLM в YAML (LoRA, DPO, GRPO)"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Axolotl

Axolotl: YAML LLM fine-tuning (LoRA, DPO, GRPO).

## Метаданные навыка

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

## Ссылка: полный SKILL.md

:::info
Ниже представлено полное определение навыка, которое Hermes загружает, когда этот навык активирован. Это то, что агент видит как инструкции при работе навыка.
:::

# Навык Axolotl

## Что внутри

Экспертные рекомендации по дообучению LLM с помощью Axolotl — YAML‑конфиги, более 100 моделей, LoRA/QLoRA, DPO/KTO/ORPO/GRPO, поддержка мультимодальности.

Всеобъемлющая помощь в разработке Axolotl, сгенерированная из официальной документации.

## Когда использовать этот навык

Этот навык следует активировать, когда:
- Работаешь с Axolotl
- Задаёшь вопросы о функциях или API Axolotl
- Реализуешь решения на основе Axolotl
- Отлаживаешь код Axolotl
- Изучаешь лучшие практики Axolotl

## Быстрая справка

### Распространённые шаблоны

**Шаблон 1:** Чтобы убедиться, что для задачи обучения доступны приемлемые скорости передачи данных, запуск NCCL Tests может помочь выявить узкие места, например:

```
./build/all_reduce_perf -b 8 -e 128M -f 2 -g 3
```

**Шаблон 2:** Настрой свою модель на использование FSDP в yaml‑файле Axolotl. Например:

```
fsdp_version: 2
fsdp_config:
  offload_params: true
  state_dict_type: FULL_STATE_DICT
  auto_wrap_policy: TRANSFORMER_BASED_WRAP
  transformer_layer_cls_to_wrap: LlamaDecoderLayer
  reshard_after_forward: true
```

**Шаблон 3:** `context_parallel_size` должен быть делителем общего количества GPU. Например:

```
context_parallel_size
```

**Шаблон 4:** Например:
- При 8 GPU и без параллелизма последовательностей: 8 разных батчей обрабатываются за шаг — по одному на каждый GPU
- При 8 GPU и `context_parallel_size=4`: только 2 разных батча обрабатываются за шаг (каждый разбит на 4 GPU)
- Если `micro_batch_size` на GPU = 2, глобальный размер батча уменьшается с 16 до 4

```
context_parallel_size=4
```

**Шаблон 5:** Установка `save_compressed: true` в конфигурации включает сохранение моделей в сжатом формате, что:
- Сокращает использование дискового пространства примерно на 40 %
- Сохраняет совместимость с vLLM для ускоренного вывода
- Сохраняет совместимость с llmcompressor для дальнейшей оптимизации (пример: квантизация)

```
save_compressed: true
```

**Шаблон 6:** Обрати внимание: не обязательно размещать интеграцию в папке `integrations`. Она может находиться в любом месте, при условии, что установленный пакет доступен в твоём python‑окружении. См. пример в репозитории: https://github.com/axolotl-ai-cloud/diff-transformer

```
integrations
```

**Шаблон 7:** Обрабатывай как одиночные примеры, так и батчированные данные.
- одиночный пример: `sample['input_ids']` — `list[int]`
- батчированные данные: `sample['input_ids']` — `list[list[int]]`

```
utils.trainer.drop_long_seq(sample, sequence_len=2048, min_sequence_len=2)
```

### Примеры кода

**Пример 1** (python):
```python
cli.cloud.modal_.ModalCloud(config, app=None)
```

**Пример 2** (python):
```python
cli.cloud.modal_.run_cmd(cmd, run_folder, volumes=None)
```

**Пример 3** (python):
```python
core.trainers.base.AxolotlTrainer(
    *_args,
    bench_data_collator=None,
    eval_data_collator=None,
    dataset_tags=None,
    **kwargs,
)
```

**Пример 4** (python):
```python
core.trainers.base.AxolotlTrainer.log(logs, start_time=None)
```

**Пример 5** (python):
```python
prompt_strategies.input_output.RawInputOutputPrompter()
```

## Справочные файлы

В этом навыке включена полная документация в `references/`:

- **api.md** — документация API
- **dataset-formats.md** — документация форматов наборов данных
- **other.md** — прочая документация

Используй `view` для чтения конкретных справочных файлов, когда нужна детальная информация.

## Работа с этим навыком

### Для новичков
Начни с файлов `getting_started` или `tutorials` в разделе справки для освоения базовых концепций.

### Для конкретных функций
Обратись к соответствующему файлу справки (api, guides и т.д.) для получения подробностей.

### Для примеров кода
Раздел быстрой справки выше содержит распространённые шаблоны, извлечённые из официальных документов.

## Ресурсы

### references/
Организованная документация, извлечённая из официальных источников. Эти файлы содержат:
- Подробные объяснения
- Примеры кода с аннотациями языка
- Ссылки на оригинальную документацию
- Оглавление для быстрой навигации

### scripts/
Помести сюда вспомогательные скрипты для типовых задач автоматизации.

### assets/
Помести сюда шаблоны, шаблонный код или примерные проекты.

## Примечания

- Этот навык был автоматически сгенерирован из официальной документации
- Справочные файлы сохраняют структуру и примеры из исходных документов
- Примеры кода включают определение языка для лучшего подсвечивания синтаксиса
- Шаблоны быстрой справки извлечены из типовых примеров использования в документах

## Обновление

Чтобы обновить навык с учётом новой документации:
1. Перезапусти скрейпер с теми же настройками
2. Навык будет пересобран с актуальной информацией