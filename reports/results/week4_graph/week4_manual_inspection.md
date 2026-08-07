# Week 4 Manual Concept Inspection

## 检查范围

- 高频 concepts: passage concept 里按 passage_count 排名前 50 的 concept。
- Query concepts: `q_000001` 到 `q_000020` 共 20 条 query。
- Gold evidence passage concepts: qrels 中按出现顺序取前 20 个 unique gold passages。
- Graph: `data/processed/concept_graph.pkl`。

本检查关注 Week 5 graph-based query expansion 是否可用，而不是只判断图是否成功构建。

## 总体判断

Query 大多数可以进入图。100 条 query 的平均 `query_coverage` 为 0.846091，47 条 query 的 concepts 全部入图，没有 query 完全无法入图。前 20 条样本中，大部分 query 至少有关键实体入图，但也有 `government position`、`science fantasy young adult series`、`opera composers`、`roger o egeberg` 等关键短语缺失。

Gold concepts 在当前图中几乎总能入图，平均 `gold_coverage` 为 1.000000。但这主要是因为图本身由 passage concepts 构建，所以 gold coverage 不能单独证明 expansion 有效。

一跳邻居能触达大量 gold concepts。100 条 query 的平均 `one_hop_recall` 为 0.722147，中位数约 0.833333，38 条 query 达到 1.0，52 条 query 大于等于 0.8。但仍有 22 条 query 低于 0.5，9 条低于 0.25。

邻居质量是主要风险。每条 query 的一跳邻居数平均约 330，median 为 218，p90 为 802，最大为 1353。`american`、`united states`、`film`、`university`、`series` 等高频节点能桥接 gold evidence，但也会引入大量非特异噪声。因此 Week 5 可以做 expansion，但必须做 neighbor filtering/ranking，不能直接把所有一跳邻居拼进 query。

## 50 个高频 Concepts

