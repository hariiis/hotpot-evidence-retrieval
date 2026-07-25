"""
Hybrid retriever for sentence-level evidence retrieval.

This module combines BM25 keyword matching with Dense semantic matching.  For
each query, it retrieves candidates from both retrievers, normalizes their
scores separately, and ranks passages by a weighted hybrid score.
"""

from __future__ import annotations

from typing import Any, Sequence

from bm25 import BM25Retriever
from dense import DenseRetriever, DEFAULT_MODEL_NAME


class HybridRetriever:
    """Retrieve passages with a weighted BM25 + Dense score."""

    def __init__(
        self,
        passages: Sequence[dict[str, Any]],
        alpha: float = 0.5,
        bm25_k1: float = 1.5,
        bm25_b: float = 0.75,
        dense_model: str = DEFAULT_MODEL_NAME,
        cache_dir: str = "data/cache/dense",
        batch_size: int = 64,
    ) -> None:
        """
        Build both base retrievers and store the hybrid weighting parameter.

        alpha controls the BM25 weight:
        - alpha close to 1.0 means more lexical/BM25 influence.
        - alpha close to 0.0 means more semantic/Dense influence.
        """
        if not 0 <= alpha <= 1:
            raise ValueError("alpha must be between 0 and 1")

        self.passages = list(passages)
        self.alpha = alpha

        # BM25 is the lexical retriever: it rewards exact keyword overlap.
        self.bm25 = BM25Retriever(self.passages, k1=bm25_k1, b=bm25_b)

        # Dense is the semantic retriever: it rewards embedding similarity.
        self.dense = DenseRetriever(
            passages=self.passages,
            model_name=dense_model,
            cache_dir=cache_dir,
            batch_size=batch_size,
        )

    def _normalize_scores(
        self,
        scores_by_passage_id: dict[str, float],
    ) -> dict[str, float]:
        """
        Min-max normalize one retriever's scores to the [0, 1] range.

        The hybrid formula is only meaningful after normalization because BM25
        scores and Dense cosine similarities use different numeric scales.
        """
        if not scores_by_passage_id:
            return {}

        min_score = min(scores_by_passage_id.values())
        max_score = max(scores_by_passage_id.values())

        # If every score is identical, no passage has a relative advantage.
        if max_score == min_score:
            return {passage_id: 0.0 for passage_id in scores_by_passage_id}

        return {
            passage_id: (score - min_score) / (max_score - min_score)
            for passage_id, score in scores_by_passage_id.items()
        }

    def retrieve(
        self,
        query: str,
        top_k: int = 10,
        candidate_k: int = 100,
    ) -> list[dict[str, Any]]:
        """
        Return top-k passages ranked by the hybrid score.

        candidate_k controls how many candidates are collected from each base
        retriever before score fusion.  It should usually be larger than top_k.
        """
        if top_k <= 0:
            return []

        candidate_k = max(candidate_k, top_k)

        # Retrieve independent candidate lists from the two base methods.
        bm25_results = self.bm25.retrieve(query, top_k=candidate_k)
        dense_results = self.dense.retrieve(query, top_k=candidate_k)

        bm25_scores = {
            result["passage_id"]: float(result["score"])
            for result in bm25_results
        }
        dense_scores = {
            result["passage_id"]: float(result["score"])
            for result in dense_results
        }

        # Fuse over the union so a passage found by either method can survive.
        candidate_passage_ids = set(bm25_scores) | set(dense_scores)

        # Missing scores mean that retriever did not rank the passage.
        for passage_id in candidate_passage_ids:
            bm25_scores.setdefault(passage_id, 0.0)
            dense_scores.setdefault(passage_id, 0.0)

        normalized_bm25_scores = self._normalize_scores(bm25_scores)
        normalized_dense_scores = self._normalize_scores(dense_scores)

        hybrid_results = []
        for passage_id in candidate_passage_ids:
            bm25_score_norm = normalized_bm25_scores[passage_id]
            dense_score_norm = normalized_dense_scores[passage_id]

            # HybridScore = alpha * BM25Score + (1 - alpha) * DenseScore.
            hybrid_score = (
                self.alpha * bm25_score_norm
                + (1 - self.alpha) * dense_score_norm
            )

            hybrid_results.append(
                {
                    "passage_id": passage_id,
                    "score": hybrid_score,
                    "bm25_score": bm25_scores[passage_id],
                    "dense_score": dense_scores[passage_id],
                    "bm25_score_norm": bm25_score_norm,
                    "dense_score_norm": dense_score_norm,
                }
            )

        # Sort deterministically: highest score first, then passage_id for ties.
        hybrid_results.sort(key=lambda result: (-result["score"], result["passage_id"]))

        top_results = hybrid_results[:top_k]
        for rank, result in enumerate(top_results, start=1):
            result["rank"] = rank

        return top_results
