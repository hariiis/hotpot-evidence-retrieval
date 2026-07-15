"""
Build a simple BM25 lexical retriever for sentence-level evidence retrieval.

This module builds an in-memory BM25 index over the sentence-level passages
stored in passages.jsonl. It provides a lexical retrieval baseline for the
HotpotQA evidence-retrieval task: given a natural-language query, it returns
the top-k candidate evidence sentences ranked by BM25 score.
"""

import json
import math
import re
from collections import Counter, defaultdict


# 1. Tokenize lowercase English words and numbers, preserving internal apostrophes.
# Example: "Scott Derrickson's film" -> ["scott", "derrickson's", "film"]
def tokenize(text):
    text = text.lower()
    return re.findall(r"[A-Za-z0-9]+(?:'[A-Za-z0-9]+)?", text)


# 2. Read passages.jsonl.
def load_passages(passages_path):
    passages = []

    with open(passages_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()

            if not line:
                continue

            passages.append(json.loads(line))

    return passages


class BM25Retriever:
    """
    BM25 retriever over sentence-level passage records.

    Expected passage format:
    {
        "passage_id": "Scott Derrickson::0",
        "title": "Scott Derrickson",
        "sentence_index": 0,
        "passage_text": "Scott Derrickson is an American director, "
                        "screenwriter and producer."
    }
    """

    # 3. Store passages and BM25 parameters, then build all index structures needed for retrieval
    def __init__(self, passages, k1=1.5, b=0.75):
        # Fixed BM25 baseline settings: k1 = 1.5 and b = 0.75.
        self.passages = passages
        self.k1 = k1
        self.b = b

        self.passage_ids = []
        self.doc_lengths = []
        self.term_frequencies = []
        self.inverted_index = defaultdict(list)
        self.document_frequencies = Counter()
        self.idf = {}

        self._build_index()

    # 4. Build BM25 index statistics from all passages: TF, DF, IDF, document lengths,
    # average document length, and the inverted index.
    def _build_index(self):
        total_doc_length = 0
        seen_passage_ids = set()

        # Build TF, DF, document lengths, and inverted index.
        for doc_idx, passage in enumerate(self.passages):
            passage_id = passage["passage_id"]
            passage_text = passage.get("passage_text", "")

            if passage_id in seen_passage_ids:
                raise ValueError(f"Duplicate passage_id: {passage_id}")
            seen_passage_ids.add(passage_id)

            tokens = tokenize(passage_text)
            term_counts = Counter(tokens)
            doc_length = len(tokens)

            self.passage_ids.append(passage_id)
            self.term_frequencies.append(term_counts)
            self.doc_lengths.append(doc_length)
            total_doc_length += doc_length

            # Each distinct term contributes once to document frequency.
            for term in term_counts:
                self.inverted_index[term].append(doc_idx)
                self.document_frequencies[term] += 1

        self.num_docs = len(self.passages)

        if self.num_docs == 0:
            self.avg_doc_length = 0
        else:
            self.avg_doc_length = total_doc_length / self.num_docs

        # IDF(t) = log(1 + (N - df(t) + 0.5) / (df(t) + 0.5))
        for term, doc_freq in self.document_frequencies.items():
            self.idf[term] = math.log(
                1 + (self.num_docs - doc_freq + 0.5) / (doc_freq + 0.5)
            )

    # 5. Compute the BM25 score contribution of one query term for one passage.
    def _score_term(self, term, doc_idx):
        term_frequency = self.term_frequencies[doc_idx].get(term, 0)

        if term_frequency == 0:
            return 0

        doc_length = self.doc_lengths[doc_idx]

        if self.avg_doc_length == 0:
            length_normalization = 1
        else:
            length_normalization = (
                1 - self.b + self.b * doc_length / self.avg_doc_length
            )

        numerator = term_frequency * (self.k1 + 1)
        denominator = term_frequency + self.k1 * length_normalization

        return self.idf.get(term, 0) * numerator / denominator

    # 6. Retrieve and rank the top-k passages with the highest BM25 scores for a query.
    def retrieve(self, query: str, top_k: int = 10):
        if top_k <= 0:
            return []

        # Keep each query term only once.
        query_terms = set(tokenize(query))
        candidate_doc_ids = set()

        # Find passages containing at least one query term.
        for term in query_terms:
            candidate_doc_ids.update(self.inverted_index.get(term, []))

        scored_passages = []

        # Calculate BM25 score for every candidate passage.
        for doc_idx in candidate_doc_ids:
            score = 0

            for term in query_terms:
                score += self._score_term(term, doc_idx)

            # Remove passages with score 0.
            if score > 0:
                scored_passages.append(
                    {
                        "passage_id": self.passage_ids[doc_idx],
                        "score": score,
                    }
                )

        # Sort by score descending; use passage_id to break ties deterministically.
        scored_passages.sort(key=lambda x: (-x["score"], x["passage_id"]))

        return scored_passages[:top_k]