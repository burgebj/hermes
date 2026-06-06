---
title: "Chroma — база даних вбудовувань з відкритим кодом для AI‑застосувань"
sidebar_label: "Chroma"
description: "відкрито‑джерельна база даних вбудовувань для AI‑застосувань"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Chroma

Відкрита embedding‑база даних для AI‑застосунків. Зберігає embeddings та метадані, виконує векторний і повнотекстовий пошук, фільтрує за метаданими. Простий 4‑функціональний API. Масштабується від ноутбуків до виробничих кластерів. Використовується для семантичного пошуку, RAG‑застосунків або пошуку документів. Найкраще підходить для локальної розробки та open‑source проєктів.

## Skill metadata

| | |
|---|---|
| Source | Optional — install with `hermes skills install official/mlops/chroma` |
| Path | `optional-skills/mlops/chroma` |
| Version | `1.0.0` |
| Author | Orchestra Research |
| License | MIT |
| Dependencies | `chromadb`, `sentence-transformers` |
| Platforms | linux, macos, windows |
| Tags | `RAG`, `Chroma`, `Vector Database`, `Embeddings`, `Semantic Search`, `Open Source`, `Self-Hosted`, `Document Retrieval`, `Metadata Filtering` |

## Reference: full SKILL.md

:::info
The following is the complete skill definition that Hermes loads when this skill is triggered. This is what the agent sees as instructions when the skill is active.
:::

# Chroma – Open‑Source Embedding Database

AI‑нативна база даних для створення LLM‑застосунків з пам’яттю.

## Коли варто використовувати Chroma

**Використовуй Chroma, коли:**
- Створюєш RAG (retrieval‑augmented generation) застосунки
- Потрібна локальна/само‑хостинг векторна база даних
- Потрібне open‑source рішення (Apache 2.0)
- Прототипуєш у ноутбуках
- Потрібен семантичний пошук по документах
- Потрібно зберігати embeddings разом із метаданими

**Метрики**:
- **24 300+ зірок на GitHub**
- **1 900+ форків**
- **v1.3.3** (стабільна, щотижневі релізи)
- **Ліцензія Apache 2.0**

**Альтернативи**:
- **Pinecone**: керований хмарний сервіс, авто‑масштабування
- **FAISS**: чистий пошук схожості, без метаданих
- **Weaviate**: продакшн‑орієнтована ML‑база даних
- **Qdrant**: високопродуктивна, написана на Rust

## Quick start

### Installation

```bash
# Python
pip install chromadb

# JavaScript/TypeScript
npm install chromadb @chroma-core/default-embed
```

### Basic usage (Python)

```python
import chromadb

# Create client
client = chromadb.Client()

# Create collection
collection = client.create_collection(name="my_collection")

# Add documents
collection.add(
    documents=["This is document 1", "This is document 2"],
    metadatas=[{"source": "doc1"}, {"source": "doc2"}],
    ids=["id1", "id2"]
)

# Query
results = collection.query(
    query_texts=["document about topic"],
    n_results=2
)

print(results)
```

## Core operations

### 1. Create collection

```python
# Simple collection
collection = client.create_collection("my_docs")

# With custom embedding function
from chromadb.utils import embedding_functions

openai_ef = embedding_functions.OpenAIEmbeddingFunction(
    api_key="your-key",
    model_name="text-embedding-3-small"
)

collection = client.create_collection(
    name="my_docs",
    embedding_function=openai_ef
)

# Get existing collection
collection = client.get_collection("my_docs")

# Delete collection
client.delete_collection("my_docs")
```

### 2. Add documents

```python
# Add with auto-generated IDs
collection.add(
    documents=["Doc 1", "Doc 2", "Doc 3"],
    metadatas=[
        {"source": "web", "category": "tutorial"},
        {"source": "pdf", "page": 5},
        {"source": "api", "timestamp": "2025-01-01"}
    ],
    ids=["id1", "id2", "id3"]
)

# Add with custom embeddings
collection.add(
    embeddings=[[0.1, 0.2, ...], [0.3, 0.4, ...]],
    documents=["Doc 1", "Doc 2"],
    ids=["id1", "id2"]
)
```

### 3. Query (similarity search)

```python
# Basic query
results = collection.query(
    query_texts=["machine learning tutorial"],
    n_results=5
)

# Query with filters
results = collection.query(
    query_texts=["Python programming"],
    n_results=3,
    where={"source": "web"}
)

# Query with metadata filters
results = collection.query(
    query_texts=["advanced topics"],
    where={
        "$and": [
            {"category": "tutorial"},
            {"difficulty": {"$gte": 3}}
        ]
    }
)

# Access results
print(results["documents"])      # List of matching documents
print(results["metadatas"])      # Metadata for each doc
print(results["distances"])      # Similarity scores
print(results["ids"])            # Document IDs
```

### 4. Get documents

```python
# Get by IDs
docs = collection.get(
    ids=["id1", "id2"]
)

# Get with filters
docs = collection.get(
    where={"category": "tutorial"},
    limit=10
)

# Get all documents
docs = collection.get()
```

### 5. Update documents

```python
# Update document content
collection.update(
    ids=["id1"],
    documents=["Updated content"],
    metadatas=[{"source": "updated"}]
)
```

