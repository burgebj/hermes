---
title: "Qdrant Vector Search — Высокопроизводительный движок поиска векторного сходства для RAG и семантического поиска"
sidebar_label: "Qdrant Vector Search"
description: "Высокопроизводительный движок поиска векторного сходства для RAG и семантического поиска"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Qdrant Vector Search

Высокопроизводительный движок поиска векторного сходства для RAG и семантического поиска. Используй при построении производственных RAG‑систем, требующих быстрого поиска ближайших соседей, гибридного поиска с фильтрацией или масштабируемого векторного хранилища с производительностью на базе Rust.

## Метаданные навыка

| | |
|---|---|
| Source | Optional — install with `hermes skills install official/mlops/qdrant` |
| Path | `optional-skills/mlops/qdrant` |
| Version | `1.0.0` |
| Author | Orchestra Research |
| License | MIT |
| Dependencies | `qdrant-client>=1.12.0` |
| Platforms | linux, macos, windows |
| Tags | `RAG`, `Vector Search`, `Qdrant`, `Semantic Search`, `Embeddings`, `Similarity Search`, `HNSW`, `Production`, `Distributed` |

## Reference: full SKILL.md

:::info
The following is the complete skill definition that Hermes loads when this skill is triggered. This is what the agent sees as instructions when the skill is active.
:::

# Qdrant — Engine поиска векторного сходства

Высокопроизводительная векторная база данных, написанная на Rust, для производственного RAG и семантического поиска.

## Когда использовать Qdrant

**Qdrant подходит, когда:**
- Нужно построить производственную RAG‑систему с низкой задержкой
- Требуется гибридный поиск (векторы + фильтрация по метаданным)
- Необходим горизонтальный масштабирование с шардингом/репликацией
- Желательно развертывание on‑premise с полным контролем над данными
- Нужно хранить несколько векторов на запись (плотные + разреженные)
- Требуется система рекомендаций в реальном времени

**Ключевые возможности:**
- **Rust-powered**: безопасная память, высокая производительность
- **Rich filtering**: фильтрация по любому полю payload во время поиска
- **Multiple vectors**: плотные, разреженные, мульти‑плотные векторы на точку
- **Quantization**: скалярная, продуктовая, бинарная для экономии памяти
- **Distributed**: консенсус Raft, шардинг, репликация
- **REST + gRPC**: оба API с полной функциональной эквивалентностью

**Альтернативы:**
- **Chroma**: более простая настройка, встраиваемые сценарии
- **FAISS**: максимальная сырая скорость, исследования/пакетная обработка
- **Pinecone**: полностью управляемый сервис, предпочтительно при нулевых операционных затратах
- **Weaviate**: предпочтение GraphQL, встроенные векторизаторы

## Быстрый старт

### Установка

```bash
# Python client
pip install qdrant-client

# Docker (recommended for development)
docker run -p 6333:6333 -p 6334:6334 qdrant/qdrant

# Docker with persistent storage
docker run -p 6333:6333 -p 6334:6334 \
    -v $(pwd)/qdrant_storage:/qdrant/storage \
    qdrant/qdrant
```

### Базовое использование

```python
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

# Connect to Qdrant
client = QdrantClient(host="localhost", port=6333)

# Create collection
client.create_collection(
    collection_name="documents",
    vectors_config=VectorParams(size=384, distance=Distance.COSINE)
)

# Insert vectors with payload
client.upsert(
    collection_name="documents",
    points=[
        PointStruct(
            id=1,
            vector=[0.1, 0.2, ...],  # 384-dim vector
            payload={"title": "Doc 1", "category": "tech"}
        ),
        PointStruct(
            id=2,
            vector=[0.3, 0.4, ...],
            payload={"title": "Doc 2", "category": "science"}
        )
    ]
)

# Search with filtering
results = client.search(
    collection_name="documents",
    query_vector=[0.15, 0.25, ...],
    query_filter={
        "must": [{"key": "category", "match": {"value": "tech"}}]
    },
    limit=10
)

for point in results:
    print(f"ID: {point.id}, Score: {point.score}, Payload: {point.payload}")
```

## Основные концепции

### Points — базовая единица данных

```python
from qdrant_client.models import PointStruct

# Point = ID + Vector(s) + Payload
point = PointStruct(
    id=123,                              # Integer or UUID string
    vector=[0.1, 0.2, 0.3, ...],        # Dense vector
    payload={                            # Arbitrary JSON metadata
        "title": "Document title",
        "category": "tech",
        "timestamp": 1699900000,
        "tags": ["python", "ml"]
    }
)

# Batch upsert (recommended)
client.upsert(
    collection_name="documents",
    points=[point1, point2, point3],
    wait=True  # Wait for indexing
)
```

### Collections — контейнеры векторов

