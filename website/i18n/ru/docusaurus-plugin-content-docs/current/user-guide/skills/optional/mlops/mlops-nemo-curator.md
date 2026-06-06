---
title: "Nemo Curator — ускоренная GPU обработка данных для обучения LLM"
sidebar_label: "Nemo Curator"
description: "GPU-ускоренная подготовка данных для обучения LLM"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Nemo Curator

GPU‑ускоренное **курирование** данных для обучения LLM. Поддерживает текст/изображения/видео/аудио. Предлагает нечеткую дедупликацию (16× быстрее), фильтрацию качества (30+ эвристик), семантическую дедупликацию, удаление PII, обнаружение NSFW. Масштабируется на несколько GPU с RAPIDS. Используется для подготовки высококачественных обучающих наборов, очистки веб‑данных или дедупликации больших корпусов.

## Метаданные навыка

| | |
|---|---|
| Source | Optional — install with `hermes skills install official/mlops/nemo-curator` |
| Path | `optional-skills/mlops/nemo-curator` |
| Version | `1.0.0` |
| Author | Orchestra Research |
| License | MIT |
| Dependencies | `nemo-curator`, `cudf`, `dask`, `rapids` |
| Platforms | linux, macos |
| Tags | `Data Processing`, `NeMo Curator`, `Data Curation`, `GPU Acceleration`, `Deduplication`, `Quality Filtering`, `NVIDIA`, `RAPIDS`, `PII Redaction`, `Multimodal`, `LLM Training Data` |

## Ссылка: полный SKILL.md

:::info
Ниже представлено полное определение навыка, которое Hermes загружает при срабатывании этого навыка. Это то, что агент видит как инструкции, когда навык активен.
:::

# NeMo Curator — GPU‑ускоренное курирование данных

Набор инструментов NVIDIA для подготовки высококачественных обучающих данных для LLM.

## Когда использовать NeMo Curator

**Используй NeMo Curator, когда:**
- Подготавливаешь обучающие данные LLM из веб‑скрейпов (Common Crawl)
- Нужна быстрая дедупликация (16× быстрее, чем на CPU)
- Курируешь мультимодальные наборы (текст, изображения, видео, аудио)
- Фильтруешь низкокачественный или токсичный контент
- Требуется масштабировать обработку данных на кластер GPU

**Производительность**:
- **16× быстрее** нечеткой дедупликации (8 TB RedPajama v2)
- **40 % ниже TCO** по сравнению с альтернативами на CPU
- **Почти линейное масштабирование** по узлам GPU

**Используй альтернативы вместо**:
- **datatrove**: обработка данных на CPU, open‑source
- **dolma**: набор инструментов данных от Allen AI
- **Ray Data**: общая обработка данных ML (без фокуса на курировании)

## Быстрый старт

### Установка

```bash
# Text curation (CUDA 12)
uv pip install "nemo-curator[text_cuda12]"

# All modalities
uv pip install "nemo-curator[all_cuda12]"

# CPU-only (slower)
uv pip install "nemo-curator[cpu]"
```

### Базовый конвейер текстового курирования

```python
from nemo_curator import ScoreFilter, Modify
from nemo_curator.datasets import DocumentDataset
import pandas as pd

# Load data
df = pd.DataFrame({"text": ["Good document", "Bad doc", "Excellent text"]})
dataset = DocumentDataset(df)

# Quality filtering
def quality_score(doc):
    return len(doc["text"].split()) > 5  # Filter short docs

filtered = ScoreFilter(quality_score)(dataset)

# Deduplication
from nemo_curator.modules import ExactDuplicates
deduped = ExactDuplicates()(filtered)

# Save
deduped.to_parquet("curated_data/")
```

## Конвейер курирования данных

### Этап 1: Фильтрация качества

```python
from nemo_curator.filters import (
    WordCountFilter,
    RepeatedLinesFilter,
    UrlRatioFilter,
    NonAlphaNumericFilter
)

# Apply 30+ heuristic filters
from nemo_curator import ScoreFilter

# Word count filter
dataset = dataset.filter(WordCountFilter(min_words=50, max_words=100000))

# Remove repetitive content
dataset = dataset.filter(RepeatedLinesFilter(max_repeated_line_fraction=0.3))

# URL ratio filter
dataset = dataset.filter(UrlRatioFilter(max_url_ratio=0.2))
```

