# Week 5 Query Expansion Completion Check

## Scope

- Baseline run: `reports/results/week5_query_expansion/hop0_top0/`
- Expansion run: `reports/results/week5_query_expansion/hop1_top5/`
- Specificity baseline-label run: `reports/results/week5_query_expansion/hop0_top0_edge_weight_log_passage_count/`
- Specificity expansion run: `reports/results/week5_query_expansion/hop1_top5_edge_weight_log_passage_count/`
- Query file: `data/processed/hotpotqa/queries.jsonl`
- Week 2 BM25 reference: `data/results/bm25_top10.jsonl`

## Checks

1. Runs have the same query count: Pass

`hop0_top0` has 100 `topk.jsonl` records, 100 `per_query.csv` rows, and 100 `expansion_traces.jsonl` records. 
`hop1_top5`, `hop0_top0_edge_weight_log_passage_count`, and `hop1_top5_edge_weight_log_passage_count` have the same counts.

2. Every query has retrieval results: Pass

All four runs have 0 empty result lists, and every `topk.jsonl` record contains 10 retrieved passages.

3. Baseline matches Week 2 BM25: Pass

`hop0_top0/topk.jsonl` has 0 passage-ranking differences from `data/results/bm25_top10.jsonl`. 
 The maximum score difference is `1.42e-14`, which is only floating-point precision noise.

4. Expansion traces explain new concepts: Pass

`hop0_top0` has 0 changed queries and 0 expanded concept lists, as expected for `hop=0, top_n=0`. 
`hop1_top5` and `hop1_top5_edge_weight_log_passage_count` each have 100 changed queries and 100 traces with `expanded_concepts`, so each expanded retrieval can be inspected through its trace.

5. Summary equals per-query simple average: Pass

For all four runs, `summary.csv` matches the simple average of `per_query.csv` metrics up to CSV rounding. 
The largest observed difference is below `0.000001`.

6. Specificity strategy changes only candidate ranking: Pass

The `edge_weight_log_passage_count` strategy uses only graph-side candidate statistics:

```text
score = edge_weight_score / log(2 + candidate_passage_count)
```

This strategy uses the same candidate pool as `edge_weight`; it only changes the ranking score before the final top candidates are selected. K/U/N labels, gold concepts, answers, and question type fields remain analysis-only.

7. `hop=0, top_n=0` is strategy-invariant: Pass

`hop0_top0` and `hop0_top0_edge_weight_log_passage_count` have identical metrics. This is expected because no expansion candidates are collected when `hop=0` or `top_n=0`; the BM25 input remains the original query.

## Metrics

| Run                                             | Strategy                            | Recall@5 | Recall@10 | MRR@10   | nDCG@10  |
|---                                              |---                                  |---:      |---:       | ---:     |---:      |
| `hop0_top0`                                     | `edge_weight`                       | 0.546500 | 0.632333  | 0.755694 | 0.585073 |
| `hop0_top0_edge_weight_log_passage_count`       | `edge_weight_log_passage_count`     | 0.546500 | 0.632333  | 0.755694 | 0.585073 |
| `hop1_top5`                                     | `edge_weight`                       | 0.451500 | 0.598167  | 0.617524 | 0.506001 |
| `hop1_top5_edge_weight_log_passage_count`       | `edge_weight_log_passage_count`     | 0.472333 | 0.617333  | 0.619718 | 0.510217 |

## Specificity Comparison

Compared with the original `hop1_top5` edge-weight expansion, `edge_weight_log_passage_count` improves all four summary metrics on this 100-query run:

| Comparison                                           | Recall@5  | Recall@10 | MRR@10    | nDCG@10   |
|---                                                   |---:       |---:       |---:       |---:       |
| Specificity minus edge-weight, `hop=1, top_n=5`      | +0.020833 | +0.019166 | +0.002194 | +0.004216 |

This supports keeping `edge_weight` as the raw baseline and treating `edge_weight_log_passage_count` as a single-variable specificity ablation. The result should still be interpreted through full retrieval metrics, not only trace-level concept quality.

## Conclusion

The completion check passes. The `hop=0, top_n=0` runs are valid BM25 baselines, and the `hop=1, top_n=5` runs produce complete retrieval outputs plus interpretable expansion traces. The specificity strategy gives a modest metric improvement over raw edge-weight expansion while preserving the experiment rule that only one ranking variable changes.
