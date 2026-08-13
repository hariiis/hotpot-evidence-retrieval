# Week 5 Query Expansion Parameter Comparison

## 实验目的

这一部分不是继续写新算法，而是系统地改变 `hop` 和 `top_n`，观察 graph-based query expansion 对 BM25 检索结果的影响。

本实验主要回答三个问题：

1. Graph expansion 是否比 BM25 baseline 更好？
2. `1-hop` 和 `2-hop` 哪个更有效？
3. 加入多少个 expanded concepts 比较合适？

同时比较两种 expansion candidate ranking strategy：

- `edge_weight`：按 graph edge weight 累积分数排序。
- `edge_weight_log_passage_count`：在 edge weight 基础上，用 candidate concept 的 `passage_count` 做 log 惩罚，降低高频 concept 的排序优势。

## 实验设置

所有实验只改变以下参数：

- `hop`
- `top_n`
- `strategy`

以下设置保持固定：

- BM25 `k1 = 1.5`
- BM25 `b = 0.75`
- query set: `data/processed/hotpotqa/queries.jsonl`
- passage corpus: `data/processed/hotpotqa/passages.jsonl`
- qrels: `data/processed/hotpotqa/qrels.jsonl`
- query concepts: `data/processed/concepts/query_concepts.jsonl`
- concept graph: `data/processed/concept_graph.pkl`
- retrieval `top_k = 10`

`hop=0, top_n=0` 是 BM25 baseline。虽然脚本中仍然需要传入 `strategy`，但在 `hop=0` 或 `top_n=0` 时不会真正执行 expansion，因此 summary 表中统一记为 `strategy=none`。

## 实验矩阵

| Experiment      | Hop | Top-n |
|------:          |---: |---:   |  
| BM25 baseline   | 0   | 0     |
| 1-hop expansion | 1   | 3     |
| 1-hop expansion | 1   | 5     |
| 1-hop expansion | 1   | 10    |
| 2-hop expansion | 2   | 3     |
| 2-hop expansion | 2   | 5     |
| 2-hop expansion | 2   | 10    |

每个 expansion 配置都分别运行 `edge_weight` 和 `edge_weight_log_passage_count` 两种 strategy，并写入独立目录，避免结果互相覆盖。

汇总结果文件：

- `reports/results/week5_query_expansion/week5_query_expansion_results_edge_weight.csv`
- `reports/results/week5_query_expansion/week5_query_expansion_results_edge_weight_log_passage_count.csv`


## Expansion 行为检查

除了平均检索指标，还统计以下 expansion 行为：

- 平均 matched graph nodes 数量：`avg_matched_graph_nodes`
- 完全没有 matched nodes 的 query 数量：`num_zero_matched_graph_nodes`
- 平均 expanded concepts 数量：`avg_expanded_concepts`
- 没有获得任何 expanded concept 的 query 数量：`num_zero_expanded_concepts`

这样做的原因是：`top_n=10` 只是上限，不代表每个 query 都真的加入了 10 个 concepts。如果很多 query 没有 matched graph nodes 或没有 expansion candidates，那么指标变化小可能不是 strategy 无效，而是 expansion 实际没有发生。

本次实验中，所有 query 都能匹配到 graph nodes：

| Hop | Top-n | avg_matched_graph_nodes | num_zero_matched_graph_nodes | avg_expanded_concepts | num_zero_expanded_concepts |
|---: |---:   |---:                     |---:                          |---:                   |---:                        |
| 0   | 0     | 4.090000                | 0                            | 0.000000              | 100                        |
| 1   | 3     | 4.090000                | 0                            | 3.000000              | 0                          |
| 1   | 5     | 4.090000                | 0                            | 5.000000              | 0                          |
| 1   | 10    | 4.090000                | 0                            | 10.000000             | 0                          |
| 2   | 3     | 4.090000                | 0                            | 3.000000              | 0                          |
| 2   | 5     | 4.090000                | 0                            | 5.000000              | 0                          |
| 2   | 10    | 4.090000                | 0                            | 10.000000             | 0                          |

这张表在两种 strategy 下数值相同，这是符合预期的。原因是这四个字段统计的是 expansion 的“数量行为”，不是 expanded concepts 的具体内容。

1. `avg_matched_graph_nodes` 和 `num_zero_matched_graph_nodes` 只取决于原始 query concepts 是否能在 concept graph 中找到对应节点。这个步骤发生在 candidate ranking 之前，因此不会受到 `edge_weight` 或 `edge_weight_log_passage_count` 的影响。只要 query set、query concepts 和 concept graph 固定，这两个值在所有 `hop`、`top_n` 和 `strategy` 配置下都会相同。

2. `avg_expanded_concepts` 和 `num_zero_expanded_concepts` 统计的是每个 query 最后加入了多少个 concepts。两种 strategy 使用同一个 candidate pool，只是排序方式不同，然后都取前 `top_n` 个 candidates。由于本次实验中每个 query 都有足够的 expansion candidates，因此除 baseline 外，两种 strategy 都能加满指定数量的 expanded concepts。所以这些数量统计也相同。

