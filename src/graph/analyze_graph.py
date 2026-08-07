"""
Analyze the concept co-occurrence graph for density and noise checks.

Input:
- data/processed/concept_graph.pkl
- data/processed/concepts/passage_concepts.jsonl

Output:
- reports/results/week4_graph/week4_graph_stats.csv

The output CSV is a long table with summary graph metrics, top concepts by
degree, weighted degree, PageRank, and the per-passage concept-count
distribution.
"""

import argparse
import sys
from collections import Counter
from pathlib import Path

import networkx as nx


PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(PROJECT_ROOT / "src"))

from graph.build_graph import deduplicate_concepts
from utils.file_io import load_graph, load_jsonl, write_csv


GRAPH_STATS_COLUMNS = ["section", "rank", "metric", "concept", "value", "extra"]


def resolve_potential_legacy_path(path):
    """Resolve the older flat passage-concepts path to the current data path."""
    path = Path(path)

    if path.exists():
        return path

    fallback_path = PROJECT_ROOT / "data/processed/concepts" / path.name
    if path.name == "passage_concepts.jsonl" and fallback_path.exists():
        print(f"Input {path} not found; using {fallback_path}")
        return fallback_path

    return path


def connected_component_stats(graph):
    """Return component count and largest component size."""
    if graph.number_of_nodes() == 0:
        return 0, 0

    if graph.is_directed():
        components = nx.weakly_connected_components(graph)
    else:
        components = nx.connected_components(graph)

    component_sizes = [len(component) for component in components]
    return len(component_sizes), max(component_sizes)


def top_degree_concepts(graph, top_n):
    """Return concepts with the highest unweighted degree."""
    return sorted(graph.degree(), key=lambda item: (-item[1], item[0]))[:top_n]


def top_weighted_degree_concepts(graph, top_n):
    """Return concepts with the highest weighted degree."""
    weighted_degrees = graph.degree(weight="weight")
    return sorted(weighted_degrees, key=lambda item: (-item[1], item[0]))[:top_n]


def top_pagerank_concepts(graph, top_n):
    """Return concepts with the highest weighted PageRank score."""
    if graph.number_of_nodes() == 0:
        # Degree and weighted degree work on empty graphs, but PageRank needs nodes to score.
        return []

    pagerank_scores = nx.pagerank(graph, weight="weight")
    return sorted(pagerank_scores.items(), key=lambda item: (-item[1], item[0]))[:top_n]


def passage_concept_count_distribution(passage_records):
    """Return a concept-count histogram using deduplicated passage concepts."""
    counts = Counter()

    for record in passage_records:
        concept_count = len(deduplicate_concepts(record.get("concepts", [])))
        counts[concept_count] += 1

    return counts


def add_summary_rows(rows, graph, component_count, largest_component_size):
    """Append graph-level summary statistics to CSV rows."""
    num_nodes = graph.number_of_nodes()
    num_edges = graph.number_of_edges()
    average_degree = 0.0 if num_nodes == 0 else (2 * num_edges) / num_nodes

    summary_metrics = [
        ("num_nodes", num_nodes, "|V|"),
        ("num_edges", num_edges, "|E|"),
        ("average_degree", f"{average_degree:.6f}", "2*|E|/|V|"),
        ("connected_components", component_count, "weak components if graph is directed"),
        ("largest_component_size", largest_component_size, "nodes in largest component"),
    ]

    for metric, value, extra in summary_metrics:
        rows.append(
            {
                "section": "graph_summary",
                "rank": "",
                "metric": metric,
                "concept": "",
                "value": value,
                "extra": extra,
            }
        )


def add_top_concept_rows(rows, section, metric, concept_scores):
    """Append ranked concept-score rows to the output table."""
    for rank, (concept, value) in enumerate(concept_scores, start=1):
        if isinstance(value, float):
            value = f"{value:.6f}"

        rows.append(
            {
                "section": section,
                "rank": rank,
                "metric": metric,
                "concept": concept,
                "value": value,
                "extra": "",
            }
        )


def add_passage_distribution_rows(rows, distribution):
    """Append per-passage concept-count distribution rows."""
    total_passages = sum(distribution.values())

    for concept_count, passage_count in sorted(distribution.items()):
        fraction = 0.0 if total_passages == 0 else passage_count / total_passages
        rows.append(
            {
                "section": "passage_concept_count_distribution",
                "rank": "",
                "metric": "num_passages",
                "concept": "",
                "value": passage_count,
                "extra": f"concept_count={concept_count}; fraction={fraction:.6f}",
            }
        )


def build_graph_stats_rows(graph, passage_records, top_n):
    """Build all graph analysis rows for CSV output."""
    rows = []
    component_count, largest_component_size = connected_component_stats(graph)

    add_summary_rows(rows, graph, component_count, largest_component_size)
    add_top_concept_rows(
        rows,
        section="top_degree_concepts",
        metric="degree",
        concept_scores=top_degree_concepts(graph, top_n),
    )
    add_top_concept_rows(
        rows,
        section="top_weighted_degree_concepts",
        metric="weighted_degree",
        concept_scores=top_weighted_degree_concepts(graph, top_n),
    )
    add_top_concept_rows(
        rows,
        section="top_pagerank_concepts",
        metric="pagerank",
        concept_scores=top_pagerank_concepts(graph, top_n),
    )
    add_passage_distribution_rows(
        rows,
        passage_concept_count_distribution(passage_records),
    )

    return rows


def parse_args():
    """Parse command-line arguments for graph analysis paths."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--graph",
        default="data/processed/concept_graph.pkl",
        help="Input pickle path for the NetworkX concept graph.",
    )
    parser.add_argument(
        "--passage_concepts",
        default="data/processed/concepts/passage_concepts.jsonl",
        help="Input JSONL with passage_id and concepts fields.",
    )
    parser.add_argument(
        "--output",
        default="reports/results/week4_graph/week4_graph_stats.csv",
        help="Output CSV path for graph statistics.",
    )
    parser.add_argument(
        "--top_n",
        type=int,
        default=20,
        help="Number of top concepts to report for ranked graph metrics.",
    )

    return parser.parse_args()


def main():
    """Load graph inputs, compute graph statistics, and write the CSV output."""
    args = parse_args()

    graph = load_graph(args.graph)
    passage_concepts_path = resolve_potential_legacy_path(args.passage_concepts)
    passage_records = load_jsonl(passage_concepts_path)
    rows = build_graph_stats_rows(graph, passage_records, args.top_n)

    write_csv(rows, args.output, fieldnames=GRAPH_STATS_COLUMNS)

    num_nodes = graph.number_of_nodes()
    num_edges = graph.number_of_edges()
    average_degree = 0.0 if num_nodes == 0 else (2 * num_edges) / num_nodes
    component_count, largest_component_size = connected_component_stats(graph)

    print(f"Wrote graph statistics to {args.output}")
    print(f"num_nodes: {num_nodes}")
    print(f"num_edges: {num_edges}")
    print(f"average_degree: {average_degree:.6f}")
    print(f"connected_components: {component_count}")
    print(f"largest_component_size: {largest_component_size}")


if __name__ == "__main__":
    main()
