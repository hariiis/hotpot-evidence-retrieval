"""
Run the Week 6 filtering ablation experiments.

This script is intentionally an orchestration layer over the existing BM25 and
graph query-expansion code. It runs the three required settings, writes the
standard per-run artifacts, and additionally writes one aggregate comparison CSV
for the ablation table.
"""

import argparse
import math
import sys
from dataclasses import dataclass
from pathlib import Path


# Add project modules and experiment helpers when this script is run directly.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT / "experiments"))
sys.path.append(str(PROJECT_ROOT / "src"))
sys.path.append(str(PROJECT_ROOT / "src" / "eval"))
sys.path.append(str(PROJECT_ROOT / "src" / "retrieval"))

from bm25 import BM25Retriever, load_passages
from run_bm25 import run_bm25_experiment
from run_query_expansion import (
    build_qrels_by_id,
    build_query_concepts_by_id,
    format_float,
    run_query_expansion_experiment,
)
from utils.file_io import load_graph, load_jsonl, write_csv


FILTER_RULE = "top_1_percent_by_passage_count"
FILTER_THRESHOLD = 0.01

ABLATION_COLUMNS = [
    "experiment_name",
    "num_queries",
    "strategy",
    "hop",
    "top_n",
    "filtering",
    "filter_rule",
    "filter_threshold",
    "recall_at_5",
    "recall_at_10",
    "mrr_at_10",
    "ndcg_at_10",
    "delta_recall_at_10_vs_baseline",
    "delta_mrr_at_10_vs_baseline",
    "delta_ndcg_at_10_vs_baseline",
]

BLOCKLIST_COLUMNS = [
    "rank",
    "concept",
    "passage_count",
    "filter_rule",
    "filter_threshold",
]


@dataclass(frozen=True)
class ExperimentConfig:
    """Store the fixed parameters for one ablation experiment row."""

    name: str
    output_name: str
    hop: int
    top_n: int
    strategy: str
    filtering: bool


