"""
Run a BM25 retrieval baseline for the HotpotQA evidence retrieval project.

This script loads processed queries, passages, and qrels; retrieves the top-k
passages for each query using BM25; evaluates the ranked results with Recall,
MRR, and nDCG; and writes top-k rankings, per-query metrics, and one summary
CSV with the same output structure as the dense baseline.
"""

import argparse
import sys
from pathlib import Path


# Add project modules to the import path when this script is run directly.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT / "src"))
sys.path.append(str(PROJECT_ROOT / "src" / "retrieval"))
sys.path.append(str(PROJECT_ROOT / "src" / "eval"))

from bm25 import BM25Retriever, load_passages
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
from utils.file_io import load_jsonl, write_csv, write_jsonl


def run_retrieval(queries, passages, top_k, k1, b):
    """Retrieve top-k passages for every query using the BM25 retriever."""
    retriever = BM25Retriever(passages, k1=k1, b=b)
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

        # Print out retrieval progress every 10 queries and at the end.
        if index % 10 == 0 or index == len(queries):
            print(f"Retrieved {index}/{len(queries)} queries")

    return results, output_records


def bm25_model_name(k1, b):
    """Return a compact label for the BM25 parameter setting."""
    return f"k1={k1}_b={b}"


def run_bm25_experiment(
    queries,
    passages,
    qrels,
    top_k,
    k1,
    b,
    topk_output,
    per_query_output,
    summary_output,
):
    """
    Run BM25 retrieval, evaluate it, write artifacts, and return metrics.

    This function keeps the command-line behavior reusable by orchestration
    scripts such as the Week 6 ablation runner.
    """
    results, output_records = run_retrieval(
        queries=queries,
        passages=passages,
        top_k=top_k,
        k1=k1,
        b=b,
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
        method="bm25",
        model=bm25_model_name(k1, b),
        num_queries=len(queries),
        top_k=top_k,
        recall_at_5=recall_at_5,
        recall_at_10=recall_at_10,
        mrr_at_10=mrr_at_10,
        ndcg_at_10=ndcg_at_10,
    )

    write_jsonl(output_records, topk_output)
    write_csv(
        per_query_rows,
        per_query_output,
        fieldnames=PER_QUERY_COLUMNS,
    )
    write_csv(
        [summary_row],
        summary_output,
        fieldnames=SUMMARY_COLUMNS,
    )

    summary = {
        "recall_at_5": recall_at_5,
        "recall_at_10": recall_at_10,
        "mrr_at_10": mrr_at_10,
        "ndcg_at_10": ndcg_at_10,
    }

    # Report saved output locations and final BM25 retrieval scores.
    print(f"Wrote BM25 top-{top_k} results to {topk_output}")
    print(f"Wrote per-query metrics to {per_query_output}")
    print(f"Wrote BM25 summary to {summary_output}")
    print(f"Recall@5: {recall_at_5:.6f}")
    print(f"Recall@10: {recall_at_10:.6f}")
    print(f"MRR@10: {mrr_at_10:.6f}")
    print(f"nDCG@10: {ndcg_at_10:.6f}")

    return {
        "results_by_id": results,
        "topk_records": output_records,
        "per_query_rows": per_query_rows,
        "summary_row": summary_row,
        "summary": summary,
    }


def main():
    """Parse command-line arguments, run retrieval, evaluate, and save outputs."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--queries", required=True)
    parser.add_argument("--passages", required=True)
    parser.add_argument("--qrels", required=True)
    parser.add_argument("--top_k", type=int, default=10)
    parser.add_argument("--k1", type=float, default=1.5)
    parser.add_argument("--b", type=float, default=0.75)
    parser.add_argument("--topk_output", default="data/results/bm25_top10.jsonl")
    parser.add_argument(
        "--per_query_output",
        default="reports/results/week2_bm25/per_query.csv",
    )
    parser.add_argument(
        "--summary_output",
        default="reports/results/week2_bm25/summary.csv",
    )
    args = parser.parse_args()

    queries = load_jsonl(args.queries)
    passages = load_passages(args.passages)
    qrels = load_qrels(args.qrels)
    run_bm25_experiment(
        queries=queries,
        passages=passages,
        top_k=args.top_k,
        k1=args.k1,
        b=args.b,
        qrels=qrels,
        topk_output=args.topk_output,
        per_query_output=args.per_query_output,
        summary_output=args.summary_output,
    )


if __name__ == "__main__":
    main()
