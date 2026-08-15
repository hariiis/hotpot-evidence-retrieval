# Week 5 Positive Cases: Graph Expansion

本报告解释 graph-based query expansion 在哪些 query 上有效。主比较配置为：

- Baseline: `hop=0, top_n=0`, BM25 only
- Expansion: `hop=1, top_n=5, strategy=edge_weight_log_passage_count`
- Rank 变化：用同一个 BM25 retriever 对完整 passage corpus 重新排序得到，不只依赖保存的 top-10。

选择该配置的原因是它在 Week 5 参数比较中取得最高的 expansion Recall@10，同时仍是保守的 1-hop 设置。

## Case 1: `q_000033`

| Field | Value |
|---|---|
| Query | Which French ace pilot and adventurer fly L'Oiseau Blanc |
| Query concepts | `french`, `french ace pilot`, `adventurer` |
| Matched graph nodes | `french`, `french ace pilot`, `adventurer` |
| Expanded concepts | `15 march`, `15 march 1892`, `charles eug ne`, `charles eug ne jules marie nungesser`, `jules marie nungesser` |
| Gold evidence | `Charles Nungesser::0`; `L'Oiseau Blanc::1` |
| Baseline top-5 | `W. E. Johns::1`; `François Coli::0`; `Charles Nungesser::0`; `Gervais Raoul Lufbery::0`; `Georges Madon::0` |
| Expansion top-5 | `Charles Nungesser::0`; `François Coli::0`; `W. E. Johns::1`; `Georges Madon::0`; `Wooster and Davis::3` |
| Metric change | Recall@10 `0.50 -> 1.00`; MRR@10 `0.333 -> 1.000`; nDCG@10 `0.307 -> 0.807` |
| Gold rank change | `Charles Nungesser::0`: `3 -> 1`; `L'Oiseau Blanc::1`: `26 -> 8` |

**原因分析。** `15 march`、`15 march 1892` 和 `jules marie nungesser` 都出现在 gold passage 中，或能直接指向 `Charles Nungesser::0`。这些 expanded concepts 是具体日期和人物姓名片段，不是泛词 hub。加入这些词后，BM25 与 gold passage 的 lexical matching 明显增强，使 `Charles Nungesser::0` 从 rank 3 提升到 rank 1，`L'Oiseau Blanc::1` 也从 rank 26 提升到 rank 8。这些具体词原本不在 query 中，是 graph expansion 补充进来的；加入后 gold passage 的排名明显上升，因此这次提升主要来自graph expansion。

## Case 2: `q_000060`

| Field | Value |
|---|---|
| Query | Are both Cypress and Ajuga genera? |
| Query concepts | `cypress`, `ajuga`, `cypress ajuga genera` |
| Matched graph nodes | `cypress`, `ajuga` |
| Expanded concepts | `genera`, `cupressus`, `family cupressaceae`, `lamiaceae`, `cupressaceae` |
| Gold evidence | `Cypress::0`; `Ajuga::0` |
| Baseline top-5 | `Cypress-pine::0`; `Ajugeae::0`; `Cupressus::0`; `Libocedrus::1`; `Cedrol::0` |
| Expansion top-5 | `Cupressus::0`; `Cypress-pine::0`; `Ajugeae::0`; `Pilgerodendron::0`; `Cedrol::0` |
| Metric change | Recall@10 `0.00 -> 1.00`; MRR@10 `0.000 -> 0.167`; nDCG@10 `0.000 -> 0.412` |
| Gold rank change | `Cypress::0`: `20 -> 6`; `Ajuga::0`: `25 -> 8` |

**原因分析。** `family cupressaceae`、`cupressaceae` 和 `lamiaceae` 是有用的植物分类概念。其中 `family Cupressaceae` 出现在 `Cypress::0` 中，`Lamiaceae` 出现在 `Ajuga::0` 中。Expansion 没有把 gold passage 推进 top-5，但把两个 gold passage 都从 top-10 外拉进了 top-10，使 Recall@10 从 0.00 提升到 1.00。原始 query 只问 Cypress 和 Ajuga 是否为 genera，并没有包含这两个 family 名称；这些 taxonomy concepts 是从 `cypress` 和 `ajuga` 通过 graph expansion 补进来的，所以提升确实来自 graph expansion。

## Case 3: `q_000021`

| Field | Value |
|---|---|
| Query | Which other Mexican Formula One race car driver has held the podium besides the Force India driver born in 1990? |
| Query concepts | `mexican`, `force india`, `1990`, `mexican formula race car driver`, `podium`, `force india driver` |
| Matched graph nodes | `mexican`, `force india`, `1990`, `podium` |
| Expanded concepts | `sergio p rez`, `26 january 1990`, `checo p rez`, `mexican racing driver`, `sahara force india f1 team` |
| Gold evidence | `Sergio Pérez::0`; `Formula One drivers from Mexico::2`; `Formula One drivers from Mexico::1` |
| Baseline top-5 | `Force India VJM04::0`; `Eduardo Troconis::0`; `Sergio Pérez::0`; `Formula One drivers from Mexico::2`; `Mike Shank::0` |
| Expansion top-5 | `Sergio Pérez::0`; `Formula One drivers from Mexico::2`; `2014 Bahrain Grand Prix::3`; `Force India VJM04::0`; `Eduardo Troconis::0` |
| Metric change | MRR@10 `0.333 -> 1.000`; nDCG@10 `0.437 -> 0.765`; Recall@10 unchanged at `0.667` |
| Gold rank change | `Sergio Pérez::0`: `3 -> 1`; `Formula One drivers from Mexico::2`: `4 -> 2`; `Formula One drivers from Mexico::1`: `19 -> 21` |

