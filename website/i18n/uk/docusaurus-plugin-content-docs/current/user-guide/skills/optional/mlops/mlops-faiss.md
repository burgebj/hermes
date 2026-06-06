---
title: "Faiss — бібліотека Facebook для ефективного пошуку за схожістю та кластеризації густих векторів"
sidebar_label: "Faiss"
description: "Бібліотека Facebook для ефективного пошуку схожості та кластеризації густих векторів"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Faiss

Бібліотека Facebook для ефективного пошуку схожості та кластеризації густих векторів. Підтримує мільярди векторів, прискорення на GPU та різні типи індексів (Flat, IVF, HNSW). Використовуй для швидкого k‑NN пошуку, масштабного отримання векторів або коли потрібен чистий пошук схожості без метаданих. Найкраще підходить для високопродуктивних застосувань.

## Метадані навички

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

## Довідка: повний SKILL.md

:::info
Нижче наведено повне визначення навички, яке Hermes завантажує, коли ця навичка активована. Це те, що агент бачить як інструкції під час роботи навички.
:::

# FAISS — ефективний пошук схожості

Бібліотека Facebook AI для пошуку схожості векторів у масштабі мільярдів.

## Коли використовувати FAISS

**Використовуй FAISS, коли:**
- Потрібен швидкий пошук схожості у великих наборах векторів (мільйони/мільярди)
- Потрібне прискорення на GPU
- Потрібна чиста векторна схожість (без фільтрації метаданих)
- Високий пропускний потік та низька затримка критичні
- Офлайн/пакетна обробка ембеддінгів

**Метрики**:
- **31 700+ зірок на GitHub**
- Meta/Facebook AI Research
- **Працює з мільярдами векторів**
- **C++** з прив’язками до Python

**Використовуй альтернативи, якщо**:
- **Chroma/Pinecone**: потрібна фільтрація метаданих
- **Weaviate**: потрібні повноцінні можливості бази даних
- **Annoy**: простіший, менше функцій

## Швидкий старт

### Встановлення

```bash
# CPU only
pip install faiss-cpu

# GPU support
pip install faiss-gpu
```

### Базове використання

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

## Типи індексів

### 1. Flat (точний пошук)

```python
# L2 (Euclidean) distance
index = faiss.IndexFlatL2(d)

# Inner product (cosine similarity if normalized)
index = faiss.IndexFlatIP(d)

# Slowest, most accurate
```

### 2. IVF (inverted file) — швидкий апроксимаційний

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

### 3. HNSW (Hierarchical NSW) — найкраща якість/швидкість

```python
# HNSW index
M = 32  # Number of connections per layer
index = faiss.IndexHNSWFlat(d, M)

# No training needed
index.add(vectors)

# Search
distances, indices = index.search(query, k)
```

### 4. Product Quantization — ефективне використання пам’яті

```python
# PQ reduces memory by 16-32×
m = 8   # Number of subquantizers
nbits = 8
index = faiss.IndexPQ(d, m, nbits)

# Train and add
index.train(vectors)
index.add(vectors)
```

## Збереження та завантаження

```python
# Save index
faiss.write_index(index, "large.index")

# Load index
index = faiss.read_index("large.index")

# Continue using
distances, indices = index.search(query, k)
```

## Прискорення на GPU

```python
# Single GPU
res = faiss.StandardGpuResources()
index_cpu = faiss.IndexFlatL2(d)
index_gpu = faiss.index_cpu_to_gpu(res, 0, index_cpu)  # GPU 0

# Multi-GPU
index_gpu = faiss.index_cpu_to_all_gpus(index_cpu)

# 10-100× faster than CPU
```

## Інтеграція з LangChain

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

## Інтеграція з LlamaIndex

```python
from llama_index.vector_stores.faiss import FaissVectorStore
import faiss

# Create FAISS index
d = 1536
faiss_index = faiss.IndexFlatL2(d)

vector_store = FaissVectorStore(faiss_index=faiss_index)
```

## Кращі практики

1. **Вибирай правильний тип індексу** — Flat для &lt;10 K, IVF для 10 K‑1 M, HNSW для якості
2. **Нормалізуй для косинуса** — використай IndexFlatIP з нормалізованими векторами
3. **Використовуй GPU для великих наборів** — 10‑100× швидше
4. **Зберігай навчені індекси** — навчання дороговартісне
5. **Тюнінг nprobe/ef_search** — баланс швидкості та точності
6. **Контролюй пам’ять** — PQ для великих наборів
7. **Пакетні запити** — краща використання GPU

## Продуктивність

| Тип індексу | Час побудови | Час пошуку | Пам’ять | Точність |
|------------|--------------|------------|---------|----------|
| Flat | Швидко | Повільно | Висока | 100% |
| IVF | Середньо | Швидко | Середня | 95‑99% |
| HNSW | Повільно | Найшвидше | Висока | 99% |
| PQ | Середньо | Швидко | Низька | 90‑95% |

## Ресурси

- **GitHub**: https://github.com/facebookresearch/faiss ⭐ 31,700+
- **Wiki**: https://github.com/facebookresearch/faiss/wiki
- **License**: MIT