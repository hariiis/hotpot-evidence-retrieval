"""
Compute concept coverage diagnostics for Week 5 query expansion planning.

Input:
- data/processed/concepts/query_concepts.jsonl
- data/processed/concepts/passage_concepts.jsonl
- data/processed/hotpotqa/qrels.jsonl
- data/processed/concept_graph.pkl

Output:
- reports/results/week4_coverage_stats.csv

One-hop recall is computed with reachable concepts defined as:
query concepts that are graph nodes union their graph neighbors. Therefore,
one-hop recall includes the query concept itself when it is present in the
concept graph.
"""

import argparse
import sys
from collections import defaultdict
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(PROJECT_ROOT / "src"))

from graph.build_graph import deduplicate_concepts
from utils.jsonl_io import load_graph, load_jsonl, write_csv


COVERAGE_COLUMNS = [
    "query_id",
    "num_query_concepts",
    "num_gold_concepts",
    "query_coverage",
    "gold_coverage",
    "direct_overlap",
    "one_hop_recall",
]


def safe_ratio(numerator, denominator):
    """Return numerator / denominator, or 0.0 for an empty denominator."""
    if denominator == 0:
        return 0.0

    return numerator / denominator


def concepts_by_id(records, id_field):
    """Return an id -> deduplicated concept set mapping."""
    mapping = {}

    for record in records:
        concepts = deduplicate_concepts(record.get("concepts", []))
        mapping[record[id_field]] = set(concepts)

    return mapping


def load_qrels(qrels_path):
    """Load positive qrels as a query_id -> gold passage_id set mapping."""
    qrels = defaultdict(set)

    for record in load_jsonl(qrels_path):
        relevance = record.get("relevance", 1)

        if relevance > 0:
            qrels[record["query_id"]].add(record["passage_id"])

    return dict(qrels)


def build_query_row(query_id, query_concepts, gold_concepts, graph):
    """Compute all coverage metrics for one query."""
    graph_nodes = set(graph.nodes)
    mapped_query = query_concepts & graph_nodes
    mapped_gold = gold_concepts & graph_nodes
    direct_overlap = query_concepts & gold_concepts
    reachable = set(mapped_query)

    # Including mapped_query makes this QueryConcepts union Neighbors(QueryConcepts).
    for concept in mapped_query:
        reachable.update(graph.neighbors(concept))

    return {
        "query_id": query_id,
        "num_query_concepts": len(query_concepts),
        "num_gold_concepts": len(gold_concepts),
        "query_coverage": safe_ratio(len(mapped_query), len(query_concepts)),
        "gold_coverage": safe_ratio(len(mapped_gold), len(gold_concepts)),
        "direct_overlap": safe_ratio(len(direct_overlap), len(gold_concepts)),
        "one_hop_recall": safe_ratio(
            len(reachable & gold_concepts),
            len(gold_concepts),
        ),
    }


def build_average_row(rows):
    """Build the final AVERAGE row across per-query diagnostics."""
    num_rows = len(rows)

    return {
        "query_id": "AVERAGE",
        "num_query_concepts": sum(row["num_query_concepts"] for row in rows)
        / num_rows,
        "num_gold_concepts": sum(row["num_gold_concepts"] for row in rows)
        / num_rows,
        "query_coverage": sum(row["query_coverage"] for row in rows) / num_rows,
        "gold_coverage": sum(row["gold_coverage"] for row in rows) / num_rows,
        "direct_overlap": sum(row["direct_overlap"] for row in rows) / num_rows,
        "one_hop_recall": sum(row["one_hop_recall"] for row in rows) / num_rows,
    }


def build_coverage_rows(query_concepts, passage_concepts, qrels, graph):
    """Build one coverage row per query plus a final AVERAGE row."""
    rows = []

    for query_id in sorted(query_concepts):
        gold_concepts = set()

        for passage_id in qrels.get(query_id, set()):
            gold_concepts.update(passage_concepts.get(passage_id, set()))

        row = build_query_row(query_id, query_concepts[query_id], gold_concepts, graph)
        rows.append(row)

    if rows:
        rows.append(build_average_row(rows))

    for row in rows:
        for field in COVERAGE_COLUMNS:
            if isinstance(row[field], float):
                row[field] = f"{row[field]:.6f}"

    return rows


def parse_args():
    """Parse coverage diagnostic input and output paths."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--query_concepts",
        default="data/processed/concepts/query_concepts.jsonl",
        help="Input JSONL with query_id and concepts fields.",
    )
    parser.add_argument(
        "--passage_concepts",
        default="data/processed/concepts/passage_concepts.jsonl",
        help="Input JSONL with passage_id and concepts fields.",
    )
    parser.add_argument(
        "--qrels",
        default="data/processed/hotpotqa/qrels.jsonl",
        help="Input JSONL with query_id, passage_id, and relevance fields.",
    )
    parser.add_argument(
        "--graph",
        default="data/processed/concept_graph.pkl",
        help="Input pickle path for the NetworkX concept graph.",
    )
    parser.add_argument(
        "--output",
        default="reports/results/week4_coverage_stats.csv",
        help="Output CSV path for coverage diagnostics.",
    )

    return parser.parse_args()


def main():
    """Load inputs, compute coverage diagnostics, and write the CSV output."""
    args = parse_args()

    graph = load_graph(args.graph)
    query_concepts = concepts_by_id(load_jsonl(args.query_concepts), "query_id")
    passage_concepts = concepts_by_id(load_jsonl(args.passage_concepts), "passage_id")
    qrels = load_qrels(args.qrels)

    rows = build_coverage_rows(query_concepts, passage_concepts, qrels, graph)
    write_csv(rows, args.output, fieldnames=COVERAGE_COLUMNS)

    average_row = rows[-1] if rows else {}

    print(f"Wrote coverage diagnostics to {args.output}")
    print(f"num_queries: {len(query_concepts)}")
    print("one_hop_recall_includes_query_concepts: true")

    if average_row:
        print(f"average_query_coverage: {average_row['query_coverage']}")
        print(f"average_gold_coverage: {average_row['gold_coverage']}")
        print(f"average_direct_overlap: {average_row['direct_overlap']}")
        print(f"average_one_hop_recall: {average_row['one_hop_recall']}")


if __name__ == "__main__":
    main()
