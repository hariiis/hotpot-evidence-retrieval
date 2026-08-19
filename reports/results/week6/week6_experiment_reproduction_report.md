# Week 6 实验设置与复现检查

## Compared Retrieval Configurations

| Role                  | Method                               | Strategy                        | Hop | top_n | 
| ---                   | ---                                  | ---:                            | ---:| ---:  | 
| Baseline              | BM25 only                            | N/A                             | N/A | N/A   | 
| Sanity check          | BM25 only via query-expansion script | `edge_weight_log_passage_count` | 0   | 0     |
| Main expansion        | Query expansion + BM25               | `edge_weight_log_passage_count` | 1   | 5     |
| Supplementary control | Query expansion + BM25               | `edge_weight_log_passage_count` | 1   | 3     |

主配置使用 `hop=1`, `top_n=5`，因为它在 Week 5 参数比较中取得了 `edge_weight_log_passage_count` strategy 下最高的 Recall@10，同时仍然保持保守的 1-hop expansion。Supplementary control 使用 `hop=1`, `top_n=3`，因为它在 MRR@10 和 nDCG@10 上比主配置更稳定，可以作为 rank-sensitive metrics 的补充对照。

## Fixed Experimental Conditions

1. Queries：`data/processed/hotpotqa/queries.jsonl`，100 queries。
2. Corpus：`data/processed/hotpotqa/passages.jsonl`，100 个 HotpotQA examples 的 pooled context passage pool，共 4085 个 sentence-level passages。
3. Passage 粒度：sentence-level passages；`passage_id` 使用 `title::sentence_index` 格式。
4. qrels：`data/processed/hotpotqa/qrels.jsonl`，243 条 positive qrels。
5. BM25 参数：`k1=1.5`, `b=0.75`。
6. Retrieval top_k：10。
7. Graph 文件：`data/processed/concept_graph.pkl`。
8. Query concept 文件：`data/processed/concepts/query_concepts.jsonl`。
9. Passage concept 文件：`data/processed/concepts/passage_concepts.jsonl`。
10. Expansion strategy：`edge_weight_log_passage_count`。
11. 比较的 expansion 配置：main 为 `hop=1`, `top_n=5`；supplementary control 为 `hop=1`, `top_n=3`。
12. Filtering rules：graph matching 时对 query concepts 去重；unmatched query concepts 不参与 expansion；expansion candidates 排除原始 matched query nodes；`DEFAULT_BLOCKED_CONCEPTS` 为空；暂时没有额外手动 blocklist；最终只追加排名最高的 `top_n` candidates。

## Reproduced Results

| Setting                                              | Recall@5 | Recall@10 | MRR@10   | nDCG@10  | Match                                   |
|---                                                   |---:      |---:       |---:      |---:      |---                                      |
| BM25 only                                            | 0.546500 | 0.632333  | 0.755694 | 0.585073 | 与 Week 2 BM25 summary 完全一致          |
| BM25 only via query-expansion script: hop=0, top_n=0 | 0.546500 | 0.632333  | 0.755694 | 0.585073 | 与 Week 5 完全一致，与 BM25 only 完全一致 |
| Main expansion: hop=1, top_n=5                       | 0.472333 | 0.617333  | 0.619718 | 0.510217 | 与 Week 5 完全一致                       |
| Supplement: hop=1, top_n=3                           | 0.469833 | 0.609833  | 0.650345 | 0.521765 | 与 Week 5 完全一致                       |

机器可读的 reproduction summary 保存在 `reports/results/week6/reproduction_summary.csv`。

## Additional Consistency Checks

1. `hop=0, top_n=0`、`hop=1, top_n=5` 和 `hop=1, top_n=3` 的 `per_query.csv` 与 Week 5 对应结果完全一致；三个配置的 `expansion_traces.jsonl` 也与 Week 5 完全一致。
2. 三个 query-expansion script runs 的 top-10 ranking 均与 Week 5 保持相同的 query ids、expanded queries 和 passage ranking order；raw score 仅存在 `1e-14` 量级浮点差异，不影响 ranking 或 metrics。

## Conclusion

Week 6 的固定实验设置已完成复现检查，BM25 baseline、main expansion 和 supplementary control 均与 Week 5/Week 2 保存结果一致。因此，后续 Week 6 分析可以直接复用 Week 5 中这些固定设置的已有输出。
