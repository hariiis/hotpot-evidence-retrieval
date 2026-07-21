"""Sentence-BERT dense retriever with reusable passage-embedding caches.

This module is deliberately a class rather than a command-line script.  Give
``DenseRetriever`` a list of passages when it is created, then call
``retrieve`` for each query.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Sequence

try:
    import numpy as np
except ImportError:  # pragma: no cover - exercised only when dependency is absent.
    np = None

try:
    from sentence_transformers import SentenceTransformer
except ImportError:  # pragma: no cover - exercised only when dependency is absent.
    SentenceTransformer = None


DEFAULT_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


class DenseRetriever:
    """Retrieve sentence passages by Sentence-BERT cosine similarity.

    Args:
        passages: Records containing ``passage_id`` and ``passage_text``.
        model_name: Name of the SentenceTransformer model to load.
        cache_dir: Directory used for the three embedding-cache files.
        batch_size: Number of texts to encode together.
    """

    def __init__(
        self,
        passages: Sequence[dict[str, Any]],
        model_name: str = DEFAULT_MODEL_NAME,
        cache_dir: str | Path = "data/cache",
        batch_size: int = 64,
    ) -> None:
        self.passages = list(passages)
        self.model_name = model_name
        self.cache_dir = Path(cache_dir)
        self.batch_size = batch_size

        self._validate_passages()
        if self.batch_size <= 0:
            raise ValueError("batch_size must be a positive integer")

        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.embeddings_path = self.cache_dir / "passage_embeddings.npy"
        self.ids_path = self.cache_dir / "passage_ids.json"
        self.metadata_path = self.cache_dir / "passage_embeddings.meta.json"

        self.passage_ids = [passage["passage_id"] for passage in self.passages]
        self.passage_texts = [passage["passage_text"] for passage in self.passages]
        self.corpus_fingerprint = self._compute_fingerprint(
            self.passage_ids, self.passage_texts
        )

        if np is None:
            raise ImportError(
                "DenseRetriever requires numpy. Install it before creating a "
                "DenseRetriever."
            )
        if SentenceTransformer is None:
            raise ImportError(
                "DenseRetriever requires sentence-transformers. "
                "Install it before creating a DenseRetriever."
            )

        # ``self.model_name`` is only a string; this loads the actual model
        # object whose built-in ``encode`` method creates embeddings.
        self.model = SentenceTransformer(self.model_name)

        if self._cache_is_valid():
            self.passage_embeddings = np.load(self.embeddings_path)
            self.passage_ids = self._load_ids()
        else:
            self.passage_embeddings = self._encode_passages()
            self._save_cache()

    def retrieve(self, query: str, top_k: int = 10) -> list[dict[str, Any]]:
        """Return the highest-scoring passages for a non-empty query.

        Embeddings are L2-normalized, so the dot product below equals cosine
        similarity.  The returned scores are plain Python floats so they can
        be written directly to JSON.
        """
        if not isinstance(query, str):
            raise TypeError("query must be a string")
        if not query.strip() or top_k <= 0 or not self.passage_ids:
            return []

        query_embedding = self.model.encode(
            query,
            normalize_embeddings=True,
            convert_to_numpy=True,
        )
        scores = self.passage_embeddings @ query_embedding
        k = min(top_k, len(self.passage_ids))

        # Stable sorting makes tied scores reproducible: their original
        # passage order is preserved.
        top_indices = np.argsort(-scores, kind="stable")[:k]

        return [
            {
                "rank": rank,
                "passage_id": self.passage_ids[index],
                "score": float(scores[index]),
            }
            for rank, index in enumerate(top_indices, start=1)
        ]

    def _validate_passages(self) -> None:
        seen_ids: set[str] = set()
        for index, passage in enumerate(self.passages):
            if not isinstance(passage, dict):
                raise TypeError(f"passages[{index}] must be a dictionary")
            if "passage_id" not in passage or "passage_text" not in passage:
                raise ValueError(
                    f"passages[{index}] must contain passage_id and passage_text"
                )
            if not isinstance(passage["passage_id"], str):
                raise TypeError(f"passages[{index}].passage_id must be a string")
            if not isinstance(passage["passage_text"], str):
                raise TypeError(f"passages[{index}].passage_text must be a string")
            if passage["passage_id"] in seen_ids:
                raise ValueError(f"duplicate passage_id: {passage['passage_id']}")
            seen_ids.add(passage["passage_id"])

    def _cache_is_valid(self) -> bool:
        """Check that all cache files match this model and passage corpus."""
        if not (
            self.embeddings_path.exists()
            and self.ids_path.exists()
            and self.metadata_path.exists()
        ):
            return False

        try:
            with self.metadata_path.open("r", encoding="utf-8") as file:
                metadata = json.load(file)
            cached_ids = self._load_ids()
            cached_embeddings = np.load(self.embeddings_path, mmap_mode="r")
        except (OSError, ValueError, json.JSONDecodeError):
            return False

        expected_dimension = metadata.get("embedding_dim")
        return (
            metadata.get("model_name") == self.model_name
            and metadata.get("corpus_fingerprint") == self.corpus_fingerprint
            and cached_ids == self.passage_ids
            and cached_embeddings.ndim == 2
            and cached_embeddings.shape[0] == len(self.passages)
            and cached_embeddings.shape[1] == expected_dimension
        )

    def _encode_passages(self) -> np.ndarray:
        """Encode every passage once and return normalized float embeddings."""
        if not self.passage_texts:
            # MiniLM normally produces 384 dimensions.  An empty corpus does
            # not need a model call, and retrieve() will return an empty list.
            return np.empty((0, 0), dtype=np.float32)

        return self.model.encode(
            self.passage_texts,
            batch_size=self.batch_size,
            normalize_embeddings=True,
            convert_to_numpy=True,
            show_progress_bar=False,
        )

    def _save_cache(self) -> None:
        np.save(self.embeddings_path, self.passage_embeddings)
        with self.ids_path.open("w", encoding="utf-8") as file:
            json.dump(self.passage_ids, file, ensure_ascii=False, indent=2)

        embedding_dim = (
            int(self.passage_embeddings.shape[1])
            if self.passage_embeddings.ndim == 2
            else 0
        )
        metadata = {
            "model_name": self.model_name,
            "embedding_dim": embedding_dim,
            "corpus_fingerprint": self.corpus_fingerprint,
        }
        with self.metadata_path.open("w", encoding="utf-8") as file:
            json.dump(metadata, file, ensure_ascii=False, indent=2)

    def _load_ids(self) -> list[str]:
        with self.ids_path.open("r", encoding="utf-8") as file:
            ids = json.load(file)
        if not isinstance(ids, list) or not all(isinstance(item, str) for item in ids):
            raise ValueError("passage_ids.json must contain a list of strings")
        return ids

    @staticmethod
    def _compute_fingerprint(
        passage_ids: Sequence[str], passage_texts: Sequence[str]
    ) -> str:
        """Hash ordered IDs and text, so even one corpus edit invalidates cache."""
        hasher = hashlib.sha256()
        for passage_id, passage_text in zip(passage_ids, passage_texts):
            hasher.update(passage_id.encode("utf-8"))
            hasher.update(b"\t")
            hasher.update(passage_text.encode("utf-8"))
            hasher.update(b"\n")
        return hasher.hexdigest()
