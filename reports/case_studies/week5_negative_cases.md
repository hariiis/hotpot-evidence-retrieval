# Week 5 Negative Cases: Graph Expansion

本报告解释 graph-based query expansion 在哪些 query 上失败。为了更清楚地区分“是 hop 太大，还是 top_n 太多”，负例不只来自单一配置，而是覆盖三类失败：

- `hop=1, top_n=5`：1-hop 下已经会被泛词 source node 带偏。
- `hop=1, top_n=10`：hop 没变，但 top_n 过大引入更多 tail noise。
- `hop=2, top_n=10`：2-hop 扩大候选范围后，噪声主题簇更容易进入 query。

Baseline 均为 `hop=0, top_n=0` 的 BM25 only。Rank 变化用同一个 BM25 retriever 对完整 passage corpus 重新排序得到，不只依赖保存的 top-10。

## Case 1: `q_000034`

| Field | Value |
|---|---|
| Expansion setting | `hop=1`, `top_n=5`, `strategy=edge_weight_log_passage_count` |
| Query | Are Freakonomics and In the Realm of the Hackers both American documentaries? |
| Query concepts | `freakonomics`, `american`, `realm`, `hackers`, `american documentaries` |
| Matched graph nodes | `freakonomics`, `american`, `realm`, `hackers` |
| Expanded concepts | `american animated television series`, `actor`, `nicolas cage`, `american comedy television series`, `american lawyer` |
| Gold evidence | `Freakonomics (film)::0`; `In the Realm of the Hackers::0` |
| Baseline top-5 | `Birthday Honours::3`; `In the Realm of the Hackers::0`; `Freakonomics (film)::0`; `The Longer We Make Love::3`; `Chris Menges::1` |
| Expansion top-5 | `It Could Happen to You (1994 film)::0`; `Evicted!::1`; `Iron Man (TV series)::0`; `Web Weirdos::0`; `Andy's Ancestry::0` |
| Metric change | Recall@5 `1.00 -> 0.00`; Recall@10 `1.00 -> 0.00`; MRR@10 `0.500 -> 0.000`; nDCG@10 `0.693 -> 0.000` |
| Gold rank change | `In the Realm of the Hackers::0`: `2 -> 26`; `Freakonomics (film)::0`: `3 -> 34` |

**原因分析。** 噪声 expanded concepts 主要是 `actor`、`nicolas cage`、`american animated television series`、`american comedy television series` 和 `american lawyer`。这里明显出现了 `american` 这种泛词 hub：它作为 matched graph node 产生多个娱乐领域邻居，把 query 从 documentary 判断带向 American entertainment pages。这个失败不是 hop 太大造成的，因为所有噪声都是 1-hop 扩出来的；`top_n=5` 则放大了问题，一次性加入多个同一噪声方向的 concepts。最终发生明显 query drift，两个 gold passages 都从 top-5 掉到 top-10 外。

## Case 2: `q_000057`

| Field | Value |
|---|---|
| Expansion setting | `hop=1`, `top_n=5`, `strategy=edge_weight_log_passage_count` |
| Query | D1NZ is a series based on what oversteering technique? |
| Query concepts | `d1nz`, `series`, `oversteering technique` |
| Matched graph nodes | `d1nz`, `series` |
| Expanded concepts | `dc entertainment`, `warner bros`, `david slack`, `dc nation's`, `dc nation's new teen titans shorts` |
| Gold evidence | `D1NZ::0`; `Drifting (motorsport)::0` |
| Baseline top-5 | `D1NZ::0`; `Raaz Pichhle Janam Ka::0`; `Rising Star (France)::0`; `D1NZ::1`; `List of The Office (U.S. TV series) characters::0` |
| Expansion top-5 | `Teen Titans (season 1)::1`; `Teen Titans (season 4)::1`; `List of Teen Titans Go! episodes::2`; `List of Teen Titans episodes::1`; `Teen Titans Go! (TV series)::2` |
| Metric change | Recall@5 `0.50 -> 0.00`; Recall@10 `0.50 -> 0.00`; MRR@10 `1.000 -> 0.000`; nDCG@10 `0.613 -> 0.000` |
| Gold rank change | `D1NZ::0`: `1 -> 14`; `Drifting (motorsport)::0`: `42 -> 73` |

**原因分析。** 噪声 expanded concepts 是 `dc entertainment`、`warner bros`、`david slack`、`dc nation's` 和 `dc nation's new teen titans shorts`。本例没有出现 `american` 或 `film`，但出现了 `series` 这个泛 source hub。由于 query concept extractor 没有把关键概念 `oversteering technique` 匹配到 graph node，expansion 只能从 `series` 出发，结果进入 Teen Titans production 主题簇。这个失败不是 hop 太大造成的，1-hop 已经足够跑偏；`top_n=5` 进一步加入了完整的错误主题簇。最终发生 query drift。