**原因分析。** 这是最干净的正例。Graph expansion 扩出了 `26 january 1990`、`mexican racing driver` 和 `sahara force india f1 team`，这些词都出现在 gold evidence 中，能直接增强 Sergio Perez 相关 passage 的 lexical matching。`Sergio Pérez::0` 从 rank 3 提升到 rank 1，`Formula One drivers from Mexico::2` 也从 rank 4 提升到 rank 2。由于这些判别性短语原始 query 中没有出现，提升确实来自 graph expansion。

## Case 4: `q_000070`

| Field | Value |
|---|---|
| Query | The 2017-18 Wigan Athletic F.C. season will be a year in which the team competes in the league cup known as what for sponsorship reasons? |
| Query concepts | `2017 18`, `wigan athletic f c season`, `year`, `2017 18 wigan athletic f c season`, `team`, `league cup`, `sponsorship reasons` |
| Matched graph nodes | `wigan athletic f c season`, `year`, `team`, `league cup`, `sponsorship reasons` |
| Expanded concepts | `2014 15 season`, `hornets`, `10 seasons`, `2013 14 season`, `annual knockout football competition` |
| Gold evidence | `2017-18 Wigan Athletic F.C. season::1`; `EFL Cup::0` |
| Baseline top-5 | `2006-07 Wigan Athletic F.C. season::0`; `2007-08 Wigan Athletic F.C. season::0`; `1978-79 Wigan Athletic F.C. season::0`; `1979-80 Wigan Athletic F.C. season::0`; `Trinidad and Tobago League Cup::0` |
| Expansion top-5 | `EFL Cup::0`; `Trinidad and Tobago League Cup::0`; `2006-07 Wigan Athletic F.C. season::0`; `2007-08 Wigan Athletic F.C. season::0`; `1978-79 Wigan Athletic F.C. season::0` |
| Metric change | Recall@5 `0.00 -> 0.50`; MRR@10 `0.167 -> 1.000`; nDCG@10 `0.218 -> 0.613` |
| Gold rank change | `EFL Cup::0`: `6 -> 1`; `2017-18 Wigan Athletic F.C. season::1`: `13 -> 25` |

**原因分析。** 真正有帮助的 expanded concept 是 `annual knockout football competition`，它出现在 `EFL Cup::0` gold passage 中，并且是从 `league cup` 和 `sponsorship reasons` 这两个 query 相关节点扩展出来的。加入这个概念后，BM25 对 `EFL Cup::0` 的 lexical matching 增强，使该 gold passage 从 rank 6 提升到 rank 1。这个案例是局部正例：answer-bearing passage 被显著提前，但另一个 gold passage `2017-18 Wigan Athletic F.C. season::1` 从 rank 13 降到 rank 25，说明 expansion 帮助了答案 hop，同时伤害了 season hop。

## Case 5: `q_000049`

| Field | Value |
|---|---|
| Query | Are Ferocactus and Silene both types of plant? |
| Query concepts | `silene`, `ferocactus`, `types`, `plant` |
| Matched graph nodes | `silene`, `ferocactus`, `types`, `plant` |
| Expanded concepts | `flowering plant`, `species`, `caryophyllaceae`, `pink family`, `genus silene` |
| Gold evidence | `Ferocactus::0`; `Silene::0` |
| Baseline top-5 | `Sex determination in Silene::0`; `Silene tomentosa::0`; `Silene antirrhina::0`; `Silene stenophylla::0`; `Silene conoidea::0` |
| Expansion top-5 | `Silene stenophylla::0`; `Silene tomentosa::0`; `Silene::0`; `Silene antirrhina::0`; `Silene conoidea::0` |
| Metric change | Recall@5 `0.00 -> 0.50`; Recall@10 `0.00 -> 0.50`; MRR@10 `0.000 -> 0.333`; nDCG@10 `0.000 -> 0.307` |
| Gold rank change | `Silene::0`: `19 -> 3`; `Ferocactus::0`: `13 -> 17` |

**原因分析。** `flowering plant` 和 `caryophyllaceae` 出现在 `Silene::0` gold passage 中，`genus silene` 也是很接近的实体/短语线索。这些 expanded concepts 把 `Silene::0` 从 rank 19 提升到 rank 3，使 Recall@5 和 Recall@10 都从 0.00 提升到 0.50。这个提升来自 graph expansion，但它也是不完整的：当前 top-5 expanded concepts 基本都围绕 `silene`，没有给 `ferocactus` 提供有效补充，导致 `Ferocactus::0` 从 rank 13 降到 rank 17。

## 正例总结

Graph expansion 最适合以下 query：

1.. **matched graph nodes 本身比较具体的 query**:
      如果 expansion 是从 `cypress`、`ajuga`、`force india` 这类具体节点出发，效果通常比从 `team`、`year`、`plant` 这类泛节点出发更稳
2. **能扩到具体、低噪声、可直接增强 lexical matching 的 concepts 的 query**:
    - 具体实体别名或日期，例如 `26 january 1990`、`jules marie nungesser`、`sahara force india f1 team`
    - 以及领域分类或答案属性短语，例如 `family cupressaceae`、`lamiaceae`、`annual knockout football competition`

正例中的收益通常来自把一个关键 gold passage，尤其是 answer-bearing passage，提前到更高 rank。需要注意的是，Case 4 和 Case 5 属于部分正例：它们的 query-level 指标确实提升了，但其中某一个 gold passage 的排名下降。这说明 graph expansion 有时只帮助一个 evidence hop，同时伤害另一个 evidence hop；这种不稳定性可能是整体平均指标难以超过 BM25 baseline 的原因之一。
