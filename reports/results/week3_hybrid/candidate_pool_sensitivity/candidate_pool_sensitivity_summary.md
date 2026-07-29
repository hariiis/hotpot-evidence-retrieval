# Candidate Pool Sensitivity Test

This sensitivity test fixes the best Hybrid interpolation weight from the main
alpha experiment, `alpha = 0.50`, and varies only the candidate pool size. BM25
and Dense use the same `candidate_k`, and the final Hybrid output is still
limited to `top_k = 10`.

| alpha | candidate_k | Recall@5 | Recall@10 | MRR@10   | nDCG@10  |
|---:   |---:         |---:      |---:       |---:      |---:      |
| 0.50  | 50          | 0.574500 | 0.714000  | 0.786187 | 0.636965 |
| 0.50  | 100         | 0.572833 | 0.722333  | 0.787853 | 0.641097 |
| 0.50  | 200         | 0.572833 | 0.722333  | 0.787536 | 0.640701 |

The results show that increasing `candidate_k` from 50 to 100 improves
Recall@10 from 0.714000 to 0.722333, while MRR@10 and nDCG@10 also improve
slightly. Increasing `candidate_k` further from 100 to 200 does not improve
Recall@10 and gives nearly identical ranking metrics. 

The results suggest Hybrid retrieval is only mildly sensitive to `candidate_k` 
and `candidate_k=100` is a reasonable default for the current setting: it gives
Hybrid enough reranking space without adding unnecessary candidate expansion.
