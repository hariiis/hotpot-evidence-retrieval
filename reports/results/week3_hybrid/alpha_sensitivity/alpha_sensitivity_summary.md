# Hybrid Alpha Experiment Summary

This experiment fixes the Hybrid candidate pool size at `candidate_k = 100`
and varies only the interpolation weight `alpha`. The final retrieval output is
still limited to `top_k = 10`.

In the Hybrid score, `alpha` controls the BM25 weight:

`HybridScore = alpha * normalized(BM25Score) + (1 - alpha) * normalized(DenseScore)`

Therefore, lower `alpha` gives more weight to Dense retrieval, while higher
`alpha` gives more weight to BM25 retrieval.

| alpha | candidate_k | Recall@5 | Recall@10 | MRR@10   | nDCG@10  |
|---:   |---:         |---:      |---:       |---:      |---:      |
| 0.25  | 100         | 0.593667 | 0.701833  | 0.753718 | 0.616496 |
| 0.50  | 100         | 0.572833 | 0.722333  | 0.787853 | 0.641097 |
| 0.75  | 100         | 0.551500 | 0.695667  | 0.773456 | 0.626500 |

The best overall setting is `alpha = 0.50`. It achieves the highest Recall@10,
MRR@10, and nDCG@10 among the tested alpha values. Although `alpha = 0.25`
has the highest Recall@5, it performs worse on Recall@10 and ranking-sensitive
metrics. This suggests that a balanced BM25-Dense weighting works best for the
current retrieval setup.
