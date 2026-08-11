"""
Run graph-based query expansion with BM25 retrieval.

This Week 5 experiment script connects the graph expansion trace from
retrieval.graph_query_expansion to the Week 2 BM25 retriever. Each run writes a
complete result package under one output directory:

- topk.jsonl
- per_query.csv
- summary.csv
- expansion_traces.jsonl
"""

import argparse
import sys
from pathlib import Path


# Add project modules to the import path when this script is run directly.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT / "src"))
sys.path.append(str(PROJECT_ROOT / "src" / "retrieval"))
sys.path.append(str(PROJECT_ROOT / "src" / "eval"))

from bm25 import BM25Retriever
from graph_query_expansion import SUPPORTED_RANKING_STRATEGIES, expand_query
from metrics import mrr_at_k, ndcg_at_k, recall_at_k
from utils.file_io import load_graph, load_jsonl, write_csv, write_jsonl


PER_QUERY_COLUMNS = [
    "method",
    "hop",
    "top_n",
    "strategy",
    "k1",
    "b",
    "query_id",
    "recall_at_5",
    "recall_at_10",
    "mrr_at_10",
    "ndcg_at_10",
]

SUMMARY_COLUMNS = [
    "method",
    "hop",
    "top_n",
    "strategy",
    "k1",
    "b",
    "num_queries",
    "recall_at_5",
    "recall_at_10",
    "mrr_at_10",
    "ndcg_at_10",
]