```python
from qdrant_client.models import VectorParams, Distance, HnswConfigDiff

# Create with HNSW configuration
client.create_collection(
    collection_name="documents",
    vectors_config=VectorParams(
        size=384,                        # Vector dimensions
        distance=Distance.COSINE         # COSINE, EUCLID, DOT, MANHATTAN
    ),
    hnsw_config=HnswConfigDiff(
        m=16,                            # Connections per node (default 16)
        ef_construct=100,                # Build-time accuracy (default 100)
        full_scan_threshold=10000        # Switch to brute force below this
    ),
    on_disk_payload=True                 # Store payload on disk
)

# Collection info
info = client.get_collection("documents")
print(f"Points: {info.points_count}, Vectors: {info.vectors_count}")
```

### Метрики расстояний

| Metric | Use Case | Range |
|--------|----------|-------|
| `COSINE` | Text embeddings, normalized vectors | 0 to 2 |
| `EUCLID` | Spatial data, image features | 0 to ∞ |
| `DOT` | Recommendations, unnormalized | -∞ to ∞ |
| `MANHATTAN` | Sparse features, discrete data | 0 to ∞ |

## Операции поиска

### Базовый поиск

```python
# Simple nearest neighbor search
results = client.search(
    collection_name="documents",
    query_vector=[0.1, 0.2, ...],
    limit=10,
    with_payload=True,
    with_vectors=False  # Don't return vectors (faster)
)
```

### Поиск с фильтрацией

```python
from qdrant_client.models import Filter, FieldCondition, MatchValue, Range

# Complex filtering
results = client.search(
    collection_name="documents",
    query_vector=query_embedding,
    query_filter=Filter(
        must=[
            FieldCondition(key="category", match=MatchValue(value="tech")),
            FieldCondition(key="timestamp", range=Range(gte=1699000000))
        ],
        must_not=[
            FieldCondition(key="status", match=MatchValue(value="archived"))
        ]
    ),
    limit=10
)

# Shorthand filter syntax
results = client.search(
    collection_name="documents",
    query_vector=query_embedding,
    query_filter={
        "must": [
            {"key": "category", "match": {"value": "tech"}},
            {"key": "price", "range": {"gte": 10, "lte": 100}}
        ]
    },
    limit=10
)
```

### Пакетный поиск

```python
from qdrant_client.models import SearchRequest

# Multiple queries in one request
results = client.search_batch(
    collection_name="documents",
    requests=[
        SearchRequest(vector=[0.1, ...], limit=5),
        SearchRequest(vector=[0.2, ...], limit=5, filter={"must": [...]}),
        SearchRequest(vector=[0.3, ...], limit=10)
    ]
)
```

## Интеграция с RAG

### С sentence‑transformers

```python
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, PointStruct

# Initialize
encoder = SentenceTransformer("all-MiniLM-L6-v2")
client = QdrantClient(host="localhost", port=6333)

# Create collection
client.create_collection(
    collection_name="knowledge_base",
    vectors_config=VectorParams(size=384, distance=Distance.COSINE)
)

# Index documents
documents = [
    {"id": 1, "text": "Python is a programming language", "source": "wiki"},
    {"id": 2, "text": "Machine learning uses algorithms", "source": "textbook"},
]

points = [
    PointStruct(
        id=doc["id"],
        vector=encoder.encode(doc["text"]).tolist(),
        payload={"text": doc["text"], "source": doc["source"]}
    )
    for doc in documents
]
client.upsert(collection_name="knowledge_base", points=points)

# RAG retrieval
def retrieve(query: str, top_k: int = 5) -> list[dict]:
    query_vector = encoder.encode(query).tolist()
    results = client.search(
        collection_name="knowledge_base",
        query_vector=query_vector,
        limit=top_k
    )
    return [{"text": r.payload["text"], "score": r.score} for r in results]

# Use in RAG pipeline
context = retrieve("What is Python?")
prompt = f"Context: {context}\n\nQuestion: What is Python?"
```

### С LangChain

```python
from langchain_community.vectorstores import Qdrant
from langchain_community.embeddings import HuggingFaceEmbeddings

embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
vectorstore = Qdrant.from_documents(documents, embeddings, url="http://localhost:6333", collection_name="docs")
retriever = vectorstore.as_retriever(search_kwargs={"k": 5})
```

### С LlamaIndex

```python
from llama_index.vector_stores.qdrant import QdrantVectorStore
from llama_index.core import VectorStoreIndex, StorageContext

vector_store = QdrantVectorStore(client=client, collection_name="llama_docs")
storage_context = StorageContext.from_defaults(vector_store=vector_store)
index = VectorStoreIndex.from_documents(documents, storage_context=storage_context)
query_engine = index.as_query_engine()
```

## Поддержка мульти‑векторов

### Именованные векторы (разные модели эмбеддингов)