## Case 3: `q_000051`

| Field | Value |
|---|---|
| Expansion setting | `hop=1`, `top_n=10`, `strategy=edge_weight_log_passage_count` |
| Query | Which year and which conference was the 14th season for this conference as part of the NCAA Division that the Colorado Buffaloes played in with a record of 2-6 in conference play? |
| Query concepts | `14th season`, `ncaa division`, `colorado`, `2 6`, `conference`, `colorado buffaloes`, `record`, `conference play` |
| Matched graph nodes | `14th season`, `ncaa division`, `colorado`, `2 6`, `conference`, `colorado buffaloes`, `record` |
| Expanded concepts | `university colorado`, `men`, `university`, `fbs`, `men's basketball team`, `2016 17`, `boulder`, `fbs football season`, `buffaloes`, `coors events center` |
| Gold evidence | `2009 Colorado Buffaloes football team::0`; `2009 Colorado Buffaloes football team::2`; `2009 Big 12 Conference football season::0` |
| Baseline top-5 | `2009 Colorado Buffaloes football team::2`; `2009 Big 12 Conference football season::0`; `2009 Colorado Buffaloes football team::0`; `1989 Colorado Buffaloes football team::0`; `2011 Colorado Buffaloes football team::0` |
| Expansion top-5 | `2016-17 Colorado Buffaloes men's basketball team::0`; `2012 Colorado Buffaloes football team::0`; `2011 Colorado Buffaloes football team::0`; `2014 Colorado Buffaloes football team::0`; `2015 Colorado Buffaloes football team::0` |
| Metric change | Recall@5 `1.00 -> 0.00`; Recall@10 `1.00 -> 0.333`; MRR@10 `1.000 -> 0.167`; nDCG@10 `1.000 -> 0.167` |
| Gold rank change | `2009 Colorado Buffaloes football team::2`: `1 -> 15`; `2009 Big 12 Conference football season::0`: `2 -> 14`; `2009 Colorado Buffaloes football team::0`: `3 -> 6` |

**原因分析。** 噪声 expanded concepts 主要是 `men`、`university`、`men's basketball team`、`2016 17`、`boulder` 和 `coors events center`。本例没有典型的 `american`、`film` hub，但有 `conference`、`colorado`、`university` 这类体育/学校泛节点，导致 expansion 从 2009 football season drift 到 Colorado basketball 和其他年份的 football teams。这里 hop 仍然是 1，因此问题不是 hop 太大；关键问题是 `top_n=10` 太多，把后排 tail concepts 也加入 query，覆盖了原始 query 中的 `2009`、`Big 12`、football season 约束。最终发生 query drift。

## Case 4: `q_000100`

| Field | Value |
|---|---|
| Expansion setting | `hop=2`, `top_n=10`, `strategy=edge_weight_log_passage_count` |
| Query | Are Yingkou and Fuding the same level of city? |
| Query concepts | `yingkou`, `level`, `city` |
| Matched graph nodes | `yingkou`, `level`, `city` |
| Expanded concepts | `central business district`, `iata`, `8 mi`, `form 5010`, `icao ktta`, `jetport sanford lee county`, `lee county`, `public use airport`, `raleigh exec`, `raleigh exec jetport` |
| Gold evidence | `Yingkou::0`; `Fuding::0` |
| Baseline top-5 | `Yingkou::0`; `Bayuquan Railway Station::1`; `Yingkou East Railway Station::1`; `Yingkou Lanqi Airport::0`; `Tongcheng Subdistrict, Fuding::0` |
| Expansion top-5 | `Raleigh Executive Jetport::0`; `Pensacola International Airport::0`; `Yingkou Lanqi Airport::0`; `Raleigh Executive Jetport::1`; `John Glenn Columbus International Airport::0` |
| Metric change | Recall@5 `0.50 -> 0.00`; Recall@10 `1.00 -> 0.00`; MRR@10 `1.000 -> 0.000`; nDCG@10 `0.832 -> 0.000` |
| Gold rank change | `Yingkou::0`: `1 -> 11`; `Fuding::0`: `6 -> 16` |

**原因分析。** 噪声 expanded concepts 是 `iata`、`form 5010`、`icao ktta`、`jetport sanford lee county`、`lee county`、`public use airport`、`raleigh exec` 和 `raleigh exec jetport`。本例没有 `american`、`film`，但 `city` 和 `level` 在 2-hop expansion 下连接到了 airport/jetport 主题簇。这里 hop 太大是核心问题：1-hop 可能还能停留在城市相关邻居，2-hop 已经跳到远距离机场节点；同时 `top_n=10` 把整个 airport cluster 加入 query，使 BM25 明显偏向机场页面。最终发生严重 query drift，两个 gold passages 都跌出 top-10。