| Rank | Concept | Passage Count | Degree | 人工判断 |
|---:|---|---:|---:|---|
| 1 | american | 196 | 1210 | 国籍/属性词；极高频、强噪声，可用于 nationality/type 判断但必须降权 |
| 2 | united states | 125 | 859 | 国家/地点实体；过宽、高噪声，可桥接地点但不宜直接强扩展 |
| 3 | song | 88 | 402 | 通用媒体类型词；高噪声，扩展会引入大量非特异歌曲相关节点 |
| 4 | second | 86 | 541 | 序数/泛词；高噪声，通常不适合作为 expansion concept |
| 5 | film | 80 | 501 | 通用媒体类型词；高噪声，扩展会偏向热门电影相关节点 |
| 6 | english | 74 | 554 | 语言/国籍/地点相关属性词；高噪声，语义歧义大 |
| 7 | album | 72 | 409 | 通用媒体类型词；中高噪声，音乐题有用但需降权 |
| 8 | university | 58 | 322 | 通用机构类型词；中高噪声，容易引入无关学校节点 |
| 9 | series | 58 | 307 | 通用作品类型词；中高噪声，需降权使用 |
| 10 | time | 50 | 344 | 泛词；高噪声，基本无 expansion 价值 |
| 11 | british | 46 | 390 | 国籍/属性词；中高噪声，可用于 nationality 判断但需降权 |
| 12 | italian | 46 | 350 | 国籍/属性词；中高噪声，可用于 nationality 判断但需降权 |
| 13 | season | 46 | 274 | 通用时间/作品结构词；中高噪声，需按题型保留 |
| 14 | 2010 | 41 | 232 | 年份节点；中高噪声，只有时间题中较有用 |
| 15 | members | 40 | 263 | 泛词/成员关系词；中高噪声，且与 `member` 重复 |
| 16 | year | 39 | 287 | 泛时间词；高噪声，直接扩展价值低 |
| 17 | number | 38 | 229 | 泛词/数量词；高噪声，直接扩展价值低 |
| 18 | u s | 38 | 279 | 国家缩写/normalization 残留；中高噪声，且与 `united states` 语义重复 |
| 19 | october | 37 | 261 | 月份节点；中高噪声，通常应降权或按题型保留 |
| 20 | september | 37 | 273 | 月份节点；中高噪声，通常应降权或按题型保留 |
| 21 | member | 35 | 215 | 泛词/成员关系词；中高噪声，且与 `members` 重复 |
| 22 | director | 34 | 222 | 职业/角色词；中高噪声，可能有桥接价值但过宽 |
| 23 | june | 34 | 234 | 月份节点；中高噪声，通常应降权或按题型保留 |
| 24 | july | 33 | 233 | 月份节点；中高噪声，通常应降权或按题型保留 |
| 25 | november | 33 | 259 | 月份节点；中高噪声，通常应降权或按题型保留 |
| 26 | april | 32 | 229 | 月份节点；中高噪声，通常应降权或按题型保留 |
| 27 | california | 31 | 184 | 地点实体；中等噪声，可用但仍需避免无条件强扩展 |
| 28 | team | 31 | 201 | 通用组织/体育类型词；中高噪声，直接扩展过宽 |
| 29 | 2014 | 30 | 223 | 年份节点；中高噪声，只有时间题中较有用 |
| 30 | new york city | 30 | 197 | 具体地点实体；中等噪声，可用但仍偏高频 |
| 31 | years | 30 | 256 | 泛时间词；高噪声，且与 `year` 重复 |
| 32 | australia | 30 | 274 | 国家/地点实体；中高噪声，可用但需降权 |
| 33 | february | 29 | 175 | 月份节点；中等噪声，通常应降权或按题型保留 |
| 34 | town | 29 | 206 | 泛地点类型词；中高噪声，直接扩展过宽 |
| 35 | city | 29 | 235 | 泛地点类型词；中高噪声，直接扩展过宽 |
| 36 | world | 28 | 202 | 泛词；中高噪声，直接扩展价值低 |
| 37 | group | 28 | 218 | 通用组织类型词；中高噪声，直接扩展过宽 |
| 38 | population | 27 | 124 | answer-type/数量主题词；中等噪声，population 题型可保留但需降权 |
| 39 | work | 27 | 201 | 泛词；中高噪声，直接扩展价值低 |
| 40 | place | 27 | 200 | 泛地点/泛词；中高噪声，直接扩展价值低 |
| 41 | men | 27 | 97 | 泛人群词；中等噪声，语义过宽 |
| 42 | united kingdom | 27 | 155 | 国家/地点实体；中等噪声，可用但需避免无条件强扩展 |
| 43 | lake | 27 | 117 | 地理类型词；中等噪声，地理题可用但需降权 |
| 44 | 2000 | 27 | 180 | 年份节点；中等噪声，只有时间题中较有用 |
| 45 | march | 27 | 243 | 月份节点；中高噪声，通常应降权或按题型保留 |
| 46 | love | 26 | 172 | 歧义词/主题词；中高噪声，语义分散 |
| 47 | january | 26 | 225 | 月份节点；中高噪声，通常应降权或按题型保留 |
| 48 | state | 26 | 167 | 泛地点/行政类型词；中高噪声，直接扩展过宽 |
| 49 | home games | 26 | 79 | 具体事件/场馆关系短语；低到中等噪声，有桥接价值 |
| 50 | president | 26 | 217 | 职业/角色词；中高噪声，可能有桥接价值但过宽 |

高频 concepts 的主要问题不是完全无意义，而是很多节点过宽。它们能提高 recall，但会把 expansion 推向热门实体、热门年份、热门类型词。

## 20 条 Query Concepts 检查