### Этап 2: Дедупликация

**Точная дедупликация**:
```python
from nemo_curator.modules import ExactDuplicates

# Remove exact duplicates
deduped = ExactDuplicates(id_field="id", text_field="text")(dataset)
```

**Нечеткая дедупликация** (16× быстрее на GPU):
```python
from nemo_curator.modules import FuzzyDuplicates

# MinHash + LSH deduplication
fuzzy_dedup = FuzzyDuplicates(
    id_field="id",
    text_field="text",
    num_hashes=260,      # MinHash parameters
    num_buckets=20,
    hash_method="md5"
)

deduped = fuzzy_dedup(dataset)
```

**Семантическая дедупликация**:
```python
from nemo_curator.modules import SemanticDuplicates

# Embedding-based deduplication
semantic_dedup = SemanticDuplicates(
    id_field="id",
    text_field="text",
    embedding_model="sentence-transformers/all-MiniLM-L6-v2",
    threshold=0.8  # Cosine similarity threshold
)

deduped = semantic_dedup(dataset)
```

### Этап 3: Удаление PII

```python
from nemo_curator.modules import Modify
from nemo_curator.modifiers import PIIRedactor

# Redact personally identifiable information
pii_redactor = PIIRedactor(
    supported_entities=["EMAIL_ADDRESS", "PHONE_NUMBER", "PERSON", "LOCATION"],
    anonymize_action="replace"  # or "redact"
)

redacted = Modify(pii_redactor)(dataset)
```

### Этап 4: Фильтрация классификатором

```python
from nemo_curator.classifiers import QualityClassifier

# Quality classification
quality_clf = QualityClassifier(
    model_path="nvidia/quality-classifier-deberta",
    batch_size=256,
    device="cuda"
)

# Filter low-quality documents
high_quality = dataset.filter(lambda doc: quality_clf(doc["text"]) > 0.5)
```

## GPU‑ускорение

### Производительность GPU vs CPU

| Operation | CPU (16 cores) | GPU (A100) | Speedup |
|-----------|----------------|------------|---------|
| Fuzzy dedup (8TB) | 120 hours | 7.5 hours | 16× |
| Exact dedup (1TB) | 8 hours | 0.5 hours | 16× |
| Quality filtering | 2 hours | 0.2 hours | 10× |

### Масштабирование на несколько GPU

```python
from nemo_curator import get_client
import dask_cuda

# Initialize GPU cluster
client = get_client(cluster_type="gpu", n_workers=8)

# Process with 8 GPUs
deduped = FuzzyDuplicates(...)(dataset)
```

## Мультимодальное курирование

### Курирование изображений

```python
from nemo_curator.image import (
    AestheticFilter,
    NSFWFilter,
    CLIPEmbedder
)

# Aesthetic scoring
aesthetic_filter = AestheticFilter(threshold=5.0)
filtered_images = aesthetic_filter(image_dataset)

# NSFW detection
nsfw_filter = NSFWFilter(threshold=0.9)
safe_images = nsfw_filter(filtered_images)

# Generate CLIP embeddings
clip_embedder = CLIPEmbedder(model="openai/clip-vit-base-patch32")
image_embeddings = clip_embedder(safe_images)
```

### Курирование видео

```python
from nemo_curator.video import (
    SceneDetector,
    ClipExtractor,
    InternVideo2Embedder
)

# Detect scenes
scene_detector = SceneDetector(threshold=27.0)
scenes = scene_detector(video_dataset)

# Extract clips
clip_extractor = ClipExtractor(min_duration=2.0, max_duration=10.0)
clips = clip_extractor(scenes)

# Generate embeddings
video_embedder = InternVideo2Embedder()
video_embeddings = video_embedder(clips)
```

### Курирование аудио

```python
from nemo_curator.audio import (
    ASRInference,
    WERFilter,
    DurationFilter
)

# ASR transcription
asr = ASRInference(model="nvidia/stt_en_fastconformer_hybrid_large_pc")
transcribed = asr(audio_dataset)

# Filter by WER (word error rate)
wer_filter = WERFilter(max_wer=0.3)
high_quality_audio = wer_filter(transcribed)

# Duration filtering
duration_filter = DurationFilter(min_duration=1.0, max_duration=30.0)
filtered_audio = duration_filter(high_quality_audio)
```