## Case 5: `q_000078`

| Field | Value |
|---|---|
| Expansion setting | `hop=2`, `top_n=10`, `strategy=edge_weight_log_passage_count` |
| Query | Alvaro Mexia had a diplomatic mission with which tribe of indigenous people? |
| Query concepts | `alvaro mexia`, `diplomatic mission`, `indigenous people` |
| Matched graph nodes | `alvaro mexia`, `diplomatic mission` |
| Expanded concepts | `embassy`, `receiving state`, `embassy nairobi`, `republic kenya`, `state department`, `united states america`, `consulates`, `country's diplomatic representatives`, `resident mission`, `republic` |
| Gold evidence | `Alvaro Mexia::0`; `Alvaro Mexia::1`; `Indigenous peoples of Florida::2` |
| Baseline top-5 | `Alvaro Mexia::0`; `Alvaro Mexia::1`; `Diplomatic mission::1`; `List of diplomatic missions of Azerbaijan::3`; `Diplomatic mission::0` |
| Expansion top-5 | `Embassy of the United States, Nairobi::0`; `Diplomatic mission::1`; `Embassy of the United States, Nairobi::1`; `Diplomatic mission::0`; `Embassy of the United States, Nairobi::3` |
| Metric change | Recall@5 `0.667 -> 0.00`; Recall@10 `0.667 -> 0.333`; MRR@10 `1.000 -> 0.100`; nDCG@10 `0.765 -> 0.136` |
| Gold rank change | `Alvaro Mexia::0`: `1 -> 10`; `Alvaro Mexia::1`: `2 -> 14`; `Indigenous peoples of Florida::2`: `2538 -> 2657` |

**原因分析。** 噪声 expanded concepts 主要是 `embassy nairobi`、`republic kenya`、`state department`、`united states america`、`consulates`、`country's diplomatic representatives`、`resident mission` 和 `republic`。这里出现了 `united states america` 这种泛国家 hub，也出现了 `diplomatic mission` 这个泛 source hub。失败既和 hop 太大有关，也和 `top_n=10` 太多有关：2-hop 把 `diplomatic mission` 扩到 Embassy/Nairobi/State Department 主题，top_n=10 又把这些远距离 concepts 大量拼进 query。最终发生 query drift，原本 rank 1、2 的 Alvaro Mexia gold passages 被 embassy pages 挤下去。

## 负例总结

常见失败原因：

1. **泛词 source hub 和泛词 concept 共同导致 query drift。**:
    - `american`、`series`、`city`、`diplomatic mission`、`conference` 这类 source node 会产生 lexical matching 很强但语义错误的 neighbors
    - 同时 BM25 会把 appended concepts 当作普通 query terms，因此 `actor`、`american`、`song`、`university`、`embassy`、`airport` 等词可能压过原始     query 中真正重要的实体约束。
2. **hop=2 更容易引入远距离噪声。**:
     Case 4 和 Case 5 显示，2-hop 会把城市 query 拉到 airport cluster，把 diplomatic mission query 拉到 embassy/state department cluster。
3. **top_n 太大会放大 tail noise。**:
     Case 3 在 `hop=1` 下已经失败，主要原因是 `top_n=10` 把 `men's basketball team`、`2016 17`、`coors events center` 等后排噪声概念加入 query。
4. **概念抽取缺口会放大失败。**:
     在 Case 2 中，关键概念 `oversteering technique` 没有匹配到 graph node，expansion 只能退化为从 `series` 扩展，最终错过 `drifting`。

## 总体结论

Graph expansion 最适合那些能通过 graph 补充 **具体别名、日期、分类标签、组织名或答案属性短语** 的 query。换句话说，当 matched query nodes 本身已经是具体实体或领域短语时，expansion 更容易产生有效补充。

最常见的失败模式是 **泛 source nodes 和 hub concepts 导致 query drift**。`american`、`film`、`series`、`song`、`team`、`conference`、`city`、`diplomatic mission` 这类概念应该作为 source nodes 和 candidate concepts 被过滤或强降权。

当前最合适的设置是 **`hop=1`，`top_n=3` 到 `5`**。如果目标是 ranking quality，`top_n=3` 更稳，因为它限制了噪声；如果目标是 Recall@10，`top_n=5` 有时能找回更多 evidence，但 drift 风险更高。在当前方法下，不建议使用 `hop=2` 或 `top_n=10`。
