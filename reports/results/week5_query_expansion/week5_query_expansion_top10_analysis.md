# Week 5 Query Expansion Top-10 Manual Analysis

## 检查范围

- Trace 文件: `data/results/query_expansion_trace_top10.jsonl`
- 标注文件: `data/results/query_expansion_trace_top10_labeled.jsonl`
- Query 范围: `q_000001` 到 `q_000010`
- 判断依据: `expanded_concepts` 是否命中或接近 `gold_concepts` 中的 K/U 概念，尤其是关键桥接实体、答案实体、答案属性和 comparison 判断属性。

`query_gold_overlap` 表示原始 query concepts 与 gold concepts 的交集。
`expanded_gold_overlap` 只表示扩展词与 gold concepts 的交集，不包含原始 query concepts。

## 总体结论

当前 expansion 结果不够稳定，不建议直接接入 BM25 主实验。10 条中只有 `q_000001` 明显扩到了核心 K 概念，`q_000004`、`q_000006`、`q_000009` 有部分帮助，其余多条缺少关键桥接实体或引入明显噪声。

主要问题是排序过度依赖 graph edge weight。高频泛词、年份、背景词和热门邻居容易排到前面，而真正关键的桥接实体没有进入 top-5。

## 逐条分析

| Query | 判断 | 说明 |
|---|---|---|
| `q_000001` | 基本合理 | 扩展词 `american` 命中 K 概念，是判断 Scott Derrickson 和 Ed Wood 是否同国籍的核心属性。其余 `c robert cargill`、`film`、`1960s`、`1970s` 对 nationality 判断帮助弱。 |
| `q_000002` | 不合理 | 关键 K 概念应是 `shirley temple`、`shirley temple black`、`chief`、`protocol`。实际只扩到 `1945` 和 `american`，分别是 U/N 级别，且 `life`、`soundtrack`、`book` 噪声较大。 |
| `q_000003` | 不合理 | 关键 K 概念包括 `hork bajir chronicles`、`second companion book`、`animorphs series`、`animorphs`、`science fantasy series`、`young adult books`。实际只 overlap 到 `books`，但它是 N 级泛词，`assistant secretaries`、`united states`、年份也明显跑偏。 |
| `q_000004` | 部分合理 | `esma sultan`、`ottoman`、`18th century`、`18th century ottoman imperial mosque` 都能辅助定位 gold passage，但缺少真正判断 same neighborhood 的 K 概念，如 `fatih`、`ortak y neighborhood`、`laleli fatih istanbul turkey`。 |
| `q_000005` | 不合理 | 关键 K 概念应是 `adriana trigiani`、`greenwich village`、`new york city`、`film director`。实际只扩到 `american`，这是 N 级高频词；`national intelligence`、`paris` 明显会带偏。 |
| `q_000006` | 弱相关 | 扩展词 `2013`、`2014` 对 Winner 句子有辅助作用，`hangul` 是背景噪声。关键 K 概念 `winner`、`yg entertainment` 没有被扩出来，因此不能算稳定有效。 |
| `q_000007` | 弱相关 | `3 april 1959` 可辅助定位 Eenasul Fateh，但关键 K 概念 `eenasul fateh`、`international management consultant`、`management consulting` 没有扩出。`american`、`record producer`、`album` 会误导检索方向。 |
| `q_000008` | 不合理 | 没有命中任何 gold concept。合理扩展应靠近 `androscoggin bank colis e`、`lewiston colisee`、`3 677`、`4 000 capacity`。实际 `members`、`buffaloes`、`boulder`、`pac 12 conference` 明显来自错误邻居。 |
| `q_000009` | 部分合理 | `juergen teller`、`marc jacobs`、`peter lindbergh` 是 U 级定位词，能帮助找到人物相关 passage。但题目问 older，关键 K 概念应是 `october 8 1970` 和 `august 14 1965`，当前扩展没有抓到出生日期。 |
| `q_000010` | 不合理 | comparison 的核心 K 概念是 `american`、`united states`、`american rock band`、`united states post punk dream pop band`。实际扩到 `united kingdom`、`canada`、`president`、`senate`、`virginia`，没有命中 gold overlap，且会严重带偏。 |

## 改进建议

### 1. 过滤或降权高频泛词

应对 `american`、`united states`、`film`、`book`、`series`、`album`、`team`、`members`、`people`、`person`、`year`、月份、单独年份等高频概念做过滤或强降权。

这些词不是永远无用，但不能仅凭 edge weight 排到 top。可以使用 graph node 的 `passage_count` 和 `degree` 做惩罚:

```text
adjusted_score = edge_score / log(2 + degree) / log(2 + passage_count)
```

### 2. 优先保留多词实体和具体短语

当前失败案例多数是没有扩出关键实体，例如 `shirley temple`、`adriana trigiani`、`winner`、`yg entertainment`、`androscoggin bank colis e`。排序时应给多词实体、标题型概念、专名短语更高权重。

可以加入简单 bonus:

```text
phrase_bonus = 1.2 if concept contains at least two tokens else 1.0
```

### 3. 区分 source concept 的可靠性

不要从所有 matched query concepts 等权扩展。`film`、`person`、`people`、`united states` 这类 source 本身度数高，容易把 expansion 带向热门背景。

建议优先从低 degree 的 query 实体扩展，如 `corliss archer`、`big stone gap`、`lewiston maineiacs`。对高 degree source 只允许贡献较小分数，或直接不作为 expansion source。

### 4. 奖励多 source 支持的候选词

如果一个候选 concept 能从多个 query concept 触达，通常更可靠。例如某个实体同时与题目中的角色和作品共现，比只从 `film` 触达更可信。

候选记录中可以保留 `sources`:

```text
source_bonus = 1 + 0.3 * (num_sources - 1)
```

### 5. 根据题型调整扩展目标

- `bridge` 题应优先扩桥接实体、答案实体、作品名、人物名、组织名、地点名。
- `comparison` 题应优先扩比较属性，如国籍、出生日期、地点、职业，而不是泛背景词。

例如 `q_000009` 问 older，扩展出生日期比扩展摄影师或品牌更有价值。`q_000010` 问 both from the United States，扩展美国相关属性比扩展其他国家或政治词更合理。

### 6. 控制 top_n 并保留 trace 诊断字段

在排序稳定前，建议先使用较小的 `top_n`，例如 3，而不是把 5 个候选全部拼进 query。同时继续保留:

- `gold_concepts`
- `query_gold_overlap`
- `expanded_gold_overlap`
- labeled 版本中的 K/U/N 标注

这些字段能快速判断改动后是扩到了真正 K 概念，还是只是增加了泛词 overlap。

## 下一步

先实现一个不使用 gold 信息的 reranking 策略，例如 `specificity`，只依赖 graph statistics、concept 字面特征和 source 支持数。然后重新生成 top10 trace，对比 `expanded_gold_overlap` 是否从 N/U 词转向 K 词。只有当 `q_000002`、`q_000005`、`q_000006`、`q_000008` 这类失败样例能扩出关键桥接实体后，再接入 BM25 实验脚本。
