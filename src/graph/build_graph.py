"""
Build a concept co-occurrence graph from passage-level concepts.

Input:
- data/processed/concepts/passage_concepts.jsonl
Output:
- data/processed/concept_graph.pkl

It builds an undirected weighted NetworkX graph:
- nodes are normalized concepts
- edges connect concepts that appear in the same passage
- edge weight is the number of co-occurring passages
- node passage_count is the number of passages containing that concept

Only passage concepts are used to build the graph. Query concepts are excluded.
Edges mean co-occurrence only, not strict semantic relations.
"""

import argparse
import pickle
import sys
from itertools import combinations
from pathlib import Path

import networkx as nx


PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(PROJECT_ROOT / "src"))

from utils.jsonl_io import load_jsonl


def deduplicate_concepts(concepts):
    """Remove duplicate concepts inside one passage."""
    seen = set()
    unique_concepts = []

    for concept in concepts:
        # Skip empty concepts and repeated concepts from the same passage.
        if not concept or concept in seen:
            continue

        seen.add(concept)
        unique_concepts.append(concept)

    return unique_concepts


def build_concept_graph(records):
    """Build an undirected weighted concept co-occurrence graph."""
    graph = nx.Graph()

    for record in records:
        concepts = deduplicate_concepts(record.get("concepts", []))

        for concept in concepts:
            if not graph.has_node(concept):
                graph.add_node(concept, passage_count=0)

            graph.nodes[concept]["passage_count"] += 1

        # Connect every pair of concepts that co-occur in this passage.
        for source, target in combinations(concepts, 2):
            # Keep the no-self-loop rule explicit.
            if source == target:
                continue

            if graph.has_edge(source, target):
                graph[source][target]["weight"] += 1
            else:
                graph.add_edge(source, target, weight=1)

    graph.graph["description"] = (
        "Undirected concept co-occurrence graph built from passage concepts only. "
        "Edges indicate same-passage co-occurrence, not strict semantic relations."
    )

    return graph


def save_graph(graph, output_path):
    """Save the NetworkX graph as a pickle file."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("wb") as f:
        pickle.dump(graph, f)


def parse_args():
    """Parse command-line arguments for graph build paths."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--passage_concepts",
        default="data/processed/concepts/passage_concepts.jsonl",
        help="Input JSONL with passage_id and concepts fields.",
    )
    parser.add_argument(
        "--output",
        default="data/processed/concept_graph.pkl",
        help="Output pickle path for the NetworkX graph.",
    )

    return parser.parse_args()


def main():
    """Load passage concepts, build the graph, and write the output."""
    args = parse_args()

    # Query concepts are intentionally not loaded for graph construction.
    passage_concepts = load_jsonl(args.passage_concepts)
    graph = build_concept_graph(passage_concepts)

    save_graph(graph, args.output)

    print(f"Wrote concept graph to {args.output}")
    print(f"num_passages: {len(passage_concepts)}")
    print(f"num_nodes: {graph.number_of_nodes()}")
    print(f"num_edges: {graph.number_of_edges()}")


if __name__ == "__main__":
    main()
