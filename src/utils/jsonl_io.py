"""Small helpers for reading and writing project data files."""

import csv
import json
import pickle
from pathlib import Path

import networkx as nx


def load_jsonl(path):
    """Load a JSONL file into a list of dictionaries."""
    records = []

    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()

            if line:
                records.append(json.loads(line))

    return records


def write_jsonl(records, output_path):
    """Write records as one JSON object per line."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")


def write_csv(rows, output_path, fieldnames):
    """Write dictionaries to a CSV file using the given column order."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def load_graph(path):
    """Load a pickled NetworkX graph."""
    with Path(path).open("rb") as f:
        graph = pickle.load(f)

    if not isinstance(graph, nx.Graph):
        raise TypeError(f"Expected a NetworkX graph, got {type(graph)}")

    return graph


def save_graph(graph, output_path):
    """Save a NetworkX graph as a pickle file."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("wb") as f:
        pickle.dump(graph, f)
