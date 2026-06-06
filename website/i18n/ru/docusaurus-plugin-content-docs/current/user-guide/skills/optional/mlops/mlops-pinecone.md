---
title: "Pinecone — управляемая векторная база данных для производственных AI‑приложений"
sidebar_label: "Pinecone"
description: "Управляемая векторная база данных для производственных AI‑приложений"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Pinecone

Управляемая векторная база данных для производственных AI‑приложений. Полностью управляемая, авто‑масштабируемая, с гибридным поиском (плотный + разреженный), фильтрацией метаданных и пространствами имён. Низкая задержка (<100 мс p95). Используется для production RAG, рекомендательных систем или семантического поиска в масштабе. Лучший вариант для serverless, управляемой инфраструктуры.

## Skill metadata

| | |
|---|---|
| Source | Optional — install with `hermes skills install official/mlops/pinecone` |
| Path | `optional-skills/mlops/pinecone` |
| Version | `1.0.0` |
| Author | Orchestra Research |
| License | MIT |
| Dependencies | `pinecone-client` |
| Platforms | linux, macos, windows |
| Tags | `RAG`, `Pinecone`, `Vector Database`, `Managed Service`, `Serverless`, `Hybrid Search`, `Production`, `Auto-Scaling`, `Low Latency`, `Recommendations` |

## Reference: full SKILL.md

:::info
The following is the complete skill definition that Hermes loads when this skill is triggered. This is what the agent sees as instructions when the skill is active.
:::

# Pinecone — Managed Vector Database

Векторная база данных для производственных AI‑приложений.

## Когда использовать Pinecone

**Когда:**
- Нужно управляемое, serverless‑решение для векторных данных
- Production RAG‑приложения
- Требуется авто‑масштабирование
- Критична низкая задержка (<100 мс)
- Не хочется управлять инфраструктурой
- Нужен гибридный поиск (плотные + разреженные векторы)

**Метрики:**
- Полностью управляемый SaaS
- Авто‑масштабируется до миллиардов векторов
- **p95 задержка <100 мс**
- SLA — 99,9 % времени безотказной работы

**Альтернативы:**
- **Chroma**: самостоятельный, open‑source
- **FAISS**: офлайн, чистый поиск по сходству
- **Weaviate**: самостоятельный с большим набором функций

## Быстрый старт

### Installation

```bash
pip install pinecone-client
```

### Basic usage

```python
from pinecone import Pinecone, ServerlessSpec

# Initialize
pc = Pinecone(api_key="your-api-key")

# Create index
pc.create_index(
    name="my-index",
    dimension=1536,  # Must match embedding dimension
    metric="cosine",  # or "euclidean", "dotproduct"
    spec=ServerlessSpec(cloud="aws", region="us-east-1")
)

# Connect to index
index = pc.Index("my-index")

# Upsert vectors
index.upsert(vectors=[
    {"id": "vec1", "values": [0.1, 0.2, ...], "metadata": {"category": "A"}},
    {"id": "vec2", "values": [0.3, 0.4, ...], "metadata": {"category": "B"}}
])

# Query
results = index.query(
    vector=[0.1, 0.2, ...],
    top_k=5,
    include_metadata=True
)

print(results["matches"])
```

## Core operations

### Create index

```python
# Serverless (recommended)
pc.create_index(
    name="my-index",
    dimension=1536,
    metric="cosine",
    spec=ServerlessSpec(
        cloud="aws",         # or "gcp", "azure"
        region="us-east-1"
    )
)

# Pod-based (for consistent performance)
from pinecone import PodSpec

pc.create_index(
    name="my-index",
    dimension=1536,
    metric="cosine",
    spec=PodSpec(
        environment="us-east1-gcp",
        pod_type="p1.x1"
    )
)
```

### Upsert vectors

```python
# Single upsert
index.upsert(vectors=[
    {
        "id": "doc1",
        "values": [0.1, 0.2, ...],  # 1536 dimensions
        "metadata": {
            "text": "Document content",
            "category": "tutorial",
            "timestamp": "2025-01-01"
        }
    }
])

# Batch upsert (recommended)
vectors = [
    {"id": f"vec{i}", "values": embedding, "metadata": metadata}
    for i, (embedding, metadata) in enumerate(zip(embeddings, metadatas))
]

index.upsert(vectors=vectors, batch_size=100)
```

### Query vectors

```python
# Basic query
results = index.query(
    vector=[0.1, 0.2, ...],
    top_k=10,
    include_metadata=True,
    include_values=False
)

# With metadata filtering
results = index.query(
    vector=[0.1, 0.2, ...],
    top_k=5,
    filter={"category": {"$eq": "tutorial"}}
)

# Namespace query
results = index.query(
    vector=[0.1, 0.2, ...],
    top_k=5,
    namespace="production"
)

# Access results
for match in results["matches"]:
    print(f"ID: {match['id']}")
    print(f"Score: {match['score']}")
    print(f"Metadata: {match['metadata']}")
```