### 6. Delete documents

```python
# Delete by IDs
collection.delete(ids=["id1", "id2"])

# Delete with filter
collection.delete(
    where={"source": "outdated"}
)
```

## Persistent storage

```python
# Persist to disk
client = chromadb.PersistentClient(path="./chroma_db")

collection = client.create_collection("my_docs")
collection.add(documents=["Doc 1"], ids=["id1"])

# Data persisted automatically
# Reload later with same path
client = chromadb.PersistentClient(path="./chroma_db")
collection = client.get_collection("my_docs")
```

## Embedding functions

### Default (Sentence Transformers)

```python
# Uses sentence-transformers by default
collection = client.create_collection("my_docs")
# Default model: all-MiniLM-L6-v2
```

### OpenAI

```python
from chromadb.utils import embedding_functions

openai_ef = embedding_functions.OpenAIEmbeddingFunction(
    api_key="your-key",
    model_name="text-embedding-3-small"
)

collection = client.create_collection(
    name="openai_docs",
    embedding_function=openai_ef
)
```

### HuggingFace

```python
huggingface_ef = embedding_functions.HuggingFaceEmbeddingFunction(
    api_key="your-key",
    model_name="sentence-transformers/all-mpnet-base-v2"
)

collection = client.create_collection(
    name="hf_docs",
    embedding_function=huggingface_ef
)
```

### Custom embedding function

```python
from chromadb import Documents, EmbeddingFunction, Embeddings

class MyEmbeddingFunction(EmbeddingFunction):
    def __call__(self, input: Documents) -> Embeddings:
        # Your embedding logic
        return embeddings

my_ef = MyEmbeddingFunction()
collection = client.create_collection(
    name="custom_docs",
    embedding_function=my_ef
)
```

## Metadata filtering

```python
# Exact match
results = collection.query(
    query_texts=["query"],
    where={"category": "tutorial"}
)

# Comparison operators
results = collection.query(
    query_texts=["query"],
    where={"page": {"$gt": 10}}  # $gt, $gte, $lt, $lte, $ne
)

# Logical operators
results = collection.query(
    query_texts=["query"],
    where={
        "$and": [
            {"category": "tutorial"},
            {"difficulty": {"$lte": 3}}
        ]
    }  # Also: $or
)

# Contains
results = collection.query(
    query_texts=["query"],
    where={"tags": {"$in": ["python", "ml"]}}
)
```

## LangChain integration

```python
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter

# Split documents
text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000)
docs = text_splitter.split_documents(documents)

# Create Chroma vector store
vectorstore = Chroma.from_documents(
    documents=docs,
    embedding=OpenAIEmbeddings(),
    persist_directory="./chroma_db"
)

# Query
results = vectorstore.similarity_search("machine learning", k=3)

# As retriever
retriever = vectorstore.as_retriever(search_kwargs={"k": 5})
```

## LlamaIndex integration

```python
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.core import VectorStoreIndex, StorageContext
import chromadb

# Initialize Chroma
db = chromadb.PersistentClient(path="./chroma_db")
collection = db.get_or_create_collection("my_collection")

# Create vector store
vector_store = ChromaVectorStore(chroma_collection=collection)
storage_context = StorageContext.from_defaults(vector_store=vector_store)

# Create index
index = VectorStoreIndex.from_documents(
    documents,
    storage_context=storage_context
)

# Query
query_engine = index.as_query_engine()
response = query_engine.query("What is machine learning?")
```

## Server mode

```python
# Run Chroma server
# Terminal: chroma run --path ./chroma_db --port 8000

# Connect to server
import chromadb
from chromadb.config import Settings

client = chromadb.HttpClient(
    host="localhost",
    port=8000,
    settings=Settings(anonymized_telemetry=False)
)

# Use as normal
collection = client.get_or_create_collection("my_docs")
```

## Best practices

1. **Використовуй постійний клієнт** – не втрачай дані після перезапуску
2. **Додавай метадані** – це дозволяє фільтрувати та відстежувати записи
3. **Пакетні операції** – додавай кілька документів одночасно
4. **Обирай правильну модель embedding** – баланс швидкості та якості
5. **Використовуй фільтри** – звужуй простір пошуку
6. **Унікальні ID** – уникай колізій
7. **Регулярні резервні копії** – копіюй каталог `chroma_db`
8. **Контролюй розмір колекції** – масштабуй за потреби
9. **Тестуй функції embedding** – переконайся у їхній якості
10. **Використовуй режим сервера для продакшну** – краще для багатокористувацького доступу

## Performance

| Operation | Latency | Notes |
|-----------|---------|-------|
| Add 100 docs | ~1‑3 s | З урахуванням embedding |
| Query (top 10) | ~50‑200 ms | Залежить від розміру колекції |
| Metadata filter | ~10‑50 ms | Швидко при правильному індексуванні |

## Resources

- **GitHub**: https://github.com/chroma-core/chroma ⭐ 24 300+
- **Docs**: https://docs.trychroma.com
- **Discord**: https://discord.gg/MMeYNTmh3x
- **Version**: 1.3.3+
- **License**: Apache 2.0