def parse_args():
    """Parse command-line arguments for the Week 6 ablation runner."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--queries",
        default="data/processed/hotpotqa/queries.jsonl",
    )
    parser.add_argument(
        "--passages",
        default="data/processed/hotpotqa/passages.jsonl",
    )
    parser.add_argument(
        "--qrels",
        default="data/processed/hotpotqa/qrels.jsonl",
    )
    parser.add_argument(
        "--query_concepts",
        default="data/processed/concepts/query_concepts.jsonl",
    )
    parser.add_argument(
        "--graph",
        default="data/processed/concept_graph.pkl",
    )
    parser.add_argument("--top_k", type=int, default=10)
    parser.add_argument("--k1", type=float, default=1.5)
    parser.add_argument("--b", type=float, default=0.75)
    parser.add_argument(
        "--output_dir",
        default="reports/results/week6_ablation",
    )
    parser.add_argument(
        "--aggregate_output",
        default="reports/results/week6_ablation/week6_ablation_results.csv",
    )
    args = parser.parse_args()

    if args.top_k < 10:
        parser.error("--top_k must be at least 10 to compute @10 metrics")

    return args


def get_experiment_configs():
    """Return the three fixed experiment settings requested for the ablation."""
    return [
        ExperimentConfig(
            name="BM25 baseline",
            output_name="bm25_baseline",
            hop=0,
            top_n=0,
            strategy="none",
            filtering=False,
        ),
        ExperimentConfig(
            name="main expansion",
            output_name="main_expansion",
            hop=1,
            top_n=5,
            strategy="edge_weight_log_passage_count",
            filtering=False,
        ),
        ExperimentConfig(
            name="filtered expansion",
            output_name="filtered_expansion",
            hop=1,
            top_n=5,
            strategy="edge_weight_log_passage_count",
            filtering=True,
        ),
    ]


def build_high_passage_count_blocklist(graph, threshold=FILTER_THRESHOLD):
    """
    Select generic concepts by passage_count rank without mutating the graph.

    The rule is deterministic: sort concepts by passage_count descending, then
    by concept string ascending, and filter the first ceil(N * threshold).
    """
    ranked_concepts = sorted(
        graph.nodes,
        key=lambda concept: (
            -int(graph.nodes[concept].get("passage_count", 0)),
            str(concept),
        ),
    )
    cutoff = math.ceil(len(ranked_concepts) * threshold)

    return set(ranked_concepts[:cutoff])


def write_high_passage_count_blocklist(graph, blocked_concepts, output_path):
    """Write the filtered expansion concept blocklist for reproducibility."""
    rows = []
    ranked_blocked_concepts = sorted(
        blocked_concepts,
        key=lambda concept: (
            -int(graph.nodes[concept].get("passage_count", 0)),
            str(concept),
        ),
    )

    for rank, concept in enumerate(ranked_blocked_concepts, start=1):
        rows.append(
            {
                "rank": rank,
                "concept": concept,
                "passage_count": graph.nodes[concept].get("passage_count", 0),
                "filter_rule": FILTER_RULE,
                "filter_threshold": format_float(FILTER_THRESHOLD),
            }
        )

    write_csv(rows, output_path, fieldnames=BLOCKLIST_COLUMNS)


def run_bm25_baseline(config, args, queries, passages, qrels, output_root):
    """Run the reusable BM25 experiment function for the baseline row."""
    output_dir = output_root / config.output_name
    outputs = run_bm25_experiment(
        queries=queries,
        passages=passages,
        qrels=qrels,
        top_k=args.top_k,
        k1=args.k1,
        b=args.b,
        topk_output=output_dir / "topk.jsonl",
        per_query_output=output_dir / "per_query.csv",
        summary_output=output_dir / "summary.csv",
    )

    return build_ablation_row(config, args, len(queries), outputs["summary"])


def run_expansion_experiment(
    config,
    args,
    queries,
    query_concepts_by_id,
    graph,
    retriever,
    qrels,
    blocked_concepts,
    output_root,
):
    """Run the reusable query-expansion package function for one ablation row."""
    output_dir = output_root / config.output_name
    active_blocklist = blocked_concepts if config.filtering else None
    outputs = run_query_expansion_experiment(
        queries=queries,
        query_concepts_by_id=query_concepts_by_id,
        graph=graph,
        retriever=retriever,
        qrels=qrels,
        hop=config.hop,
        top_n=config.top_n,
        strategy=config.strategy,
        top_k=args.top_k,
        k1=args.k1,
        b=args.b,
        output_dir=output_dir,
        blocked_concepts=active_blocklist, 
    )

    return build_ablation_row(config, args, len(queries), outputs["summary"])


def build_ablation_row(config, args, num_queries, summary):
    """Build one row for the aggregate Week 6 ablation comparison CSV."""
    filtering_label = "on" if config.filtering else "off"
    filter_rule = FILTER_RULE if config.filtering else "none"
    filter_threshold = format_float(FILTER_THRESHOLD) if config.filtering else ""

    return {
        "experiment_name": config.name,
        "num_queries": num_queries,
        "strategy": config.strategy,
        "hop": config.hop,
        "top_n": config.top_n,
        "filtering": filtering_label,
        "filter_rule": filter_rule,
        "filter_threshold": filter_threshold,
        "recall_at_5": format_float(summary["recall_at_5"]),
        "recall_at_10": format_float(summary["recall_at_10"]),
        "mrr_at_10": format_float(summary["mrr_at_10"]),
        "ndcg_at_10": format_float(summary["ndcg_at_10"]),
        "delta_recall_at_10_vs_baseline": "",
        "delta_mrr_at_10_vs_baseline": "",
        "delta_ndcg_at_10_vs_baseline": "",
    }


def add_baseline_deltas(rows):
    """Fill metric deltas for every row against the BM25 baseline row."""
    baseline = rows[0]
    baseline_recall = float(baseline["recall_at_10"])
    baseline_mrr = float(baseline["mrr_at_10"])
    baseline_ndcg = float(baseline["ndcg_at_10"])

    for row in rows:
        row["delta_recall_at_10_vs_baseline"] = format_float(
            float(row["recall_at_10"]) - baseline_recall
        )
        row["delta_mrr_at_10_vs_baseline"] = format_float(
            float(row["mrr_at_10"]) - baseline_mrr
        )
        row["delta_ndcg_at_10_vs_baseline"] = format_float(
            float(row["ndcg_at_10"]) - baseline_ndcg
        )

    return rows


def main():
    """Load shared inputs, run all ablation settings, and write comparisons."""
    args = parse_args()
    output_root = Path(args.output_dir)

    queries = load_jsonl(args.queries)
    passages = load_passages(args.passages)
    qrel_rows = load_jsonl(args.qrels)
    query_concept_rows = load_jsonl(args.query_concepts)
    graph = load_graph(args.graph)

    qrels = build_qrels_by_id(qrel_rows)
    query_concepts_by_id = build_query_concepts_by_id(query_concept_rows)
    blocked_concepts = build_high_passage_count_blocklist(graph)
    write_high_passage_count_blocklist(
        graph=graph,
        blocked_concepts=blocked_concepts,
        output_path=output_root / "filtered_expansion_concept_blocklist.csv",
    )

    # Build the BM25 index once for expansion runs after the standalone
    # baseline has written its own normal BM25 artifacts.
    retriever = BM25Retriever(passages, k1=args.k1, b=args.b)

    rows = []
    for config in get_experiment_configs():
        print(f"Running {config.name}")

        if config.hop == 0:
            row = run_bm25_baseline(
                config,
                args,
                queries,
                passages,
                qrels,
                output_root,
            )
        else:
            row = run_expansion_experiment(
                config=config,
                args=args,
                queries=queries,
                query_concepts_by_id=query_concepts_by_id,
                graph=graph,
                retriever=retriever,
                qrels=qrels,
                blocked_concepts=blocked_concepts,
                output_root=output_root,
            )

        rows.append(row)

    rows = add_baseline_deltas(rows)
    write_csv(rows, args.aggregate_output, fieldnames=ABLATION_COLUMNS)

    print(f"Wrote aggregate ablation results to {args.aggregate_output}")


if __name__ == "__main__":
    main()
