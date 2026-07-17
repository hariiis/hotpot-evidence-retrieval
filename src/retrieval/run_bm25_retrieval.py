import argparse
import json
from pathlib import Path

from bm25 import BM25Retriever, load_passages


def load_queries(queries_path):
    queries = []

    with open(queries_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                queries.append(json.loads(line))

    return queries


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--queries", required=True)
    parser.add_argument("--passages", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--top_k", type=int, default=10)
    args = parser.parse_args()

    passages = load_passages(args.passages)
    retriever = BM25Retriever(passages)

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)

    with open(args.output, "w", encoding="utf-8") as f:
        for query_record in load_queries(args.queries):
            results = retriever.retrieve(
                query_record["query"],
                top_k=args.top_k,
            )

            output_record = {
                "query_id": query_record["query_id"],
                "results": results,
            }
            f.write(json.dumps(output_record) + "\n")


if __name__ == "__main__":
    main()
