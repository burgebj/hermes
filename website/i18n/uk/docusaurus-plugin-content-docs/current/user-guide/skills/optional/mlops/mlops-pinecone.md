---
title: "Pinecone — керована векторна база даних для виробничих AI‑застосувань"
sidebar_label: "Pinecone"
description: "Керована векторна база даних для виробничих AI‑застосувань"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Pinecone

Керована векторна база даних для виробничих AI‑застосунків. Повністю керована, авто‑масштабована, з гібридним пошуком (dense + sparse), фільтрацією метаданих та просторами імен. Низька затримка (<100 мс p95). Використовуй для виробничих RAG, систем рекомендацій або семантичного пошуку в масштабі. Найкраще підходить для безсерверної, керованої інфраструктури.

## Метадані навички

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

## Довідка: повний SKILL.md

:::info
Нижче наведено повне визначення навички, яке Hermes завантажує, коли ця навичка активована. Це те, що агент бачить як інструкції під час роботи навички.
:::

# Pinecone — керована векторна база даних

Векторна база даних для виробничих AI‑застосувань.

## Коли використовувати Pinecone

**Використовуй, коли:**
- Потрібна керована, безсерверна векторна база даних
- Виробничі RAG‑застосунки
- Потрібне авто‑масштабування
- Критична низька затримка (<100 мс)
- Не хочеш керувати інфраструктурою
- Потрібен гібридний пошук (dense + sparse vectors)

**Метрики**:
- Повністю керований SaaS
- Авто‑масштабується до мільярдів векторів
- **p95 latency <100 мс**
- SLA 99,9 % часу безвідмовної роботи

**Використовуй альтернативи**:
- **Chroma**: Самостійно розгорнута, open‑source
- **FAISS**: Офлайн, чистий пошук за схожістю
- **Weaviate**: Самостійно розгорнута з більшою кількістю функцій

## Швидкий старт

### Встановлення

```bash
pip install pinecone-client
```

### Базове використання

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

## Основні операції

### Створення індексу

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

### Додавання (upsert) векторів

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

### Запит векторів

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

### Фільтрація метаданих

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

## Простори імен

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

## Гібридний пошук (dense + sparse)

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

## Інтеграція з LangChain

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

## Інтеграція з LlamaIndex

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

## Управління індексами

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

## Видалення векторів

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

## Кращі практики

1. **Використовуй безсерверну інфраструктуру** — авто‑масштабування, економічно вигідно
2. **Пакетні upsert** — ефективніше (100‑200 за пакет)
3. **Додавай метадані** — дозволяє фільтрацію
4. **Використовуй простори імен** — ізоляція даних за користувачем/тенантом
5. **Моніторинг використання** — перевіряй панель Pinecone
6. **Оптимізуй фільтри** — індексуй часто фільтрувані поля
7. **Тестуй безкоштовний тариф** — 1 індекс, 100 K векторів безкоштовно
8. **Використовуй гібридний пошук** — краща якість
9. **Встанови відповідну розмірність** — підбери під модель ембеддінгів
10. **Регулярні резервні копії** — експортуй важливі дані

## Продуктивність

| Operation | Latency | Notes |
|-----------|---------|-------|
| Upsert | ~50-100ms | Per batch |
| Query (p50) | ~50ms | Depends on index size |
| Query (p95) | ~100ms | SLA target |
| Metadata filter | ~+10-20ms | Additional overhead |

## Ціноутворення (станом на 2025)

**Serverless**:
- $0.096 per million read units
- $0.06 per million write units
- $0.06 per GB storage/month

**Free tier**:
- 1 serverless index
- 100K vectors (1536 dimensions)
- Great for prototyping

## Ресурси

- **Website**: https://www.pinecone.io
- **Docs**: https://docs.pinecone.io
- **Console**: https://app.pinecone.io
- **Pricing**: https://www.pinecone.io/pricing