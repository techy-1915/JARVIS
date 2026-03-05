# JARVIS Memory System

## Three-Layer Architecture

| Layer | Class | Purpose | Persistence |
|-------|-------|---------|-------------|
| Short-term | `ShortTermMemory` | Conversation context | In-process only |
| Long-term | `LongTermMemory` | User preferences, facts | JSON file on disk |
| Knowledge | `KnowledgeMemory` | Documents and data | In-process (vector DB planned) |

## Usage via MemoryStore

```python
from jarvis.core.memory.memory_store import MemoryStore

mem = MemoryStore()

# Short-term
mem.add_interaction("Hello", "Hi there!")
context = mem.get_context(limit=10)

# Long-term
mem.remember("user_name", "Alice")
name = mem.recall("user_name")

# Knowledge
doc_id = mem.learn("FastAPI is a Python framework", title="FastAPI")
results = mem.search_knowledge("FastAPI")
```

## Embeddings

The `EmbeddingManager` provides a semantic search stub.
For production, replace with:
- **ChromaDB** – local vector database
- **FAISS** – Facebook's similarity search library
- **Pinecone** – cloud vector database
