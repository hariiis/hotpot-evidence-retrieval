import argparse
import csv
import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT / "src" / "retrieval"))
sys.path.append(str(PROJECT_ROOT / "src" / "eval"))

from bm25 import BM25Retriever, load_passages
from metrics import load_qrels, mrr_at_k, ndcg_at_k, recall_at_k


CSV_COLUMNS = [
    "setting",
    "num_queries",
    "num_passages",
    "corpus_mode",
    "passage_granularity",
    "top_k",
    "k1",
    "b",
    "Recall@5",
    "Recall@10",
    "MRR@10",
    "nDCG@10",
]


def load_queries(queries_path):
    queries = []

    with open(queries_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()

            if line:
                queries.append(json.loads(line))

    return queries


def run_retrieval(queries, passages, top_k, k1, b):
    retriever = BM25Retriever(passages, k1=k1, b=b)
    results = {}

    for query_record in queries:
        query_id = query_record["query_id"]
        query = query_record["query"]
        results[query_id] = retriever.retrieve(query, top_k=top_k)

    return results


def write_summary_csv(row, output_path):
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        writer.writerow(row)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--queries", required=True)
    parser.add_argument("--passages", required=True)
    parser.add_argument("--qrels", required=True)
    parser.add_argument("--top_k", type=int, default=10)
    parser.add_argument("--output", required=True)
    parser.add_argument("--setting", default="bm25_default")
    parser.add_argument("--corpus_mode", default="pooled")
    parser.add_argument("--passage_granularity", default="sentence")
    parser.add_argument("--k1", type=float, default=1.5)
    parser.add_argument("--b", type=float, default=0.75)
    args = parser.parse_args()

    queries = load_queries(args.queries)
    passages = load_passages(args.passages)
    qrels = load_qrels(args.qrels)
    results = run_retrieval(
        queries=queries,
        passages=passages,
        top_k=args.top_k,
        k1=args.k1,
        b=args.b,
    )

    recall_at_5 = recall_at_k(results, qrels, 5)
    recall_at_10 = recall_at_k(results, qrels, 10)
    mrr_at_10 = mrr_at_k(results, qrels, 10)
    ndcg_at_10 = ndcg_at_k(results, qrels, 10)

    row = {
        "setting": args.setting,
        "num_queries": len(queries),
        "num_passages": len(passages),
        "corpus_mode": args.corpus_mode,
        "passage_granularity": args.passage_granularity,
        "top_k": args.top_k,
        "k1": args.k1,
        "b": args.b,
        "Recall@5": f"{recall_at_5:.6f}",
        "Recall@10": f"{recall_at_10:.6f}",
        "MRR@10": f"{mrr_at_10:.6f}",
        "nDCG@10": f"{ndcg_at_10:.6f}",
    }

    write_summary_csv(row, args.output)

    print(f"Wrote BM25 summary to {args.output}")
    print(f"Recall@5: {recall_at_5:.6f}")
    print(f"Recall@10: {recall_at_10:.6f}")
    print(f"MRR@10: {mrr_at_10:.6f}")
    print(f"nDCG@10: {ndcg_at_10:.6f}")


if __name__ == "__main__":
    main()