## Распространённые шаблоны

### Курирование веб‑скрейпов (Common Crawl)

```python
from nemo_curator import ScoreFilter, Modify
from nemo_curator.filters import *
from nemo_curator.modules import *
from nemo_curator.datasets import DocumentDataset

# Load Common Crawl data
dataset = DocumentDataset.read_parquet("common_crawl/*.parquet")

# Pipeline
pipeline = [
    # 1. Quality filtering
    WordCountFilter(min_words=100, max_words=50000),
    RepeatedLinesFilter(max_repeated_line_fraction=0.2),
    SymbolToWordRatioFilter(max_symbol_to_word_ratio=0.3),
    UrlRatioFilter(max_url_ratio=0.3),

    # 2. Language filtering
    LanguageIdentificationFilter(target_languages=["en"]),

    # 3. Deduplication
    ExactDuplicates(id_field="id", text_field="text"),
    FuzzyDuplicates(id_field="id", text_field="text", num_hashes=260),

    # 4. PII redaction
    PIIRedactor(),

    # 5. NSFW filtering
    NSFWClassifier(threshold=0.8)
]

# Execute
for stage in pipeline:
    dataset = stage(dataset)

# Save
dataset.to_parquet("curated_common_crawl/")
```

### Распределённая обработка

```python
from nemo_curator import get_client
from dask_cuda import LocalCUDACluster

# Multi-GPU cluster
cluster = LocalCUDACluster(n_workers=8)
client = get_client(cluster=cluster)

# Process large dataset
dataset = DocumentDataset.read_parquet("s3://large_dataset/*.parquet")
deduped = FuzzyDuplicates(...)(dataset)

# Cleanup
client.close()
cluster.close()
```

## Бенчмарки производительности

### Нечеткая дедупликация (8 TB RedPajama v2)

- **CPU (256 cores)**: 120 hours
- **GPU (8× A100)**: 7.5 hours
- **Speedup**: 16×

### Точная дедупликация (1 TB)

- **CPU (64 cores)**: 8 hours
- **GPU (4× A100)**: 0.5 hours
- **Speedup**: 16×

### Фильтрация качества (100 GB)

- **CPU (32 cores)**: 2 hours
- **GPU (2× A100)**: 0.2 hours
- **Speedup**: 10×

## Сравнение стоимости

**Курирование на CPU** (AWS c5.18xlarge × 10):
- Стоимость: $3.60/hour × 10 = $36/hour
- Время для 8 TB: 120 hours
- **Итого**: $4 320

**Курирование на GPU** (AWS p4d.24xlarge × 2):
- Стоимость: $32.77/hour × 2 = $65.54/hour
- Время для 8 TB: 7.5 hours
- **Итого**: $491.55

**Экономия**: 89 % сокращения ($3 828 saved)

## Поддерживаемые форматы данных

- **Ввод**: Parquet, JSONL, CSV
- **Вывод**: Parquet (рекомендовано), JSONL
- **WebDataset**: TAR‑архивы для мультимодального контента

## Сценарии использования

**Продакшн‑развёртывания**:
- NVIDIA использовала NeMo Curator для подготовки данных обучения Nemotron‑4
- Открытые наборы данных: RedPajama v2, The Pile

## Ссылки

- **[Filtering Guide](https://github.com/NousResearch/hermes-agent/blob/main/optional-skills/mlops/nemo-curator/references/filtering.md)** — 30+ фильтров качества, эвристики
- **[Deduplication Guide](https://github.com/NousResearch/hermes-agent/blob/main/optional-skills/mlops/nemo-curator/references/deduplication.md)** — методы точной, нечеткой и семантической дедупликации

## Ресурсы

- **GitHub**: https://github.com/NVIDIA/NeMo-Curator ⭐ 500+
- **Docs**: https://docs.nvidia.com/nemo-framework/user-guide/latest/datacuration/
- **Version**: 0.4.0+
- **License**: Apache 2.0