### Metadata filtering

```python
# Exact match
filter = {"category": "tutorial"}

# Comparison
filter = {"price": {"$gte": 100}}  # $gt, $gte, $lt, $lte, $ne

# Logical operators
filter = {
    "$and": [
        {"category": "tutorial"},
        {"difficulty": {"$lte": 3}}
    ]
}  # Also: $or

# In operator
filter = {"tags": {"$in": ["python", "ml"]}}
```

## Namespaces

```python
# Partition data by namespace
index.upsert(
    vectors=[{"id": "vec1", "values": [...]}],
    namespace="user-123"
)

# Query specific namespace
results = index.query(
    vector=[...],
    namespace="user-123",
    top_k=5
)

# List namespaces
stats = index.describe_index_stats()
print(stats['namespaces'])
```

## Hybrid search (dense + sparse)

```python
# Upsert with sparse vectors
index.upsert(vectors=[
    {
        "id": "doc1",
        "values": [0.1, 0.2, ...],  # Dense vector
        "sparse_values": {
            "indices": [10, 45, 123],  # Token IDs
            "values": [0.5, 0.3, 0.8]   # TF-IDF scores
        },
        "metadata": {"text": "..."}
    }
])

# Hybrid query
results = index.query(
    vector=[0.1, 0.2, ...],
    sparse_vector={
        "indices": [10, 45],
        "values": [0.5, 0.3]
    },
    top_k=5,
    alpha=0.5  # 0=sparse, 1=dense, 0.5=hybrid
)
```

## LangChain integration

```python
from langchain_pinecone import PineconeVectorStore
from langchain_openai import OpenAIEmbeddings

# Create vector store
vectorstore = PineconeVectorStore.from_documents(
    documents=docs,
    embedding=OpenAIEmbeddings(),
    index_name="my-index"
)

# Query
results = vectorstore.similarity_search("query", k=5)

# With metadata filter
results = vectorstore.similarity_search(
    "query",
    k=5,
    filter={"category": "tutorial"}
)

# As retriever
retriever = vectorstore.as_retriever(search_kwargs={"k": 10})
```

## LlamaIndex integration

```python
from llama_index.vector_stores.pinecone import PineconeVectorStore

# Connect to Pinecone
pc = Pinecone(api_key="your-key")
pinecone_index = pc.Index("my-index")

# Create vector store
vector_store = PineconeVectorStore(pinecone_index=pinecone_index)

# Use in LlamaIndex
from llama_index.core import StorageContext, VectorStoreIndex

storage_context = StorageContext.from_defaults(vector_store=vector_store)
index = VectorStoreIndex.from_documents(documents, storage_context=storage_context)
```

## Index management

```python
# List indices
indexes = pc.list_indexes()

# Describe index
index_info = pc.describe_index("my-index")
print(index_info)

# Get index stats
stats = index.describe_index_stats()
print(f"Total vectors: {stats['total_vector_count']}")
print(f"Namespaces: {stats['namespaces']}")

# Delete index
pc.delete_index("my-index")
```

## Delete vectors

```python
# Delete by ID
index.delete(ids=["vec1", "vec2"])

# Delete by filter
index.delete(filter={"category": "old"})

# Delete all in namespace
index.delete(delete_all=True, namespace="test")

# Delete entire index
index.delete(delete_all=True)
```

## Best practices

1. **Use serverless** — авто‑масштабирование, экономия затрат
2. **Batch upserts** — более эффективно (100‑200 записей за пакет)
3. **Add metadata** — позволяет фильтрацию
4. **Use namespaces** — изолирует данные по пользователю/тенанту
5. **Monitor usage** — проверяй панель Pinecone
6. **Optimize filters** — индексируй часто фильтруемые поля
7. **Test with free tier** — 1 индекс, 100 K векторов бесплатно
8. **Use hybrid search** — лучшее качество
9. **Set appropriate dimensions** — соответствует модели эмбеддингов
10. **Regular backups** — экспортируй важные данные

## Performance

| Operation | Latency | Notes |
|-----------|---------|-------|
| Upsert | ~50‑100 ms | За пакет |
| Query (p50) | ~50 ms | Зависит от размера индекса |
| Query (p95) | ~100 ms | Цель SLA |
| Metadata filter | ~+10‑20 ms | Дополнительные накладные расходы |

## Pricing (as of 2025)

**Serverless:**
- $0.096 за миллион read‑units
- $0.06 за миллион write‑units
- $0.06 за GB хранилища в месяц

**Free tier:**
- 1 serverless‑индекс
- 100 K векторов (1536 измерений)
- Отлично подходит для прототипов

## Resources

- **Website**: https://www.pinecone.io
- **Docs**: https://docs.pinecone.io
- **Console**: https://app.pinecone.io
- **Pricing**: https://www.pinecone.io/pricing