| Query | Type | Query Concepts | 入图/缺失 | 一跳邻居质量 |
|---|---|---|---|---|
| q_000001 | comparison | scott derrickson; ed wood; nationality | 3/3 入图 | 好。能从 `scott derrickson` 触达 `american` 等 gold concepts，但 `nationality` 本身偏 answer-type |
| q_000002 | bridge | corliss archer; kiss tell; government position; woman; film; kiss | 5/6 入图，缺 `government position` | 部分有效。`corliss archer`、`kiss` 能桥到 Shirley Temple；`film` 带来大量噪声 |
| q_000003 | bridge | science fantasy young adult series; person; set; companion books; stories; enslaved worlds; alien species | 4/7 入图 | 弱。关键长概念缺失，命中的多是 `book`、`time`、`second` 等泛词 |
| q_000004 | comparison | laleli mosque; esma; sultan mansion; laleli mosque esma sultan mansion; neighborhood | 2/5 入图 | 部分有效。能桥到 Laleli/Istanbul/Turkey，但 `esma` 粒度太细，`sultan mansion` 缺失 |
| q_000005 | bridge | big stone gap; new york; director; romantic comedy; new york city | 4/5 入图 | 好但噪声大。能触达所有 gold concepts，`director`、`new york` 带来大量邻居 |
| q_000006 | bridge | s s; south korean; 2014 s s; debut album; south korean boy group | 5/5 入图 | 好。query 和 gold concepts 高度重合 |
| q_000007 | bridge | aladin; stage; organizations; performance; consultant | 5/5 入图 | 好。能桥到管理咨询相关 gold concepts |
| q_000008 | bridge | arena; lewiston maineiacs; home games; people | 4/4 入图 | 中等。能桥到 arena/team/home games，但 `people` 是泛词且未直接触达容量数字 |
| q_000009 | bridge | annie morton; terry richardson | 2/2 入图 | 好。实体节点直接触达两边 gold evidence |
| q_000010 | comparison | local h; united states | 2/2 入图 | 好但噪声极大。`united states` degree 859 |
| q_000011 | bridge | lawrence; kansas; kansas city; fight song; university; main campus; branch campuses; kansas city metropolitan area | 8/8 入图 | 好。query concepts 与 gold concepts 高度重合，但 `university` 高噪声 |
| q_000012 | bridge | nicolas cage; t leoni; credits; film | 4/4 入图 | 中等偏好。能桥到目标 screenwriter，但 `film` 和 `credits` 噪声较大 |
| q_000013 | bridge | guns n roses; arnold schwarzenegger; new york police; promo; movie; new york police detective | 6/6 入图 | 中等。能桥到 song/soundtrack/year，但仍需要排序找答案 |
| q_000014 | comparison | random house tower; 888 7th avenue; real estate | 3/3 入图 | 中等。能桥到 Random House Tower，另一个建筑侧依赖有限 |
| q_000015 | bridge | david beckham; manchester united; football manager; timeframe | 3/4 入图，缺 `timeframe` | 好。能桥到 Alex Ferguson 相关 concepts |
| q_000016 | bridge | fishing lake; brown state fishing lake; country; population; inhabitants | 4/5 入图，缺 `inhabitants` | 好但需过滤。能触达 Brown County/Kansas/United States，`country`、`population` 较宽 |
| q_000017 | bridge | vermont; 1988; 1996; vermont catamounts men's soccer team; conference | 5/5 入图 | 好。能桥到 America East/North Atlantic Conference |
| q_000018 | comparison | ambroise thomas; opera; giuseppe verdi; opera composers | 3/4 入图，缺 `opera composers` | 弱。只命中 `italian`、`mignon`，没有稳定触达 composer 相关 gold concepts |
| q_000019 | bridge | roger o egeberg; health scientific affairs; years; assistant secretary; health; scientific affairs; administration; president | 7/8 入图，缺 `roger o egeberg` | 中等。能桥到 Nixon/department，但 `years`、`president` 噪声大 |
| q_000020 | comparison | england; henry roth; robert erskine childers; writer | 4/4 入图 | 中等。触达 Henry Roth 侧较好，对 Childers/England 侧较弱 |

20 条 query concepts 的主要问题不是无法入图，而是入图后邻居质量不稳定。具体实体通常能提供有效桥接，answer-type 词和高频泛词则容易把一跳扩展变成噪声。

## 20 个 Gold Evidence Passage Concepts 检查