```python
from qdrant_client.models import VectorParams, Distance

# Collection with multiple vector types
client.create_collection(
    collection_name="hybrid_search",
    vectors_config={
        "dense": VectorParams(size=384, distance=Distance.COSINE),
        "sparse": VectorParams(size=30000, distance=Distance.DOT)
    }
)

# Insert with named vectors
client.upsert(
    collection_name="hybrid_search",
    points=[
        PointStruct(
            id=1,
            vector={
                "dense": dense_embedding,
                "sparse": sparse_embedding
            },
            payload={"text": "document text"}
        )
    ]
)

# Search specific vector
results = client.search(
    collection_name="hybrid_search",
    query_vector=("dense", query_dense),  # Specify which vector
    limit=10
)
```

### Разреженные векторы (BM25, SPLADE)

```python
from qdrant_client.models import SparseVectorParams, SparseIndexParams, SparseVector

# Collection with sparse vectors
client.create_collection(
    collection_name="sparse_search",
    vectors_config={},
    sparse_vectors_config={"text": SparseVectorParams(index=SparseIndexParams(on_disk=False))}
)

# Insert sparse vector
client.upsert(
    collection_name="sparse_search",
    points=[PointStruct(id=1, vector={"text": SparseVector(indices=[1, 5, 100], values=[0.5, 0.8, 0.2])}, payload={"text": "document"})]
)
```

## Квантование (оптимизация памяти)

```python
from qdrant_client.models import ScalarQuantization, ScalarQuantizationConfig, ScalarType

# Scalar quantization (4x memory reduction)
client.create_collection(
    collection_name="quantized",
    vectors_config=VectorParams(size=384, distance=Distance.COSINE),
    quantization_config=ScalarQuantization(
        scalar=ScalarQuantizationConfig(
            type=ScalarType.INT8,
            quantile=0.99,        # Clip outliers
            always_ram=True      # Keep quantized in RAM
        )
    )
)

# Search with rescoring
results = client.search(
    collection_name="quantized",
    query_vector=query,
    search_params={"quantization": {"rescore": True}},  # Rescore top results
    limit=10
)
```

## Индексация payload

```python
from qdrant_client.models import PayloadSchemaType

# Create payload index for faster filtering
client.create_payload_index(
    collection_name="documents",
    field_name="category",
    field_schema=PayloadSchemaType.KEYWORD
)

client.create_payload_index(
    collection_name="documents",
    field_name="timestamp",
    field_schema=PayloadSchemaType.INTEGER
)

# Index types: KEYWORD, INTEGER, FLOAT, GEO, TEXT (full-text), BOOL
```

## Производственное развертывание

### Qdrant Cloud

```python
from qdrant_client import QdrantClient

# Connect to Qdrant Cloud
client = QdrantClient(
    url="https://your-cluster.cloud.qdrant.io",
    api_key="your-api-key"
)
```

### Тонкая настройка производительности

```python
# Optimize for search speed (higher recall)
client.update_collection(
    collection_name="documents",
    hnsw_config=HnswConfigDiff(ef_construct=200, m=32)
)

# Optimize for indexing speed (bulk loads)
client.update_collection(
    collection_name="documents",
    optimizer_config={"indexing_threshold": 20000}
)
```

## Лучшие практики

1. **Batch operations** — используйте пакетные upsert/search для повышения эффективности
2. **Payload indexing** — индексируйте поля, используемые в фильтрах
3. **Quantization** — включайте для больших коллекций (> 1 M векторов)
4. **Sharding** — применяйте для коллекций > 10 M векторов
5. **On‑disk storage** — включайте `on_disk_payload` для больших payload‑ов
6. **Connection pooling** — переиспользуйте экземпляры клиента

## Распространённые проблемы

**Медленный поиск с фильтрами:**
```python
# Create payload index for filtered fields
client.create_payload_index(
    collection_name="docs",
    field_name="category",
    field_schema=PayloadSchemaType.KEYWORD
)
```

**Недостаток памяти:**
```python
# Enable quantization and on-disk storage
client.create_collection(
    collection_name="large_collection",
    vectors_config=VectorParams(size=384, distance=Distance.COSINE),
    quantization_config=ScalarQuantization(...),
    on_disk_payload=True
)
```

**Проблемы с соединением:**
```python
# Use timeout and retry
client = QdrantClient(
    host="localhost",
    port=6333,
    timeout=30,
    prefer_grpc=True  # gRPC for better performance
)
```

## Ссылки

- **[Advanced Usage](https://github.com/NousResearch/hermes-agent/blob/main/optional-skills/mlops/qdrant/references/advanced-usage.md)** — распределённый режим, гибридный поиск, рекомендации
- **[Troubleshooting](https://github.com/NousResearch/hermes-agent/blob/main/optional-skills/mlops/qdrant/references/troubleshooting.md)** — типичные проблемы, отладка, настройка производительности

## Ресурсы

- **GitHub**: https://github.com/qdrant/qdrant (22k+ stars)
- **Docs**: https://qdrant.tech/documentation/
- **Python Client**: https://github.com/qdrant/qdrant-client
- **Cloud**: https://cloud.qdrant.io
- **Version**: 1.12.0+
- **License**: Apache 2.0