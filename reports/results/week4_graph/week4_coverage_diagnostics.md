# Week 4 Coverage Diagnostics

## 实验设置

本实验用于判断当前 concept graph 是否能帮助 Week 5 的 Query Expansion。

- Query concepts: `data/processed/concepts/query_concepts.jsonl`
- Passage concepts: `data/processed/concepts/passage_concepts.jsonl`
- Qrels: `data/processed/hotpotqa/qrels.jsonl`
- Concept graph: `data/processed/concept_graph.pkl`
- Output CSV: `reports/results/week4_graph/week4_coverage_stats.csv`
- Number of queries: 100

这里的 `one_hop_recall` 包含 query concept 自身。也就是说，reachable
concepts 定义为：

```text
mapped_query_concepts union neighbors(mapped_query_concepts)
```

## 平均结果

| Metric | Average |
|---|---:|
| num_query_concepts | 4.850000 |
| num_gold_concepts | 18.600000 |
| query_coverage | 0.846091 |
| gold_coverage | 1.000000 |
| direct_overlap | 0.149021 |
| one_hop_recall | 0.722147 |

## 结论

当前 concept graph 对 gold passage concepts 的覆盖非常高，平均
`gold_coverage` 为 1.000000。这是预期结果，因为 graph 本身就是由 passage
concepts 构建的。因此，在当前设置下，`gold_coverage` 的诊断价值有限。只有在
后续对 graph 进行低频节点过滤、移除孤立节点，或者 concept normalization 发生
变化时，这个指标才会更有参考意义。

更关键的指标是 `query_coverage`。100 条 query 的平均 `query_coverage` 为
0.846091，说明大部分 query concepts 能够映射到 graph nodes，但仍有一部分
query concepts 不在 graph 中。这意味着 Week 5 的 Query Expansion 大多数情况
下可以使用 graph，但仍可能受到 normalization 不一致或 query concept 缺失的
影响。

平均 `direct_overlap` 只有 0.149021，说明 query concepts 和 gold concepts
的直接重合较少。如果只依赖原始 query concepts，能够直接命中的 gold concepts
有限。加入一跳邻居后，平均 `one_hop_recall` 提升到 0.722147，说明 concept
graph 的一跳扩展能够覆盖相当一部分原 query 中没有直接出现的 gold concepts。

因此，Week 5 值得尝试 graph-based query expansion。需要注意的是，一跳扩展
虽然明显提高了 recall，但也可能引入噪声。比较合理的下一步是对 neighbors 做
筛选或加权，再把筛选后的 concepts 加入 expanded query。
