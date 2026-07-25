"""
Run Hybrid retrieval experiments for the HotpotQA evidence retrieval project.

This script evaluates three hybrid settings:
- alpha = 0.25
- alpha = 0.50
- alpha = 0.75

Each run uses the same queries, passages, qrels, and metrics as the BM25 and
Dense baselines, then writes top-k rankings, per-query metrics, and summary
CSV files.
"""

import argparse
import sys
from pathlib import Path


# Add project modules to the import path when this script is run directly.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT / "src"))
sys.path.append(str(PROJECT_ROOT / "src" / "retrieval"))
sys.path.append(str(PROJECT_ROOT / "src" / "eval"))

from dense import DEFAULT_MODEL_NAME
from hybrid import HybridRetriever
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


def run_retrieval(queries, retriever, top_k, candidate_k):
    """Retrieve top-k passages for every query using one HybridRetriever."""
    results = {}
    output_records = []

    for index, query_record in enumerate(queries, start=1):
        query_id = query_record["query_id"]
        query = query_record["query"]
        ranked_results = retriever.retrieve(
            query,
            top_k=top_k,
            candidate_k=candidate_k,
        )

        # metrics.py expects a query_id -> ranked results mapping.
        results[query_id] = ranked_results
        output_records.append(
            {
                "query_id": query_id,
                "query": query,
                "results": ranked_results,
            }
        )

        # Print retrieval progress every 10 queries and at the end.
        if index % 10 == 0 or index == len(queries):
            print(f"Retrieved {index}/{len(queries)} queries")

    return results, output_records


def short_model_name(model_name):
    """Return the final path segment of a model name for compact reporting."""
    return model_name.rstrip("/").split("/")[-1]


def format_alpha(alpha):
    """Format alpha for stable method labels and output filenames."""
    alpha_text = f"{alpha:.2f}"
    alpha_label = alpha_text.replace(".", "")
    return alpha_text, alpha_label


def evaluate_results(queries, qrels, results):
    """Compute Recall@5, Recall@10, MRR@10, nDCG@10, and per-query rows."""
    per_query_metrics = {}
    recall_at_5 = recall_at_k(results, qrels, 5, per_query_metrics)
    recall_at_10 = recall_at_k(results, qrels, 10, per_query_metrics)
    mrr_at_10 = mrr_at_k(results, qrels, 10, per_query_metrics)
    ndcg_at_10 = ndcg_at_k(results, qrels, 10, per_query_metrics)

    # Preserve the query file order in the per-query CSV.
    query_ids = [query_record["query_id"] for query_record in queries]
    per_query_rows = build_per_query_metric_rows(per_query_metrics, query_ids)

    return per_query_rows, recall_at_5, recall_at_10, mrr_at_10, ndcg_at_10


def run_alpha_experiment(args, queries, passages, qrels, alpha):
    """Run retrieval, evaluate metrics, and write files for one alpha value."""
    alpha_text, alpha_label = format_alpha(alpha)
    print(f"Running Hybrid retrieval with alpha={alpha_text}")

    retriever = HybridRetriever(
        passages=passages,
        alpha=alpha,
        bm25_k1=args.k1,
        bm25_b=args.b,
        dense_model=args.model,
        cache_dir=args.cache_dir,
        batch_size=args.batch_size,
    )

    results, output_records = run_retrieval(
        queries=queries,
        retriever=retriever,
        top_k=args.top_k,
        candidate_k=args.candidate_k,
    )

    per_query_rows, recall_at_5, recall_at_10, mrr_at_10, ndcg_at_10 = (
        evaluate_results(queries, qrels, results)
    )

    summary_row = build_summary_row(
        method=f"hybrid_alpha_{alpha_text}",
        model=f"bm25+dense:{short_model_name(args.model)}",
        num_queries=len(queries),
        top_k=args.top_k,
        recall_at_5=recall_at_5,
        recall_at_10=recall_at_10,
        mrr_at_10=mrr_at_10,
        ndcg_at_10=ndcg_at_10,
    )

    topk_output = f"{args.output_dir}/hybrid_alpha_{alpha_label}_top{args.top_k}.jsonl"
    per_query_output = f"{args.report_dir}/alpha_{alpha_label}_per_query.csv"
    summary_output = f"{args.report_dir}/alpha_{alpha_label}_summary.csv"

    write_jsonl(output_records, topk_output)
    write_csv(per_query_rows, per_query_output, fieldnames=PER_QUERY_COLUMNS)
    write_csv([summary_row], summary_output, fieldnames=SUMMARY_COLUMNS)

    # Report output locations and the metrics needed for the experiment table.
    print(f"Wrote Hybrid top-{args.top_k} results to {topk_output}")
    print(f"Wrote per-query metrics to {per_query_output}")
    print(f"Wrote Hybrid summary to {summary_output}")
    print(f"Recall@10: {recall_at_10:.6f}")
    print(f"MRR@10: {mrr_at_10:.6f}")
    print(f"nDCG@10: {ndcg_at_10:.6f}")

    return summary_row


def main():
    """Parse arguments, run all alpha experiments, and save one combined CSV."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--queries", required=True)
    parser.add_argument("--passages", required=True)
    parser.add_argument("--qrels", required=True)
    parser.add_argument("--top_k", type=int, default=10)
    parser.add_argument("--candidate_k", type=int, default=100)
    parser.add_argument("--alphas", type=float, nargs="+", default=[0.25, 0.5, 0.75])
    parser.add_argument("--k1", type=float, default=1.5)
    parser.add_argument("--b", type=float, default=0.75)
    parser.add_argument("--model", default=DEFAULT_MODEL_NAME)
    parser.add_argument("--batch_size", type=int, default=64)
    parser.add_argument("--cache_dir", default="data/cache/dense")
    parser.add_argument("--output_dir", default="data/results")
    parser.add_argument("--report_dir", default="reports/results/week3_hybrid")
    args = parser.parse_args()

    queries = load_jsonl(args.queries)
    passages = load_jsonl(args.passages)
    qrels = load_qrels(args.qrels)

    all_summary_rows = []
    for alpha in args.alphas:
        summary_row = run_alpha_experiment(args, queries, passages, qrels, alpha)
        all_summary_rows.append(summary_row)

    # This file makes it easy to compare alpha=0.25/0.50/0.75 in one table.
    combined_summary_output = f"{args.report_dir}/summary_all.csv"
    write_csv(
        all_summary_rows,
        combined_summary_output,
        fieldnames=SUMMARY_COLUMNS,
    )

    print(f"Wrote combined Hybrid summary to {combined_summary_output}")


if __name__ == "__main__":
    main()
