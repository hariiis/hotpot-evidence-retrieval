"""
Print graph query expansion traces for manual inspection.

This script loads real HotpotQA queries, their Week 4 normalized query concepts,
and the Week 4 concept graph. It then runs graph-based query expansion for a
small number of queries and prints the full trace needed to judge whether the
expanded concepts are reasonable.
"""

import argparse
import json
import sys
from pathlib import Path


# Add project modules to the import path when this script is run directly.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT / "src"))
sys.path.append(str(PROJECT_ROOT / "src" / "retrieval"))

from graph_query_expansion import expand_query
from utils.file_io import load_graph, load_jsonl, write_jsonl


def build_query_concept_map(query_concept_records):
    """Return a query_id -> normalized concepts mapping."""
    return {
        record["query_id"]: record.get("concepts", [])
        for record in query_concept_records
    }


def build_expansion_traces(queries, query_concepts, graph, limit, hop, top_n):
    """Run graph query expansion for the first limit queries."""
    traces = []

    for query_record in queries[:limit]:
        query_id = query_record["query_id"]
        concepts = query_concepts.get(query_id, [])

        trace = expand_query(
            query=query_record["query"],
            query_concepts=concepts,
            graph=graph,
            hop=hop,
            top_n=top_n,
        )

        # Keep query metadata next to the expansion trace for manual review.
        trace = {
            "query_id": query_id,
            "type": query_record.get("type"),
            "answer": query_record.get("answer"),
            **trace,
        }
        traces.append(trace)

    return traces


def print_traces(traces):
    """Print one complete JSON trace per query."""
    for index, trace in enumerate(traces, start=1):
        if index > 1:
            print()

        print("=" * 80)
        print(f"{index}. {trace['query_id']}")
        print("=" * 80)
        print(json.dumps(trace, ensure_ascii=False, indent=2))


def parse_args():
    """Parse command-line options for query expansion inspection."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--queries",
        default="data/processed/hotpotqa/queries.jsonl",
        help="Input JSONL file with processed query records.",
    )
    parser.add_argument(
        "--query_concepts",
        default="data/processed/concepts/query_concepts.jsonl",
        help="Input JSONL file with normalized query concepts.",
    )
    parser.add_argument(
        "--graph",
        default="data/processed/concept_graph.pkl",
        help="Input pickle file with the NetworkX concept graph.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Number of queries to inspect from the start of the query file.",
    )
    parser.add_argument(
        "--hop",
        type=int,
        default=1,
        help="Expansion depth passed to expand_query.",
    )
    parser.add_argument(
        "--top_n",
        type=int,
        default=5,
        help="Maximum number of expansion concepts per query.",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Optional JSONL output path for saved expansion traces.",
    )

    return parser.parse_args()


def main():
    """Load inputs, build expansion traces, print them, and optionally save."""
    args = parse_args()

    queries = load_jsonl(args.queries)
    query_concept_records = load_jsonl(args.query_concepts)
    query_concepts = build_query_concept_map(query_concept_records)
    graph = load_graph(args.graph)

    traces = build_expansion_traces(
        queries=queries,
        query_concepts=query_concepts,
        graph=graph,
        limit=args.limit,
        hop=args.hop,
        top_n=args.top_n,
    )

    print_traces(traces)

    if args.output:
        write_jsonl(traces, args.output)
        print()
        print(f"Wrote expansion traces to {args.output}")


if __name__ == "__main__":
    main()
