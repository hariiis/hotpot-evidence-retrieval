"""
Analyze Week 6 retrieval metrics by HotpotQA query type.

This script connects per-query metric CSV files with HotpotQA query metadata,
then aggregates retrieval quality separately for bridge and comparison queries.
It writes the required query-type breakdown CSV for the Week 6 analysis.
"""

import argparse
import csv
import sys
from dataclasses import dataclass
from pathlib import Path


# Add project modules to the import path when this script is run directly.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT / "src"))

from utils.file_io import load_jsonl, write_csv


QUERY_TYPES = ["bridge", "comparison"]
METRIC_NAMES = [
    "recall_at_5",
    "recall_at_10",
    "mrr_at_10",
    "ndcg_at_10",
]
DELTA_METRIC_NAMES = [
    "recall_at_10",
    "mrr_at_10",
    "ndcg_at_10",
]
OUTPUT_COLUMNS = [
    "method",
    "query_type",
    "num_queries",
    "recall_at_5",
    "recall_at_10",
    "mrr_at_10",
    "ndcg_at_10",
    "delta_recall_at_10_vs_baseline",
    "delta_mrr_at_10_vs_baseline",
    "delta_ndcg_at_10_vs_baseline",
]

# The existing BM25 baseline and graph-expansion runs use different per-query
# CSV column names, so each canonical metric accepts all known aliases.
METRIC_COLUMN_ALIASES = {
    "recall_at_5": ["recall_at_5", "Recall@5"],
    "recall_at_10": ["recall_at_10", "Recall@10"],
    "mrr_at_10": ["mrr_at_10", "MRR@10", "RR@10"],
    "ndcg_at_10": ["ndcg_at_10", "nDCG@10"],
}

# 0. Helper

def format_float(value):
    """Format metric values with the same stable precision as other reports."""
    return f"{value:.6f}"


# 1. Configuration

def parse_args():
    """Parse command-line arguments for the query-type breakdown analysis."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--queries",
        default="data/processed/hotpotqa/queries.jsonl",
        help="HotpotQA processed query metadata with query_id and type fields.",
    )
    parser.add_argument(
        "--bm25_per_query",
        default="reports/results/week6_ablation/bm25_baseline/per_query.csv",
        help="Per-query metrics CSV for the BM25 baseline.",
    )
    parser.add_argument(
        "--main_expansion_per_query",
        default="reports/results/week6_ablation/main_expansion/per_query.csv",
        help="Per-query metrics CSV for the main graph-expansion run.",
    )
    parser.add_argument(
        "--filtered_expansion_per_query",
        default="reports/results/week6_ablation/filtered_expansion/per_query.csv",
        help="Per-query metrics CSV for the filtered graph-expansion run.",
    )
    parser.add_argument(
        "--output",
        default="reports/results/week6_query_type_results.csv",
        help="Output CSV path for bridge/comparison aggregate metrics.",
    )

    return parser.parse_args()

@dataclass(frozen=True)
class MethodConfig:
    """Store one method label and its per-query metric CSV path."""

    method: str
    per_query_path: Path

def get_method_configs(args):
    """Return the required Week 6 methods in output order."""
    return [
        MethodConfig("BM25 baseline", Path(args.bm25_per_query)),
        MethodConfig("main expansion", Path(args.main_expansion_per_query)),
        MethodConfig(
            "filtered expansion",
            Path(args.filtered_expansion_per_query),
        ),
    ]


# 2. Loading

def load_query_types(queries_path):
    """Return query_id -> HotpotQA query type for bridge/comparison queries."""
    query_types = {}
    skipped_rows = 0

    for row in load_jsonl(queries_path):
        query_id = row.get("query_id")
        query_type = row.get("type")

        if not query_id or query_type not in QUERY_TYPES:
            skipped_rows += 1
            continue

        query_types[query_id] = query_type

    if skipped_rows:
        print(f"Skipped {skipped_rows} query rows without a supported type")

    return query_types


def first_present_column(fieldnames, aliases, source_path):
    """Return the first available column name from a list of metric aliases."""
    for alias in aliases:
        if alias in fieldnames:
            return alias

    joined_aliases = ", ".join(aliases)
    raise ValueError(
        f"{source_path} is missing one of these columns: {joined_aliases}"
    )


def load_per_query_metrics(per_query_path):
    """Load per-query metrics as query_id -> canonical metric dictionary."""
    per_query_path = Path(per_query_path)
    metrics_by_id = {}

    with per_query_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)

        if not reader.fieldnames or "query_id" not in reader.fieldnames:
            raise ValueError(f"{per_query_path} must contain a query_id column")

        metric_columns = {
            metric_name: first_present_column(
                reader.fieldnames,
                aliases,
                per_query_path,
            )
            for metric_name, aliases in METRIC_COLUMN_ALIASES.items()
        }

        for row in reader:
            query_id = row["query_id"]

            if query_id in metrics_by_id:
                raise ValueError(
                    f"Duplicate query_id in {per_query_path}: {query_id}"
                )

            metrics_by_id[query_id] = {
                metric_name: float(row[column_name])
                for metric_name, column_name in metric_columns.items()
            }

    return metrics_by_id


# 3. Validation

def validate_method_query_sets(raw_metrics):
    """Raise when methods do not contain exactly the same query IDs."""
    baseline_ids = set(raw_metrics["BM25 baseline"])

    for method, metrics_by_id in raw_metrics.items():
        method_ids = set(metrics_by_id)

        if method_ids == baseline_ids:
            continue

        missing_ids = baseline_ids - method_ids
        extra_ids = method_ids - baseline_ids
        missing_examples = ", ".join(sorted(missing_ids)[:5])
        extra_examples = ", ".join(sorted(extra_ids)[:5])

        raise ValueError(
            f"{method} has a different query set than BM25 baseline: "
            f"missing={len(missing_ids)} [{missing_examples}], "
            f"extra={len(extra_ids)} [{extra_examples}]"
        )


def validate_query_type_coverage(method, metrics_by_id, query_types):
    """Raise when metric rows lack bridge/comparison query type metadata."""
    missing_type_ids = {
        query_id
        for query_id in metrics_by_id
        if query_id not in query_types
    }

    if missing_type_ids:
        missing_examples = ", ".join(sorted(missing_type_ids)[:5])

        raise ValueError(
            f"{method} has query IDs without supported query type metadata: "
            f"count={len(missing_type_ids)}, "
            f"examples=[{missing_examples}]"
        )


# 4. Aggregation

def summarize_method_by_type(metrics_by_id, query_types, method):
    """Aggregate one method's per-query metrics by HotpotQA query type."""
    rows_by_type = {query_type: [] for query_type in QUERY_TYPES}

    validate_query_type_coverage(
        method=method,
        metrics_by_id=metrics_by_id,
        query_types=query_types,
    )

    for query_id, metrics in metrics_by_id.items():
        rows_by_type[query_types[query_id]].append(metrics)

    summary_by_type = {}
    for query_type in QUERY_TYPES:
        type_rows = rows_by_type[query_type]

        if not type_rows:
            raise ValueError(
                f"{method} has no metric rows for query_type={query_type}"
            )

        summary_by_type[query_type] = {
            "num_queries": len(type_rows),
        }
        for metric_name in METRIC_NAMES:
            summary_by_type[query_type][metric_name] = (
                sum(row[metric_name] for row in type_rows) / len(type_rows)
            )

    return summary_by_type