| # | Passage | 抽取到的 Concepts | Concepts 质量判断 |
|---:|---|---|---|
| 1 | Scott Derrickson::0 | `scott derrickson`; `july 16 1966`; `american`; `american director`; `screenwriter`; `producer` | 实体、出生日期、nationality、职业抽取得较好；`american director` 与 `director` 类关系未合并 |
| 2 | Ed Wood::0 | `edward davis wood jr`; `october 10 1924`; `december 10 1978`; `american`; `october`; `december`; `american filmmaker`; `actor`; `writer`; `producer`; `director` | 实体和职业完整；月份 `october`、`december` 作为单独节点偏噪声 |
| 3 | Kiss and Tell (1945 film)::0 | `kiss`; `tell`; `1945`; `american`; `17 year old`; `shirley temple`; `corliss archer`; `1945 american comedy film`; `17 year old shirley temple` | 电影、年份、Shirley Temple、Corliss Archer 抽取得好；`kiss`/`tell` 拆分会引入噪声 |
| 4 | Shirley Temple::0 | `shirley temple black`; `april 23 1928`; `february 10 2014`; `american`; `hollywood`; `1935`; `april`; `february`; `american actress`; `singer`; `dancer`; `businesswoman`; `diplomat`; `hollywood's number box office draw`; `child actress` | 人名、日期、职业较完整；`hollywood's number box office draw` 太细 |
| 5 | Shirley Temple::1 | `united states`; `ghana`; `czechoslovakia`; `adult`; `united states ambassador`; `chief`; `protocol` | `chief` 和 `protocol` 被拆开，缺少完整 `chief of protocol`，会影响 bridge |
| 6 | The Hork-Bajir Chronicles::0 | `second`; `k applegate`; `hork bajir chronicles`; `second companion book`; `animorphs series` | 作品名、series、companion book 可用；`second` 单独节点噪声大 |
| 7 | The Hork-Bajir Chronicles::1 | `23`; `pretender`; `ellimist chronicles`; `andalite chronicles`; `respect`; `continuity`; `series`; `place`; `book`; `events`; `story`; `time` | 大量泛词：respect、continuity、place、book、events、story、time，桥接质量弱 |
| 8 | The Hork-Bajir Chronicles::2 | `tobias`; `jara hamee`; `yeerks`; `hork bajir`; `aldrea`; `andalite`; `dak hamee`; `book`; `valley`; `free hork bajir`; `story`; `companion`; `world`; `invasion` | 专名较好；`world`、`companion`、`story` 较泛 |
| 9 | Animorphs::0 | `katherine applegate`; `michael grant`; `k applegate`; `scholastic`; `animorphs`; `science fantasy series`; `young adult books`; `husband` | 作品、作者、系列类型抽取得较好；`science fantasy series` 与 query 的更长短语不匹配 |
| 10 | Animorphs::1 | `person`; `main characters`; `turns`; `books`; `perspectives` | 多数为泛概念：person、turns、books、perspectives；能入图但桥接弱 |
| 11 | Laleli Mosque::0 | `laleli mosque`; `turkish`; `laleli camii`; `tulip mosque`; `18th century`; `ottoman`; `laleli`; `fatih`; `istanbul`; `turkey`; `18th century ottoman imperial mosque`; `laleli fatih istanbul turkey` | 地点、别名、建筑类型较好 |
| 12 | Esma Sultan Mansion::0 | `turkish`; `english`; `bosphorus ortak y`; `istanbul`; `turkey`; `esma sultan`; `today`; `esma sultan mansion`; `esma sultan yal s`; `historical yal`; `waterside mansion`; `bosphorus`; `ortak y neighborhood`; `original owner`; `cultural center` | 概念完整，但非 ASCII/重音归一化造成 `ortak y`、`yal s` 等损伤 |
| 13 | Big Stone Gap (film)::0 | `big stone gap`; `2014`; `american`; `adriana trigiani`; `donna gigliotti`; `altar identity studios`; `media society`; `2014 american drama romantic comedy film`; `subsidiary` | 电影、年份、导演、制作方较好；超长类型短语太细 |
| 14 | Adriana Trigiani::0 | `adriana trigiani`; `italian`; `american`; `sixteen`; `greenwich village`; `new york city`; `italian american best selling author`; `sixteen books`; `television writer`; `film director`; `entrepreneur` | 人名、地点、职业较好；`sixteen` 单独节点偏噪声 |
| 15 | 2014 S/S::0 | `s s`; `south korean`; `2014 s s`; `debut album`; `south korean group winner` | 专辑和团体相关概念质量好；`s s` 是格式化残留但对本题可用 |
| 16 | Winner (band)::0 | `south korean`; `2013`; `yg entertainment`; `2014`; `winner`; `hangul`; `south korean boy group` | 团体、年份、YG Entertainment 抽取得好 |
| 17 | Eenasul Fateh::0 | `eenasul fateh`; `bengali`; `3 april 1959`; `aladin`; `bangladeshi`; `magician`; `stage`; `bangladeshi british cultural practitioner`; `live artist`; `international management consultant` | 人名、stage name、职业抽取得好 |
| 18 | Management consulting::0 | `management consulting`; `practice`; `organizations`; `performance`; `analysis`; `existing organizational problems`; `development`; `plans`; `improvement` | 领域概念可用；`practice`、`plans`、`improvement` 这类词偏泛 |
| 19 | Lewiston Maineiacs::1 | `androscoggin bank colis e`; `team`; `home games` | `home games` 和场馆名可用；`androscoggin bank colis e` 有重音损伤 |
| 20 | Androscoggin Bank Colisée::0 | `androscoggin bank colis e`; `central maine`; `lewiston colisee`; `4 000`; `3 677`; `lewiston`; `maine`; `1958`; `central maine civic center`; `4 000 capacity`; `multi purpose arena` | 场馆、容量、地点可用；`4 000`、`3 677` 是有价值答案概念，但需要数值处理；场馆名重音损伤 |

