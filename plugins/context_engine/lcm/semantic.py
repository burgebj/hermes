"""Optional semantic search for LCM context management.

Provides embedding-based similarity search over the immutable message store.
This is a stub implementation that can be enabled when embedding APIs are
available.
"""
from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    import numpy as np
    from plugins.context_engine.lcm.store import ImmutableStore

logger = logging.getLogger(__name__)


@dataclass
class SemanticIndexConfig:
    """Configuration for SemanticIndex."""
    enabled: bool = False
    model: str = "text-embedding-3-small"
    min_messages: int = 50  # Only build index if store has this many messages
    batch_size: int = 100


class SemanticIndex:
    """Optional embedding-based search for the immutable store.

    This allows semantic similarity search across all messages, including
    those already compacted into summaries. Falls back gracefully when
    embedding APIs are unavailable.
    """

    def __init__(self, config: SemanticIndexConfig):
        self.config = config
        self.embeddings: List[Any] = []  # List of numpy arrays
        self.msg_ids: List[int] = []
        self._client = None
        self._indexed_count = 0

    def is_available(self) -> bool:
        """Check if semantic search is available."""
        if not self.config.enabled:
            return False

        # Check for API key (OpenAI embeddings)
        if not os.getenv("OPENAI_API_KEY"):
            return False

        return True

    def should_index(self, store: "ImmutableStore") -> bool:
        """Check if the store is large enough to warrant indexing."""
        return len(store) >= self.config.min_messages

    def index(self, store: "ImmutableStore") -> bool:
        """Build index for all messages in store.

        Returns True if indexing succeeded.
        """
        if not self.is_available():
            logger.debug("Semantic index not available (disabled or no API key)")
            return False

        if not self.should_index(store):
            logger.debug(
                "Store too small for semantic indexing (%d < %d messages)",
                len(store), self.config.min_messages
            )
            return False

        try:
            self._do_index(store)
            return True
        except Exception as e:
            logger.warning("Semantic indexing failed: %s", e)
            return False

    def _do_index(self, store: "ImmutableStore"):
        """Actual indexing implementation."""
        # Lazy import to avoid loading numpy/embedding libs unless needed
        try:
            import numpy as np
        except ImportError:
            logger.debug("numpy not installed, skipping semantic indexing")
            return

        self.embeddings = []
        self.msg_ids = []
        self._indexed_count = 0

        # Batch messages for embedding
        batch_texts = []
        batch_ids = []

        for msg_id in range(len(store)):
            msg = store.get(msg_id)
            if msg is None:
                continue

            content = str(msg.get("content") or "")
            if not content.strip():
                continue

            batch_texts.append(content)
            batch_ids.append(msg_id)

            # Process batch
            if len(batch_texts) >= self.config.batch_size:
                self._index_batch(batch_texts, batch_ids)
                batch_texts = []
                batch_ids = []

        # Process remaining
        if batch_texts:
            self._index_batch(batch_texts, batch_ids)

        logger.info(
            "Semantic index built: %d messages indexed",
            self._indexed_count
        )

    def _index_batch(self, texts: List[str], ids: List[int]):
        """Index a batch of texts."""
        try:
            import numpy as np
        except ImportError:
            return

        embeddings = self._get_embeddings(texts)
        if embeddings is None:
            return

        for emb, msg_id in zip(embeddings, ids):
            self.embeddings.append(np.array(emb))
            self.msg_ids.append(msg_id)
            self._indexed_count += 1

    def _get_embeddings(self, texts: List[str]) -> Optional[List[List[float]]]:
        """Get embeddings for a batch of texts."""
        if self._client is None:
            self._client = self._create_client()

        if self._client is None:
            return None

        try:
            response = self._client.embeddings.create(
                model=self.config.model,
                input=texts,
            )
            return [item.embedding for item in response.data]
        except Exception as e:
            logger.warning("Embedding API call failed: %s", e)
            return None

    def _create_client(self):
        """Create OpenAI client for embeddings."""
        try:
            from openai import OpenAI
            return OpenAI()
        except ImportError:
            logger.debug("openai package not installed")
            return None
        except Exception as e:
            logger.debug("Failed to create OpenAI client: %s", e)
            return None

    def search(self, query: str, k: int = 10) -> List[int]:
        """Return top-k message IDs by semantic similarity.

        Returns empty list if semantic search is unavailable.
        """
        if not self.embeddings:
            return []

        try:
            import numpy as np
        except ImportError:
            return []

        # Get query embedding
        query_embeddings = self._get_embeddings([query])
        if not query_embeddings:
            return []

        query_emb = np.array(query_embeddings[0])

        # Compute cosine similarities
        similarities = []
        for i, emb in enumerate(self.embeddings):
            sim = np.dot(query_emb, emb) / (
                np.linalg.norm(query_emb) * np.linalg.norm(emb)
            )
            similarities.append((sim, self.msg_ids[i]))

        # Sort by similarity (descending)
        similarities.sort(reverse=True, key=lambda x: x[0])

        # Return top-k message IDs
        return [msg_id for _, msg_id in similarities[:k]]

    def clear(self):
        """Clear the index."""
        self.embeddings = []
        self.msg_ids = []
        self._indexed_count = 0


# Stub implementation for when semantic search is disabled
class NoOpSemanticIndex:
    """No-op semantic index that always returns empty results."""

    def is_available(self) -> bool:
        return False

    def index(self, store: "ImmutableStore") -> bool:
        return False

    def search(self, query: str, k: int = 10) -> List[int]:
        return []

    def clear(self):
        pass


def create_semantic_index(config: SemanticIndexConfig) -> SemanticIndex:
    """Factory function to create a semantic index.

    Returns a working SemanticIndex if dependencies are available,
    or a NoOpSemanticIndex otherwise.
    """
    if not config.enabled:
        return NoOpSemanticIndex()

    if not os.getenv("OPENAI_API_KEY"):
        logger.debug("No OPENAI_API_KEY, semantic search disabled")
        return NoOpSemanticIndex()

    try:
        return SemanticIndex(config)
    except Exception as e:
        logger.warning("Failed to create semantic index: %s", e)
        return NoOpSemanticIndex()
