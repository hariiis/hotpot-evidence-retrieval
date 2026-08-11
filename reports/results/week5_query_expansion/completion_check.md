# Week 5 Query Expansion Completion Check

## Scope

- Baseline run: `reports/results/week5_query_expansion/hop0_top0/`
- Expansion run: `reports/results/week5_query_expansion/hop1_top5/`
- Query file: `data/processed/hotpotqa/queries.jsonl`
- Week 2 BM25 reference: `data/results/bm25_top10.jsonl`

## Checks

1. Two runs have the same query count: Pass

`hop0_top0` has 100 `topk.jsonl` records, 100 `per_query.csv` rows, and 100 `expansion_traces.jsonl` records. 
`hop1_top5` has the same counts.

2. Every query has retrieval results: Pass

Both runs have 0 empty result lists, and every `topk.jsonl` record contains 10 retrieved passages.

3. Baseline matches Week 2 BM25: Pass

`hop0_top0/topk.jsonl` has 0 passage-ranking differences from `data/results/bm25_top10.jsonl`. 
 The maximum score difference is `1.42e-14`, which is only floating-point precision noise.

4. Expansion traces explain new concepts: Pass

`hop0_top0` has 0 changed queries and 0 expanded concept lists, as expected for `hop=0, top_n=0`. 
`hop1_top5` has 100 changed queries and 100 traces with `expanded_concepts`, so each expanded retrieval can be inspected through its trace.

5. Summary equals per-query simple average: Pass

For both runs, `summary.csv` matches the simple average of `per_query.csv` metrics up to CSV rounding. 
The largest observed difference is below `0.000001`.

## Metrics

| Run         | Recall@5 | Recall@10 | MRR@10   | nDCG@10  |
|---          |---:      |---:       | ---:     |---:      |
| `hop0_top0` | 0.546500 | 0.632333  | 0.755694 | 0.585073 |
| `hop1_top5` | 0.451500 | 0.598167  | 0.617524 | 0.506001 |

## Conclusion

The two-run completion check passes. The `hop=0, top_n=0` run is a valid BM25 baseline, and the `hop=1, top_n=5` run produces complete retrieval outputs plus interpretable expansion traces.