Gold evidence concepts 整体可入图且能保留关键实体、地点、职业和数值信息，但 passage 侧也混入了日期碎片、泛名词、过长 noun phrase 和字符归一化损伤。


## 记录的问题

### 是否有无意义词

有。主要包括：

- 泛词：`time`、`year`、`years`、`number`、`place`、`work`、`world`、`group`、`state`、`city`、`town`。
- 序数/日期碎片：`second`、`january`、`february`、`march`、`april`、`june`、`july`、`october`、`november`、`2010`、`2014`、`2000`。
- 过宽类型词：`film`、`song`、`album`、`series`、`university`、`team`。
- 编码或 normalization 损伤：`androscoggin bank colis e`、`ortak y`、`esma sultan yal s`。

这些词不是全部无意义，但直接用于 expansion 时容易成为噪声源。

### 是否有重复概念

有语义重复，但精确重复已被单条记录内 deduplicate。

- 单复数未合并：`member`/`members`、`year`/`years`。
- 缩写和全称未合并：`u s`/`united states`。
- 层级概念并存：`film`/`1945 american comedy film`、`american director`/`director`、`science fantasy series`/`science fantasy young adult series`。
- 别名和损伤形式并存：`androscoggin bank colisée` 类实体可能因重音处理变成 `androscoggin bank colis e`。

### 是否概念太细或太粗

两类问题都存在。

太粗的概念更影响 expansion，包括 `american`、`film`、`united states`、`university`、`series`、`time`。这些节点 degree 很高，会把大量无关 passage concepts 引入邻居集合。

太细的概念也存在，例如 `1994 american biographical period comedy drama film`、`laleli mosque esma sultan mansion`、`science fantasy young adult series`、`500 mile race eavery`、`hollywood's number box office draw`。这些概念可读但匹配脆弱，query 与 gold passage 稍有措辞差异就无法相连。

### 是否影响 Week 5 Expansion

会影响，而且是 Week 5 的核心风险。

正面影响是显著的：直接 overlap 平均只有 0.149021，一跳 recall 平均提升到 0.722147，说明 graph neighbors 确实能补充 query 中没有直接出现的 gold concepts。

负面影响也明显：高频节点会把邻居规模推到数百甚至上千，直接全量扩展会稀释 retrieval query，尤其是 bridge 问题中会混入大量热门年份、国家、职业、媒体类型词。
