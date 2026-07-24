"""
Run a dense retrieval baseline for the HotpotQA evidence retrieval project.

This script loads processed queries, passages, and qrels; retrieves the top-k
passages for each query using a Sentence-BERT style dense retriever; evaluates
the ranked results with Recall, MRR, and nDCG; and writes both per-query and
summary result files for later analysis.
"""


import argparse
import sys
from pathlib import Path


# Add project modules to the import path when this script is run directly.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT / "src"))
sys.path.append(str(PROJECT_ROOT / "src" / "retrieval"))
sys.path.append(str(PROJECT_ROOT / "src" / "eval"))

from dense import DenseRetriever
from metrics import (
    load_qrels,
    mrr_at_k,
    ndcg_at_k,
    recall_at_k,
)
from result_format import (
    PER_QUERY_COLUMNS,
    SUMMARY_COLUMNS,
    build_per_query_metric_rows,
    build_summary_row,
)
from utils.result_io import load_jsonl, write_csv, write_jsonl


def run_retrieval(queries, passages, model_name, top_k, cache_dir, batch_size):
    """Retrieve top-k passages for every query using the dense retriever."""
    retriever = DenseRetriever(
        passages=passages,
        model_name=model_name,
        cache_dir=cache_dir,
        batch_size=batch_size,
    )
    results = {}
    output_records = []

    for index, query_record in enumerate(queries, start=1):
        query_id = query_record["query_id"]
        query = query_record["query"]
        ranked_results = retriever.retrieve(query, top_k=top_k)

        # metrics.py expects a query_id -> ranked results mapping.
        results[query_id] = ranked_results
        output_records.append(
            {
                "query_id": query_id,
                "query": query,
                "results": ranked_results,
            }
        )

        # Print out retrieval progress every 10 queries and at the end
        if index % 10 == 0 or index == len(queries):
            print(f"Retrieved {index}/{len(queries)} queries")

    return results, output_records


def short_model_name(model_name):
    """Return the final path segment of a model name for compact reporting."""
    return model_name.rstrip("/").split("/")[-1]


def main():
    """Parse command-line arguments, run retrieval, evaluate, and save outputs."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--queries", required=True)
    parser.add_argument("--passages", required=True)
    parser.add_argument("--qrels", required=True)
    parser.add_argument("--model", default="sentence-transformers/all-MiniLM-L6-v2")
    parser.add_argument("--top_k", type=int, default=10)
    parser.add_argument("--batch_size", type=int, default=64)
    parser.add_argument("--cache_dir", default="data/cache/dense")
    parser.add_argument("--topk_output", default="data/results/dense_top10.jsonl")
    parser.add_argument(
        "--per_query_output",
        default="reports/results/week3_dense_per_query.csv",
    )
    parser.add_argument(
        "--summary_output",
        default="reports/results/week3_dense_results.csv",
    )
    args = parser.parse_args()

    queries = load_jsonl(args.queries)
    passages = load_jsonl(args.passages)
    qrels = load_qrels(args.qrels)

    results, output_records = run_retrieval(
        queries=queries,
        passages=passages,
        model_name=args.model,
        top_k=args.top_k,
        cache_dir=args.cache_dir,
        batch_size=args.batch_size,
    )

    # Reuse one dictionary so each metric function can fill in per-query values.
    per_query_metrics = {}
    recall_at_5 = recall_at_k(results, qrels, 5, per_query_metrics)
    recall_at_10 = recall_at_k(results, qrels, 10, per_query_metrics)
    mrr_at_10 = mrr_at_k(results, qrels, 10, per_query_metrics)
    ndcg_at_10 = ndcg_at_k(results, qrels, 10, per_query_metrics)

    # Preserve the query file order in the per-query CSV.
    query_ids = [query_record["query_id"] for query_record in queries]
    per_query_rows = build_per_query_metric_rows(per_query_metrics, query_ids)
    summary_row = build_summary_row(
        method="dense",
        model=short_model_name(args.model),
        num_queries=len(queries),
        top_k=args.top_k,
        recall_at_5=recall_at_5,
        recall_at_10=recall_at_10,
        mrr_at_10=mrr_at_10,
        ndcg_at_10=ndcg_at_10,
    )

    write_jsonl(output_records, args.topk_output)
    write_csv(
        per_query_rows,
        args.per_query_output,
        fieldnames=PER_QUERY_COLUMNS,
    )
    write_csv(
        [summary_row],
        args.summary_output,
        fieldnames=SUMMARY_COLUMNS,
    )

    # Report saved output locations and final Dense retrieval scores.
    print(f"Wrote Dense top-{args.top_k} results to {args.topk_output}")
    print(f"Wrote per-query metrics to {args.per_query_output}")
    print(f"Wrote Dense summary to {args.summary_output}")
    print(f"Recall@5: {recall_at_5:.6f}")
    print(f"Recall@10: {recall_at_10:.6f}")
    print(f"MRR@10: {mrr_at_10:.6f}")
    print(f"nDCG@10: {ndcg_at_10:.6f}")


if __name__ == "__main__":
    main()
