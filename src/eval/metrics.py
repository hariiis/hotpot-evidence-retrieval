"""
Evaluation metrics for passage retrieval.

This module compares ranked retrieval results against qrels gold labels and
computes Recall@k, MRR@k, and nDCG@k for evidence retrieval.
"""

import json
import math
from collections import defaultdict


def load_results(results_path):
    """
    Load retrieval results from a jsonl file.

    Expected format:
    {
        "query_id": "q_000001",
        "results": [
            {"passage_id": "Scott Derrickson::0", "score": 12.3},
            {"passage_id": "Ed Wood::0", "score": 10.1}
        ]
    }
    """
    results = {}

    with open(results_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()

            if not line:
                continue

            record = json.loads(line)
            query_id = record["query_id"]
            ranked_results = record["results"]

            results[query_id] = ranked_results

    return results


def load_qrels(qrels_path):
    """
    Load qrels from a jsonl file.

    Expected format:
    {"query_id": "q_000001", "passage_id": "Scott Derrickson::0", "relevance": 1}
    """
    qrels = defaultdict(set)

    with open(qrels_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()

            if not line:
                continue

            record = json.loads(line)
            query_id = record["query_id"]
            passage_id = record["passage_id"]
            relevance = record.get("relevance", 1)

            if relevance > 0:
                qrels[query_id].add(passage_id)

    return dict(qrels)


def get_top_k_passage_ids(ranked_results, k):
    """
    Return passage IDs from the top-k ranked results.
    """
    top_k_passage_ids = []

    for result in ranked_results[:k]:
        top_k_passage_ids.append(result["passage_id"])

    return top_k_passage_ids


def recall_at_k(results, qrels, k, per_query_metrics=None):
    """
    Compute average Recall@k.

    Recall@k = number of retrieved gold passages in top-k / number of gold passages.
    """
    total_recall = 0
    num_queries = 0

    for query_id, gold_passages in qrels.items():
        if not gold_passages:
            continue

        ranked_results = results.get(query_id, [])
        top_k_passage_ids = get_top_k_passage_ids(ranked_results, k)

        retrieved_passages = set(top_k_passage_ids)
        hit_passages = retrieved_passages & gold_passages

        recall = len(hit_passages) / len(gold_passages)

        # Write Recall@k of every query into per_query_metrics
        if per_query_metrics is not None:
            record = per_query_metrics.setdefault(
                query_id, {"query_id": query_id}
            )
            record[f"recall_at_{k}"] = recall

            if recall == 1:
                record[f"retrieval_status at {k}"] = "success"
            elif recall == 0:
                record[f"retrieval_status at {k}"] = "failure"
            else:
                record[f"retrieval_status at {k}"] = "partial_success"

        total_recall += recall
        num_queries += 1

    if num_queries == 0:
        return 0

    return total_recall / num_queries


def mrr_at_k(results, qrels, k, per_query_metrics=None):
    """
    Compute average MRR@k.

    MRR@k rewards the rank of the first retrieved gold passage.
    """
    total_rr = 0
    num_queries = 0

    for query_id, gold_passages in qrels.items():
        if not gold_passages:
            continue

        ranked_results = results.get(query_id, [])
        top_k_passage_ids = get_top_k_passage_ids(ranked_results, k)

        reciprocal_rank = 0

        for rank, passage_id in enumerate(top_k_passage_ids, start=1):
            if passage_id in gold_passages:
                reciprocal_rank = 1 / rank
                break

        # Write MRR@k of every query into per_query_metrics
        if per_query_metrics is not None:
            record = per_query_metrics.setdefault(
                query_id, {"query_id": query_id}
            )
            record[f"mrr_at_{k}"] = reciprocal_rank
        
        total_rr += reciprocal_rank
        num_queries += 1

    if num_queries == 0:
        return 0

    return total_rr / num_queries


def ndcg_at_k(results, qrels, k, per_query_metrics=None):
    """
    Compute average nDCG@k.

    nDCG@k compares the actual ranking quality against the ideal ranking.
    """
    total_ndcg = 0
    num_queries = 0

    for query_id, gold_passages in qrels.items():
        if not gold_passages:
            continue

        ranked_results = results.get(query_id, [])
        top_k_passage_ids = get_top_k_passage_ids(ranked_results, k)

        dcg = 0
        # Track passages already counted so duplicate results do not increase nDCG.
        seen_passage_ids = set() 

        for rank, passage_id in enumerate(top_k_passage_ids, start=1):
            if passage_id in gold_passages and passage_id not in seen_passage_ids:
                relevance = 1
            else:
                relevance = 0

            dcg += relevance / math.log2(rank + 1)
            seen_passage_ids.add(passage_id)

        ideal_hits = min(len(gold_passages), k)
        idcg = 0

        for rank in range(1, ideal_hits + 1):
            idcg += 1 / math.log2(rank + 1)

        if idcg == 0:
            ndcg = 0
        else:
            ndcg = dcg / idcg

        # Write nDCG@k of every query into per_query_metrics
        if per_query_metrics is not None:
            record = per_query_metrics.setdefault(
                query_id, {"query_id": query_id}
            )
            record[f"ndcg_at_{k}"] = ndcg
        
        total_ndcg += ndcg
        num_queries += 1

    if num_queries == 0:
        return 0

    return total_ndcg / num_queries

def write_per_query_metrics(per_query_metrics, output_path):
    """
    Write already computed per-query metrics to a jsonl file.
    """
    with open(output_path, "w", encoding="utf-8") as f:
        for query_id in sorted(per_query_metrics):
            record = per_query_metrics[query_id]
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