def parse_args():
    """Parse command-line arguments for one query expansion experiment run."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--queries", required=True)
    parser.add_argument("--passages", required=True)
    parser.add_argument("--qrels", required=True)
    parser.add_argument("--query_concepts", required=True)
    parser.add_argument("--graph", required=True)
    parser.add_argument("--hop", type=int, default=1)
    parser.add_argument("--top_n", type=int, default=5)
    parser.add_argument("--strategy", default="edge_weight")
    parser.add_argument("--top_k", type=int, default=10)
    parser.add_argument("--k1", type=float, default=1.5)
    parser.add_argument("--b", type=float, default=0.75)
    parser.add_argument("--output_dir", required=True)
    args = parser.parse_args()

    if args.hop not in {0, 1, 2}:
        parser.error("--hop must be 0, 1, or 2")
    if args.top_n < 0:
        parser.error("--top_n must be greater than or equal to 0")
    if args.top_k < 10:
        parser.error("--top_k must be at least 10 to compute @10 metrics")
    if args.strategy not in SUPPORTED_RANKING_STRATEGIES:
        supported = "', '".join(sorted(SUPPORTED_RANKING_STRATEGIES))
        parser.error(f"--strategy must be one of '{supported}'")

    return args


def build_query_concepts_by_id(query_concept_rows):
    """Return query_id -> normalized query concepts."""
    return {
        row["query_id"]: row.get("concepts") or []
        for row in query_concept_rows
    }


def build_qrels_by_id(qrel_rows):
    """Return query_id -> positive gold passage_id set for metric evaluation."""
    qrels_by_id = {}

    for row in qrel_rows:
        if row.get("relevance", 1) <= 0:
            continue

        query_id = row["query_id"]
        passage_id = row["passage_id"]
        qrels_by_id.setdefault(query_id, set()).add(passage_id)

    return qrels_by_id


def experiment_method_name(hop):
    """Return the method label used in CSV outputs."""
    if hop == 0:
        return "bm25_baseline"

    return "query_expansion_bm25"


def format_float(value):
    """Format experiment parameters and metrics with stable precision."""
    return f"{value:.6f}"


def run_query_expansion_experiment(
    queries,
    query_concepts_by_id,
    graph,
    retriever,
    hop,
    top_n,
    strategy,
    top_k,
):
    """
    Expand every query, retrieve with BM25, and collect result records.

    The BM25 retriever is passed in after being built once over all passages.
    """
    results_by_id = {}
    topk_records = []
    expansion_traces = []

    for index, query_record in enumerate(queries, start=1):
        query_id = query_record["query_id"]
        original_query = query_record["query"]
        query_concepts = query_concepts_by_id.get(query_id, [])

        expansion = expand_query(
            query=original_query,
            query_concepts=query_concepts,
            graph=graph,
            hop=hop,
            top_n=top_n,
            strategy=strategy,
        )

        # Keep original_query in outputs, but retrieve with the expanded query.
        ranked_results = retriever.retrieve(
            expansion["expanded_query"],
            top_k=top_k,
        )

        results_by_id[query_id] = ranked_results
        topk_records.append(
            {
                "query_id": query_id,
                "query": original_query,
                "expanded_query": expansion["expanded_query"],
                "results": ranked_results,
            }
        )
        expansion_traces.append(
            {
                "query_id": query_id,
                "original_query": expansion["original_query"],
                "query_concepts": expansion["query_concepts"],
                "matched_graph_nodes": expansion["matched_graph_nodes"],
                "unmatched_query_concepts": (
                    expansion["unmatched_query_concepts"]
                ),
                "expanded_concepts": expansion["expanded_concepts"],
                "expanded_query": expansion["expanded_query"],
            }
        )

        if index % 10 == 0 or index == len(queries):
            print(f"Expanded and retrieved {index}/{len(queries)} queries")

    return results_by_id, topk_records, expansion_traces


def evaluate_results(queries, qrels, results_by_id):
    """
    Compute per-query metrics and summary metrics.

    The summary values are simple averages over the per-query metric rows in
    the original query order.
    """
    per_query_metrics = {}
    recall_at_k(results_by_id, qrels, 5, per_query_metrics)
    recall_at_k(results_by_id, qrels, 10, per_query_metrics)
    mrr_at_k(results_by_id, qrels, 10, per_query_metrics)
    ndcg_at_k(results_by_id, qrels, 10, per_query_metrics)

    query_ids = [query_record["query_id"] for query_record in queries]
    summary = {
        "recall_at_5": 0.0,
        "recall_at_10": 0.0,
        "mrr_at_10": 0.0,
        "ndcg_at_10": 0.0,
    }
    per_query_rows = []

    for query_id in query_ids:
        metrics = per_query_metrics.get(query_id, {})
        row = {
            "query_id": query_id,
            "recall_at_5": metrics.get("recall_at_5", 0.0),
            "recall_at_10": metrics.get("recall_at_10", 0.0),
            "mrr_at_10": metrics.get("mrr_at_10", 0.0),
            "ndcg_at_10": metrics.get("ndcg_at_10", 0.0),
        }
        per_query_rows.append(row)

        for metric_name in summary:
            summary[metric_name] += row[metric_name]

    if query_ids:
        for metric_name in summary:
            summary[metric_name] /= len(query_ids)

    return per_query_rows, summary


def add_experiment_columns(rows, args, method):
    """Attach experiment parameters to each per-query metric row."""
    enriched_rows = []

    for row in rows:
        enriched_rows.append(
            {
                "method": method,
                "hop": args.hop,
                "top_n": args.top_n,
                "strategy": args.strategy,
                "k1": format_float(args.k1),
                "b": format_float(args.b),
                "query_id": row["query_id"],
                "recall_at_5": format_float(row["recall_at_5"]),
                "recall_at_10": format_float(row["recall_at_10"]),
                "mrr_at_10": format_float(row["mrr_at_10"]),
                "ndcg_at_10": format_float(row["ndcg_at_10"]),
            }
        )

    return enriched_rows


def build_summary_row(args, method, num_queries, summary):
    """Build the one-row summary.csv record for this parameter setting."""
    return {
        "method": method,
        "hop": args.hop,
        "top_n": args.top_n,
        "strategy": args.strategy,
        "k1": format_float(args.k1),
        "b": format_float(args.b),
        "num_queries": num_queries,
        "recall_at_5": format_float(summary["recall_at_5"]),
        "recall_at_10": format_float(summary["recall_at_10"]),
        "mrr_at_10": format_float(summary["mrr_at_10"]),
        "ndcg_at_10": format_float(summary["ndcg_at_10"]),
    }


def write_outputs(output_dir, topk_records, per_query_rows, summary_row, traces):
    """Write the four standard output files for one experiment run."""
    output_dir = Path(output_dir)

    write_jsonl(topk_records, output_dir / "topk.jsonl")
    write_csv(per_query_rows, output_dir / "per_query.csv", PER_QUERY_COLUMNS)
    write_csv([summary_row], output_dir / "summary.csv", SUMMARY_COLUMNS)
    write_jsonl(traces, output_dir / "expansion_traces.jsonl")


def main():
    """Load inputs, run query expansion retrieval, evaluate, and save outputs."""
    args = parse_args()

    queries = load_jsonl(args.queries)
    passages = load_jsonl(args.passages)
    qrel_rows = load_jsonl(args.qrels)
    query_concept_rows = load_jsonl(args.query_concepts)
    graph = load_graph(args.graph)

    qrels = build_qrels_by_id(qrel_rows)
    query_concepts_by_id = build_query_concepts_by_id(query_concept_rows)

    # Build the corpus-level BM25 index once, then reuse it for every query.
    retriever = BM25Retriever(passages, k1=args.k1, b=args.b)

    results_by_id, topk_records, expansion_traces = (
        run_query_expansion_experiment(
            queries=queries,
            query_concepts_by_id=query_concepts_by_id,
            graph=graph,
            retriever=retriever,
            hop=args.hop,
            top_n=args.top_n,
            strategy=args.strategy,
            top_k=args.top_k,
        )
    )
    per_query_rows, summary = evaluate_results(queries, qrels, results_by_id)

    method = experiment_method_name(args.hop)
    per_query_rows = add_experiment_columns(per_query_rows, args, method)
    summary_row = build_summary_row(
        args=args,
        method=method,
        num_queries=len(queries),
        summary=summary,
    )

    write_outputs(
        output_dir=args.output_dir,
        topk_records=topk_records,
        per_query_rows=per_query_rows,
        summary_row=summary_row,
        traces=expansion_traces,
    )

    print(f"Wrote top-k results to {args.output_dir}/topk.jsonl")
    print(f"Wrote per-query metrics to {args.output_dir}/per_query.csv")
    print(f"Wrote summary metrics to {args.output_dir}/summary.csv")
    print(f"Wrote expansion traces to {args.output_dir}/expansion_traces.jsonl")


if __name__ == "__main__":
    main()