def calculate_type_deltas(reference_by_type, comparison_by_type, metric_name):
    """Return query-type metric deltas between two method summaries."""
    return {
        query_type: (
            comparison_by_type[query_type][metric_name]
            - reference_by_type[query_type][metric_name]
        )
        for query_type in QUERY_TYPES
    }


# 5. Output

def build_output_rows(method_summaries):
    """Build output CSV rows and fill deltas against the typed BM25 baseline."""
    baseline_by_type = method_summaries["BM25 baseline"]
    output_rows = []

    for method, summary_by_type in method_summaries.items():
        deltas_by_metric = {
            metric_name: calculate_type_deltas(
                reference_by_type=baseline_by_type,
                comparison_by_type=summary_by_type,
                metric_name=metric_name,
            )
            for metric_name in DELTA_METRIC_NAMES
        }

        for query_type in QUERY_TYPES:
            summary = summary_by_type[query_type]
            output_row = {
                "method": method,
                "query_type": query_type,
                "num_queries": summary["num_queries"],
            }

            for metric_name in METRIC_NAMES:
                output_row[metric_name] = format_float(summary[metric_name])

            for metric_name in DELTA_METRIC_NAMES:
                output_row[f"delta_{metric_name}_vs_baseline"] = format_float(
                    deltas_by_metric[metric_name][query_type]
                )

            output_rows.append(output_row)

    return output_rows


# 6. main

def main():
    """Run the query-type aggregation and write the result CSV."""
    args = parse_args()
    query_types = load_query_types(args.queries)
    method_configs = get_method_configs(args)
    method_summaries = {}
    raw_metrics = {}

    for config in method_configs:
        raw_metrics[config.method] = load_per_query_metrics(
            config.per_query_path
        )

    validate_method_query_sets(raw_metrics)

    for config in method_configs:
        method_summaries[config.method] = summarize_method_by_type(
            metrics_by_id=raw_metrics[config.method],
            query_types=query_types,
            method=config.method,
        )

    output_rows = build_output_rows(method_summaries)
    write_csv(output_rows, args.output, OUTPUT_COLUMNS)
    print(f"Wrote query-type breakdown to {args.output}")


if __name__ == "__main__":
    main()