从这四个指标可以进一步判断 expansion 是否真正发生。首先，`num_zero_matched_graph_nodes = 0`，说明 100 个 query 中没有任何一个 query 完全匹配不到 graph node；同时 `avg_matched_graph_nodes = 4.090000`，说明每个 query 平均有约 4 个原始 query concepts 能进入 graph expansion 流程。其次，在所有 expansion 配置中，`avg_expanded_concepts` 都正好等于对应的 `top_n`，并且 `num_zero_expanded_concepts = 0`，说明每个 query 最终都获得了 expanded concepts，而且都加满了当前配置允许的数量。

因此，这张表说明本次实验中 expansion 是充分发生的：除 baseline 外，每个 query 都加入了指定数量的 expanded concepts。后续指标下降不能解释为“没有扩展成功”，更可能来自扩展词本身带来的 query drift 或噪声。


## Edge Weight 结果

`edge_weight` 表中的 delta 定义为：

```text
delta = expansion_metric - baseline_metric
```

| Hop | Top-n | Recall@10 | MRR@10   | nDCG@10  | Delta Recall@10 | Delta MRR@10 | Delta nDCG@10 |
|---: |---:   |---:       |---:      |---:      |---:             |---:          |---:           |
| 0   | 0     | 0.632333  | 0.755694 | 0.585073 | 0.000000        | 0.000000     | 0.000000      |
| 1   | 3     | 0.617333  | 0.657917 | 0.531507 | -0.015000       | -0.097777    | -0.053566     |
| 1   | 5     | 0.598167  | 0.617524 | 0.506001 | -0.034166       | -0.138170    | -0.079072     |
| 1   | 10    | 0.566500  | 0.585825 | 0.476096 | -0.065833       | -0.169869    | -0.108977     |
| 2   | 3     | 0.609000  | 0.671262 | 0.528814 | -0.023333       | -0.084432    | -0.056259     |
| 2   | 5     | 0.599833  | 0.653786 | 0.519436 | -0.032500       | -0.101908    | -0.065637     |
| 2   | 10    | 0.589833  | 0.554790 | 0.471605 | -0.042500       | -0.200904    | -0.113468     |

在 `edge_weight` strategy 下，所有 expansion 配置相对 BM25 baseline 都是负 delta，说明当前按 edge weight 直接选择 graph neighbors 并拼接到 query，并没有让 graph expansion 超过 BM25 baseline。也就是说，在这个 strategy 下，graph expansion 不是更好的检索方法。

在 graph expansion 总体没有超过 baseline 的前提下，`1-hop` 和 `2-hop` 的比较只能作为 expansion 内部的相对分析。`1-hop, top_n=3` 的 Recall@10 和 nDCG@10 最高，分别为 0.617333 和 0.531507；`2-hop, top_n=3` 的 MRR@10 最高，为 0.671262。因此不能断言某个 hop 在所有指标上都更有效，只能说明 `2-hop` 没有带来稳定收益。

`top_n` 的比较也需要放在 graph expansion 总体无效的背景下理解。这里讨论的是哪个设置损失较小，而不是哪个设置超过 baseline。整体来看，`top_n=3` 相对更稳；更大的 `top_n` 往往带来更明显的下降，说明加入更多 expanded concepts 可能增加噪声。


## Edge Weight Log Passage Count 结果

`edge_weight_log_passage_count` 表中有两类 delta：

```text
delta_vs_baseline = expansion_metric_edge_weight_log_passage_count - baseline_metric
delta_vs_edge_weight = expansion_metric_edge_weight_log_passage_count - expansion_metric_edge_weight
```

| Hop | Top-n | Recall@10 | MRR@10 | nDCG@10 | Delta vs Baseline Recall@10 | Delta vs Baseline MRR@10 | Delta vs Baseline nDCG@10 | Delta vs Edge Weight Recall@10 | Delta vs Edge Weight MRR@10 | Delta vs Edge Weight nDCG@10 |
|---:|---:|---:      |---:      |---:      |---:       |---:       |---:       |---:       |---:       |---:       |
| 0  | 0  | 0.632333 | 0.755694 | 0.585073 | 0.000000  | 0.000000  | 0.000000  | 0.000000  | 0.000000  | 0.000000  |
| 1  | 3  | 0.609833 | 0.650345 | 0.521765 | -0.022500 | -0.105349 | -0.063308 | -0.007500 | -0.007572 | -0.009742 |
| 1  | 5  | 0.617333 | 0.619718 | 0.510217 | -0.015000 | -0.135976 | -0.074856 | 0.019166  | 0.002194  | 0.004216  |
| 1  | 10 | 0.602333 | 0.607829 | 0.495910 | -0.030000 | -0.147865 | -0.089163 | 0.035833  | 0.022004  | 0.019814  |
| 2  | 3  | 0.604000 | 0.606020 | 0.494637 | -0.028333 | -0.149674 | -0.090436 | -0.005000 | -0.065242 | -0.034177 |
| 2  | 5  | 0.599000 | 0.503163 | 0.447043 | -0.033333 | -0.252531 | -0.138030 | -0.000833 | -0.150623 | -0.072393 |
| 2  | 10 | 0.599000 | 0.436591 | 0.416894 | -0.033333 | -0.319103 | -0.168179 | 0.009167  | -0.118199 | -0.054711 |

