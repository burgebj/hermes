---
title: "Faiss — библиотека Facebook для эффективного поиска сходства и кластеризации плотных векторов"
sidebar_label: "Faiss"
description: "библиотека Facebook для эффективного поиска похожих элементов и кластеризации плотных векторов"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Faiss

Библиотека Facebook для эффективного поиска похожих векторов и кластеризации плотных векторов. Поддерживает миллиарды векторов, ускорение на GPU и различные типы индексов (Flat, IVF, HNSW). Используется для быстрого поиска k‑NN, масштабного извлечения векторов или когда нужен чистый поиск похожести без метаданных. Лучший выбор для высокопроизводительных приложений.

## Метаданные навыка

| | |
|---|---|
| Source | Optional — install with `hermes skills install official/mlops/faiss` |
| Path | `optional-skills/mlops/faiss` |
| Version | `1.0.0` |
| Author | Orchestra Research |
| License | MIT |
| Dependencies | `faiss-cpu`, `faiss-gpu`, `numpy` |
| Platforms | linux, macos |
| Tags | `RAG`, `FAISS`, `Similarity Search`, `Vector Search`, `Facebook AI`, `GPU Acceleration`, `Billion-Scale`, `K-NN`, `HNSW`, `High Performance`, `Large Scale` |

## Ссылка: полный SKILL.md

:::info
Ниже представлено полное определение навыка, которое Hermes загружает при срабатывании этого навыка. Это то, что агент видит как инструкции, когда навык активен.
:::

# FAISS — эффективный поиск похожести

Библиотека Facebook AI для поиска похожих векторов в масштабе миллиардов векторов.

## Когда использовать FAISS

**Используй FAISS, когда:**
- Нужен быстрый поиск похожести в больших наборах векторов (миллионы/миллиарды)
- Требуется ускорение на GPU
- Требуется чистая векторная похожесть (без фильтрации по метаданным)
- Критичны высокая пропускная способность и низкая задержка
- Необходима офлайн/пакетная обработка эмбеддингов

**Метрики**:
- **31 700+ звёзд на GitHub**
- Meta/Facebook AI Research
- **Обрабатывает миллиарды векторов**
- **C++** с привязками к Python

**Используй альтернативы вместо FAISS**:
- **Chroma/Pinecone**: нужна фильтрация по метаданным
- **Weaviate**: нужны полноценные возможности базы данных
- **Annoy**: проще, меньше функций

## Быстрый старт

### Установка

```bash
# CPU only
pip install faiss-cpu

# GPU support
pip install faiss-gpu
```

### Базовое использование

```python
import faiss
import numpy as np

# Create sample data (1000 vectors, 128 dimensions)
d = 128
nb = 1000
vectors = np.random.random((nb, d)).astype('float32')

# Create index
index = faiss.IndexFlatL2(d)  # L2 distance
index.add(vectors)             # Add vectors

# Search
k = 5  # Find 5 nearest neighbors
query = np.random.random((1, d)).astype('float32')
distances, indices = index.search(query, k)

print(f"Nearest neighbors: {indices}")
print(f"Distances: {distances}")
```

## Типы индексов

### 1. Flat (точный поиск)

```python
# L2 (Euclidean) distance
index = faiss.IndexFlatL2(d)

# Inner product (cosine similarity if normalized)
index = faiss.IndexFlatIP(d)

# Slowest, most accurate
```

### 2. IVF (инвертированный файл) — быстрое приближённое решение

```python
# Create quantizer
quantizer = faiss.IndexFlatL2(d)

# IVF index with 100 clusters
nlist = 100
index = faiss.IndexIVFFlat(quantizer, d, nlist)

# Train on data
index.train(vectors)

# Add vectors
index.add(vectors)

# Search (nprobe = clusters to search)
index.nprobe = 10
distances, indices = index.search(query, k)
```

### 3. HNSW (иерархический NSW) — лучшая точность/скорость

```python
# HNSW index
M = 32  # Number of connections per layer
index = faiss.IndexHNSWFlat(d, M)

# No training needed
index.add(vectors)

# Search
distances, indices = index.search(query, k)
```

### 4. Product Quantization — экономия памяти

```python
# PQ reduces memory by 16-32×
m = 8   # Number of subquantizers
nbits = 8
index = faiss.IndexPQ(d, m, nbits)

# Train and add
index.train(vectors)
index.add(vectors)
```

## Сохранение и загрузка

```python
# Save index
faiss.write_index(index, "large.index")

# Load index
index = faiss.read_index("large.index")

# Continue using
distances, indices = index.search(query, k)
```

## Ускорение на GPU

```python
# Single GPU
res = faiss.StandardGpuResources()
index_cpu = faiss.IndexFlatL2(d)
index_gpu = faiss.index_cpu_to_gpu(res, 0, index_cpu)  # GPU 0

# Multi-GPU
index_gpu = faiss.index_cpu_to_all_gpus(index_cpu)

# 10-100× faster than CPU
```

## Интеграция с LangChain

```python
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings

# Create FAISS vector store
vectorstore = FAISS.from_documents(docs, OpenAIEmbeddings())

# Save
vectorstore.save_local("faiss_index")

# Load
vectorstore = FAISS.load_local(
    "faiss_index",
    OpenAIEmbeddings(),
    allow_dangerous_deserialization=True
)

# Search
results = vectorstore.similarity_search("query", k=5)
```

## Интеграция с LlamaIndex

```python
from llama_index.vector_stores.faiss import FaissVectorStore
import faiss

# Create FAISS index
d = 1536
faiss_index = faiss.IndexFlatL2(d)

vector_store = FaissVectorStore(faiss_index=faiss_index)
```

## Лучшие практики

1. **Выбирай правильный тип индекса** — Flat для &lt;10 K, IVF для 10 K‑1 M, HNSW для качества
2. **Нормализуй для косинуса** — используй `IndexFlatIP` с нормализованными векторами
3. **Используй GPU для больших наборов** — 10‑100× быстрее
4. **Сохраняй обученные индексы** — обучение дорогостоящее
5. **Тонко настраивай nprobe/ef_search** — баланс скорости и точности
6. **Следи за памятью** — PQ для больших наборов
7. **Пакетные запросы** — лучшая загрузка GPU

## Производительность

| Тип индекса | Время построения | Время поиска | Память | Точность |
|------------|-------------------|--------------|--------|----------|
| Flat | Быстро | Медленно | Высокая | 100% |
| IVF | Средне | Быстро | Средняя | 95‑99% |
| HNSW | Медленно | Самое быстрое | Высокая | 99% |
| PQ | Средне | Быстро | Низкая | 90‑95% |

## Ресурсы

- **GitHub**: https://github.com/facebookresearch/faiss ⭐ 31,700+
- **Wiki**: https://github.com/facebookresearch/faiss/wiki
- **License**: MIT