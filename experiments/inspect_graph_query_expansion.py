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
from collections import defaultdict
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


def deduplicate_concepts(concepts):
    """Remove empty and repeated concepts while preserving order."""
    seen = set()
    deduplicated = []

    for concept in concepts:
        if not concept or concept in seen:
            continue

        seen.add(concept)
        deduplicated.append(concept)

    return deduplicated


def build_passage_concept_map(passage_concept_records):
    """Return a passage_id -> deduplicated concepts mapping."""
    return {
        record["passage_id"]: deduplicate_concepts(record.get("concepts", []))
        for record in passage_concept_records
    }


def build_qrels_map(qrel_records):
    """Return a query_id -> positive gold passage_id list mapping."""
    qrels = defaultdict(list)
    seen = defaultdict(set)

    for record in qrel_records:
        if record.get("relevance", 1) <= 0:
            continue

        query_id = record["query_id"]
        passage_id = record["passage_id"]

        if passage_id in seen[query_id]:
            continue

        seen[query_id].add(passage_id)
        qrels[query_id].append(passage_id)

    return dict(qrels)


def collect_gold_concepts(gold_passage_ids, passage_concepts):
    """Collect deduplicated concepts from a query's gold passages."""
    gold_concepts = []

    for passage_id in gold_passage_ids:
        gold_concepts.extend(passage_concepts.get(passage_id, []))

    return deduplicate_concepts(gold_concepts)


def find_expanded_gold_overlap(expanded_concepts, gold_concepts):
    """Return only expanded concepts that also appear in gold concepts."""
    gold_concept_set = set(gold_concepts)

    return [
        item["concept"]
        for item in expanded_concepts
        if item["concept"] in gold_concept_set
    ]


def find_query_gold_overlap(query_concepts, gold_concepts):
    """Return query concepts that also appear in gold concepts."""
    gold_concept_set = set(gold_concepts)

    return [
        concept
        for concept in query_concepts
        if concept in gold_concept_set
    ]


def build_expansion_traces(
    queries,
    query_concepts,
    graph,
    limit,
    hop,
    top_n,
    qrels,
    passage_concepts,
):
    """Run graph query expansion for the first limit queries."""
    traces = []

    for query_record in queries[:limit]:
        query_id = query_record["query_id"]
        concepts = query_concepts.get(query_id, [])
        gold_passage_ids = qrels.get(query_id, [])
        gold_concepts = collect_gold_concepts(gold_passage_ids, passage_concepts)

        expansion_trace = expand_query(
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
            "original_query": expansion_trace["original_query"],
            "gold_passage_ids": gold_passage_ids,
            "answer": query_record.get("answer"),
            "query_concepts": expansion_trace["query_concepts"],
            "matched_graph_nodes": expansion_trace["matched_graph_nodes"],
            "unmatched_query_concepts": expansion_trace[
                "unmatched_query_concepts"
            ],
            "expanded_concepts": expansion_trace["expanded_concepts"],
            "expanded_query": expansion_trace["expanded_query"],
            "gold_concepts": gold_concepts,
            "query_gold_overlap": find_query_gold_overlap(
                expansion_trace["query_concepts"],
                gold_concepts,
            ),
            "expanded_gold_overlap": find_expanded_gold_overlap(
                expansion_trace["expanded_concepts"],
                gold_concepts,
            ),
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


def write_markdown_traces(traces, output_path):
    """Write pretty-printed traces to a Markdown file for manual review."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    lines = ["# Query Expansion Trace", ""]

    for index, trace in enumerate(traces, start=1):
        query_id = trace.get("query_id", f"record_{index}")
        lines.extend(
            [
                f"## {index}. {query_id}",
                "",
                "```json",
                json.dumps(trace, ensure_ascii=False, indent=2),
                "```",
                "",
            ]
        )

    output_path.write_text("\n".join(lines), encoding="utf-8")


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
        "--passage_concepts",
        default="data/processed/concepts/passage_concepts.jsonl",
        help="Input JSONL file with normalized passage concepts.",
    )
    parser.add_argument(
        "--qrels",
        default="data/processed/hotpotqa/qrels.jsonl",
        help="Input JSONL file with positive gold passage labels.",
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
    parser.add_argument(
        "--markdown_output",
        default=None,
        help="Optional Markdown output path for pretty-printed manual traces.",
    )

    return parser.parse_args()


def main():
    """Load inputs, build expansion traces, print them, and optionally save."""
    args = parse_args()

    queries = load_jsonl(args.queries)
    query_concept_records = load_jsonl(args.query_concepts)
    query_concepts = build_query_concept_map(query_concept_records)
    passage_concepts = build_passage_concept_map(load_jsonl(args.passage_concepts))
    qrels = build_qrels_map(load_jsonl(args.qrels))
    graph = load_graph(args.graph)

    traces = build_expansion_traces(
        queries=queries,
        query_concepts=query_concepts,
        graph=graph,
        limit=args.limit,
        hop=args.hop,
        top_n=args.top_n,
        qrels=qrels,
        passage_concepts=passage_concepts,
    )

    print_traces(traces)

    if args.output:
        write_jsonl(traces, args.output)
        print()
        print(f"Wrote expansion traces to {args.output}")

    if args.markdown_output:
        write_markdown_traces(traces, args.markdown_output)
        print()
        print(f"Wrote readable expansion traces to {args.markdown_output}")


if __name__ == "__main__":
    main()
