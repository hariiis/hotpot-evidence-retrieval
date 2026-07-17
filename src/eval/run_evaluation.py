import argparse

from metrics import (
    load_qrels,
    load_results,
    mrr_at_k,
    ndcg_at_k,
    recall_at_k,
    write_per_query_metrics,
)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", required=True)
    parser.add_argument("--qrels", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--top_k", type=int, default=10)
    args = parser.parse_args()

    results = load_results(args.results)
    qrels = load_qrels(args.qrels)
    per_query_metrics = {}

    recall = recall_at_k(
        results, qrels, args.top_k, per_query_metrics
    )
    mrr = mrr_at_k(
        results, qrels, args.top_k, per_query_metrics
    )
    ndcg = ndcg_at_k(
        results, qrels, args.top_k, per_query_metrics
    )

    print(f"Recall@{args.top_k}: {recall:.4f}")
    print(f"MRR@{args.top_k}: {mrr:.4f}")
    print(f"nDCG@{args.top_k}: {ndcg:.4f}")

    write_per_query_metrics(per_query_metrics, args.output)


if __name__ == "__main__":
    main()