`edge_weight_log_passage_count` 相对 baseline 仍然全部为负，说明加入 `passage_count` 惩罚后，graph expansion 仍然没有超过 BM25 baseline。因此，这个 strategy 改善了部分 expansion ranking，但还不足以证明 graph expansion 本身优于 baseline。

在 hop 的比较上，`1-hop` 明显比 `2-hop` 更稳。`1-hop, top_n=5` 的 Recall@10 最高，达到 0.617333；`1-hop, top_n=3` 的 MRR@10 最高，达到 0.650345。相比之下，`2-hop` 的 MRR@10 下降更明显，特别是 `2-hop, top_n=10` 降到 0.436591，说明 2-hop 虽然扩大了候选范围，但也更容易引入远距离噪声 concept。

从 expanded concepts 数量看，`top_n=5` 在 Recall@10 上最好，但 `top_n=3` 在 MRR@10 和 nDCG@10 上更稳；`top_n=10` 没有带来进一步提升。这个结果说明加入更多 expanded concepts 并不一定更合适，较小或中等的 `top_n` 更符合当前 expansion 质量。与此同时，`edge_weight_log_passage_count` 在 `hop=1, top_n=5` 和 `hop=1, top_n=10` 上相对 `edge_weight` 有正 delta，说明 `passage_count` 惩罚确实缓解了一部分高频 concept 的负面影响，但改善幅度还不够。

## 两种 Strategy 对比

`edge_weight` 的问题是容易偏向高频、泛化、共现强的 concepts。手动查看 expansion traces 后，常见扩展词包括：

- `american`
- `united states`
- `song`
- `english`
- `actor`
- `film`
- `second`
- `album`

这些词并非永远无用，但对很多 HotpotQA 问题来说区分度不足。BM25 会把追加词直接当作 query terms，因此这些泛词可能把检索结果拉向泛相关文档，而不是目标 evidence passages。

`edge_weight_log_passage_count` 对高 passage_count concepts 做惩罚，因此在部分 `1-hop` 配置中比 `edge_weight` 更好。不过它仍然没有解决全部问题，可能因为：

1. 低频 concept 不一定就是正确 concept。
2. 只惩罚 candidate 的 passage_count，还没有控制 source concept 的泛化程度。
3. 当 `top_n` 较大时，后排 concepts 仍可能引入噪声。

因此，两种 strategy 的对比结论是：

- `edge_weight_log_passage_count` 相比 `edge_weight` 有一定改善，说明降低高频 concept 权重是有帮助的。
- 但两者都没有超过 BM25 baseline，说明当前 query expansion 仍然存在明显 query drift。
- 在现有设置下，`1-hop` 通常比 `2-hop` 更稳，较小的 `top_n` 通常比更大的 `top_n` 更稳。


## 总体结论

Expansion 行为检查显示，本次实验不是因为 expansion 没有发生才导致指标变化。100 个 query 中没有任何 query 完全匹配不到 graph node，平均每个 query 有 4.09 个 matched graph nodes；除 baseline 外，所有配置的 `avg_expanded_concepts` 都等于对应的 `top_n`，并且 `num_zero_expanded_concepts = 0`。因此，后续指标下降更可能来自 expanded concepts 的质量和 query drift，而不是 expansion coverage 不足。

对于 “Graph expansion 是否比 BM25 baseline 更好”，本次结果是否定的。`edge_weight` 和 `edge_weight_log_passage_count` 两种 strategy 的所有 expansion 配置都低于 BM25 baseline，说明当前把 graph concepts 直接拼接进 BM25 query 还不能提升整体检索效果。

对于 `1-hop` 和 `2-hop` 的比较，需要放在 graph expansion 总体无效的前提下理解。`edge_weight` 下不能断言某个 hop 在所有指标上都更好；`edge_weight_log_passage_count` 下 `1-hop` 更稳，`2-hop` 的 MRR@10 下降更明显。综合来看，`2-hop` 没有提供稳定收益，当前更适合把 `1-hop` 作为后续诊断和改进的保守设置。

对于 expanded concepts 数量，更多并不一定更好。`edge_weight` 下 `top_n=3` 损失较小；`edge_weight_log_passage_count` 下 `top_n=5` 的 Recall@10 最好，但 `top_n=3` 的 MRR@10 和 nDCG@10 更稳，`top_n=10` 没有带来进一步提升。因此，当前不应继续简单增大 `top_n`，较小或中等的 expansion 数量更合理。

两种 strategy 的对比说明，`edge_weight_log_passage_count` 相比 `edge_weight` 有部分改善，尤其在 `1-hop, top_n=5` 和 `1-hop, top_n=10` 上相对 `edge_weight` 出现正 delta。这说明惩罚高 passage_count concepts 有帮助，但改善幅度不足以超过 baseline。整体结论是：本次实验得到的是一个有用的 negative result，后续改进重点应放在控制 expansion 质量和减少高频泛词噪声，而不是继续增加 `hop` 或 `top_n`。
