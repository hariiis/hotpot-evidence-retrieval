"""Shared CSV schemas and row builders for retrieval experiment results."""


# Column order for the per-query metrics CSV.
PER_QUERY_COLUMNS = ["query_id", "Recall@5", "Recall@10", "RR@10", "nDCG@10"]

# Column order for the one-row summary CSV.
SUMMARY_COLUMNS = [
    "method",
    "model",
    "num_queries",
    "top_k",
    "Recall@5",
    "Recall@10",
    "MRR@10",
    "nDCG@10",
]


def build_per_query_metric_rows(per_query_metrics, query_ids):
    """
    Build per-query metric CSV rows in the original query order.
    """
    rows = []

    for query_id in query_ids:
        metrics = per_query_metrics.get(query_id, {})

        # Default to 0 if a query has no recorded metric entry.
        rows.append(
            {
                "query_id": query_id,
                "Recall@5": f"{metrics.get('recall_at_5', 0):.6f}",
                "Recall@10": f"{metrics.get('recall_at_10', 0):.6f}",
                "RR@10": f"{metrics.get('mrr_at_10', 0):.6f}",
                "nDCG@10": f"{metrics.get('ndcg_at_10', 0):.6f}",
            }
        )

    return rows


def build_summary_row(
    method,
    model,
    num_queries,
    top_k,
    recall_at_5,
    recall_at_10,
    mrr_at_10,
    ndcg_at_10,
):
    """Build the one-row summary baseline record."""
    return {
        "method": method,
        "model": model,
        "num_queries": num_queries,
        "top_k": top_k,
        "Recall@5": f"{recall_at_5:.6f}",
        "Recall@10": f"{recall_at_10:.6f}",
        "MRR@10": f"{mrr_at_10:.6f}",
        "nDCG@10": f"{ndcg_at_10:.6f}",
    }
