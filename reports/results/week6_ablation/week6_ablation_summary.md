# Week 6 Filtering Ablation Summary

## Setup

本实验比较三个固定设置：

| Experiment         | Hop | Top-n | Strategy                      | Filtering |
|---                 |---: |---:   |---                            |---        |
| BM25 baseline      | 0   | 0     | none                          | off       |
| main expansion     | 1   | 5     | edge_weight_log_passage_count | off       |
| filtered expansion | 1   | 5     | edge_weight_log_passage_count | on        |

Filtering 规则固定为：在 expansion candidate selection 阶段过滤 `passage_count` 最高的 top 1% concepts。原始 concept graph 不删除、不修改。具体输出见 `reports/results/week6_ablation/week6_ablation_results.csv`。

## Main Results

| Experiment         | Recall@5 | Recall@10 | MRR@10   | nDCG@10  | Delta Recall@10 | Delta MRR@10 | Delta nDCG@10 |
|---                 |---:      |---:       |---:      |---:      |---:             |---:          |---:           |
| BM25 baseline      | 0.546500 | 0.632333  | 0.755694 | 0.585073 | 0.000000        | 0.000000     | 0.000000      |
| main expansion     | 0.472333 | 0.617333  | 0.619718 | 0.510217 | -0.015000       | -0.135976    | -0.074856     |
| filtered expansion | 0.472333 | 0.612333  | 0.627163 | 0.510067 | -0.020000       | -0.128531    | -0.075006     |

## Findings

1. Filtering 是否优于未过滤的 main expansion？

不是整体优于。Filtering 后 Recall@10 从 0.617333 降到 0.612333，nDCG@10 从 0.510217 小幅降到 0.510067；但 MRR@10 从 0.619718 提升到 0.627163。也就是说，filtering 对首个相关证据的排序有轻微帮助，但没有改善整体 recall。

2. Filtering 是否减少高频泛词进入 expanded concepts？

是。主实验的 top 1% 高频 concept blocklist 共 172 个 concepts。未过滤 main expansion 中，26/100 个 query 的 expanded concepts 包含这些高频 concepts，共出现 36 次；filtered expansion 中该数量降为 0。说明 filtering 按设计有效阻止了高频泛词进入 expanded concepts。

3. Filtering 是否减少严重 query drift？

本实验不做严格的 query-level drift 判断，这部分留给后续 Query-level Stability Analysis。仅从 aggregate metrics 看，filtering 没有显示出明显缓解 query drift 的证据：filtered expansion 的 Recall@10 低于 main expansion，nDCG@10 基本持平但略低，只有 MRR@10 小幅提升。因此目前只能说 filtering 可能改善了部分 query 的首个相关结果排序，但不能证明它减少了严重 query drift。

4. Filtering 后是否仍然低于 BM25 baseline？

是。filtered expansion 在三个核心指标上仍低于 BM25 baseline：Recall@10 低 0.020000，MRR@10 低 0.128531，nDCG@10 低 0.075006。

## Conclusion

Top 1% `passage_count` filtering 成功移除了高频泛词 expansion candidates，但没有带来整体检索提升。它略微改善 MRR@10，却降低 Recall@10，并且仍明显低于 BM25 baseline。因此，本实验不支持将该 filtering 设置作为优于 main expansion 或 BM25 baseline 的改进方法；它更适合作为控制 query expansion 噪声的诊断性 ablation。
