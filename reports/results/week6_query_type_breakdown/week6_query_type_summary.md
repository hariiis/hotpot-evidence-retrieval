# Week 6 Query Type Breakdown Summary

## 1. 实验简介

HotpotQA query type 分为两类：

- `bridge`：问题需要通过桥接实体或中间证据连接多个事实。 这类问题可能更适合 graph expansion，因为 graph 有机会补充中间实体、实体别名或相关属性。扩展后的 query 可能更容易召回后续 evidence。
- `comparison`：问题需要比较两个实体的属性，例如国籍、地点、时间或类别。Graph expansion 如果只围绕其中一个实体扩展，可能提高一个 gold passage 的排名，同时伤害另一个 gold passage 的召回或排序。因此，comparison query 更容易受到不均衡 expansion 或 query drift 的影响。

本实验将 per-query retrieval metrics 与 HotpotQA query type metadata 连接起来，分别汇总 `bridge` 和 `comparison` queries 的检索表现。分析目标是观察 graph expansion 在不同 query type 上是否表现出不同影响，并判断 filtering 是否更偏向改善某一类 query。

本实验比较三种方法：

- BM25 baseline
- main expansion
- filtered expansion 

结果文件：

- Query type breakdown: `reports/results/week6_query_type_results.csv`
- Overall ablation results: `reports/results/week6_ablation/week6_ablation_results.csv`

## 2. 数据呈现

|          |                   Total (100)               |                   Bridge (79)               |              Comparison (21)              |
| Method   |  Recall@5 | Recall@10 |  MRR@10  | nDCG@10  | Recall@5  | Recall@10 | MRR@10   | nDCG@10  | Recall@5 | Recall@10| MRR@10   |  nDCG@10 |
|---       |---:       |---:       | ---:     |---:      |---:       |---:       |---:      |---:      |---:      |---:      |---:      |---:      |
| baseline | 0.546500  | 0.632333  | 0.755694 | 0.585073 | 0.528270  | 0.620042  | 0.775141 | 0.579967 | 0.615079 | 0.678571 | 0.682540 | 0.604278 |
| main     | 0.472333  | 0.617333  | 0.619718 | 0.510217 | 0.473418  | 0.608439  | 0.662392 | 0.523408 | 0.468254 | 0.650794 | 0.459184 | 0.460592 |
| filtered | 0.472333  | 0.612333  | 0.627163 | 0.510067 | 0.479747  | 0.602110  | 0.672237 | 0.523457 | 0.444444 | 0.650794 | 0.457596 | 0.459697 |


相对 BM25 baseline 的 query-type delta 如下：

| Method             | Query type | Num queries | Delta Recall@5 | Delta Recall@10 | Delta MRR@10 | Delta nDCG@10 |
|---                 |---         |---:         |---:            |---:             |---:          |---:           |
| main expansion     | bridge     | 79          | -0.054852      | -0.011603       | -0.112749    | -0.056559     |
| main expansion     | comparison | 21          | -0.146825      | -0.027778       | -0.223356    | -0.143686     |
| filtered expansion | bridge     | 79          | -0.048523      | -0.017933       | -0.102903    | -0.056511     |
| filtered expansion | comparison | 21          | -0.170635      | -0.027778       | -0.224943    | -0.144581     |


Filtering 相对 main expansion 的变化如下：

| Query type | Delta Recall@5 | Delta Recall@10 | Delta MRR@10 | Delta nDCG@10 |
|---         |---:            |---:             |---:          |---:           |
| bridge     | +0.006329      | -0.006329       | +0.009845    | +0.000049     |
| comparison | -0.023810      | +0.000000       | -0.001588    | -0.000895     |


## 3. 数据分析

### 3.1 bridge 是否比 comparison 更容易从 graph expansion 中受益？

本实验结果不支持“bridge 比 comparison 更容易从 graph expansion 中受益”这个结论。相对 BM25 baseline，main expansion 在两类 query 上都下降：

- `bridge`: Recall@10 下降 0.011603，MRR@10 下降 0.112749，nDCG@10 下降 0.056559。
- `comparison`: Recall@10 下降 0.027778，MRR@10 下降 0.223356，nDCG@10 下降 0.143686。

观察到的模式是：graph expansion 对两类 query 都没有带来整体提升，但 `comparison` 的退化幅度更大。结果表明，当前 expansion 设置可能对 `comparison` 更不稳定；对 `bridge` 的伤害相对较小，但还不能说 `bridge` 已经从 expansion 中受益。


### 3.2 comparison 是否更容易出现只改善一个 evidence hop 的情况？

仅凭本 query-type breakdown 不能直接回答这个问题。

当前表格使用的是按 query type 聚合后的 Recall@5、Recall@10、MRR@10、nDCG@10。这些指标能说明某类 query 的平均召回和排序变化，但不能判断具体哪一个 evidence hop 被改善。

从结果中只能观察到：`comparison` 在 main/filtered expansion 下的 MRR@10 和 nDCG@10 都下降更明显，说明排序质量可能更容易受到 expansion 噪声影响。但这不是“只改善一个 evidence hop”的直接证据。该问题应留给后续 query-level delta analysis 或 hop/evidence-level case study 进一步验证。


### 3.3 filtering 对哪种 query 类型更有效？

相对 main expansion，filtering 对 `bridge` 的影响略微更正面，但效果很弱且不一致：

- 在 `bridge` 上，filtering 使 Recall@5 提升 0.006329，MRR@10 提升 0.009845，nDCG@10 基本持平；但 Recall@10 下降 0.006329。
- 在 `comparison` 上，filtering 使 Recall@10 持平，但 Recall@5、MRR@10、nDCG@10 都小幅下降。

因此，观察到 filtering 可能更有利于 `bridge` query 的高排名结果或首个相关证据排序，但没有改善 `bridge` 的整体 Recall@10。对 `comparison`，当前结果没有显示 filtering 有明确帮助。


### 3.4 每类 query 的样本数是否足够支持结论？

本实验共有 100 条 query，其中：

- `bridge`: 79 条
- `comparison`: 21 条

`bridge` 样本数相对更多，结果更适合作为描述性观察。`comparison` 只有 21 条，样本较少，因此关于 comparison 的结论需要谨慎表述。当前结果可以说“观察到 comparison 退化更明显”或“结果表明 comparison 可能更容易受到 expansion 噪声影响”，但不应直接推广为普遍结论。

## 4. 总结

本 query type breakdown 观察到：当前 graph expansion 设置没有在 `bridge` 或 `comparison` 上超过 BM25 baseline。`comparison` 的退化幅度更大，尤其是 MRR@10 和 nDCG@10，说明 comparison query 可能更容易受到 expansion 噪声影响。

Filtering 的效果也有限。它对 `bridge` 的 MRR@10 和 Recall@5 有轻微正向变化，但没有改善 Recall@10；对 `comparison` 基本没有帮助。由于 `comparison` 只有 21 条样本，这些结果应作为描述性发现，而不是强结论。
