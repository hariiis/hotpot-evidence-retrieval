# Week 3 Retrieval Case Study: BM25 vs Dense vs Hybrid

## 1. 实验配置信息

This case study uses the same HotpotQA sentence-level evidence retrieval data, compare BM25, Dense, and Hybrid three methods on query level.

- Queries: `data/processed/hotpotqa/queries.jsonl`, 100 queries
- Passages: `data/processed/hotpotqa/passages.jsonl`, 4085 sentence passages
- Qrels: `data/processed/hotpotqa/qrels.jsonl`, 243 relevant query-passage labels
- Methods:
    - BM25: `k1=1.5`, `b=0.75`
    - Dense: 
        - model: `sentence-transformers/all-MiniLM-L6-v2`
        - cache: `data/cache/dense`
    - Hybrid: 
        - `alpha=0.50`
        - min-max normalization: HybridScore = alpha * normalized(BM25Score) + (1 - alpha) * normalized(DenseScore)
        - Hybrid candidate pool: BM25 top 100 union Dense top 100
- Final evaluation cutoff: top 10
- Metrics: Recall@10, MRR@10, nDCG@10

Overall top-10 results:

| Method | Recall@10 | MRR@10 | nDCG@10 |
|---|---:|---:|---:|
| BM25 | 0.632333 | 0.755694 | 0.585073 |
| Dense | 0.653167 | 0.722802 | 0.577069 |
| Hybrid alpha=0.50 | 0.722333 | 0.787853 | 0.641097 |

In the case tables below, `rank -` means the gold passage was not retrieved in top 10.

## 2. 案例信息

### Case Directory

1. BM25 wins Dense
   - Case 1: query with rare entity names and exact date evidence
   - Case 2: query with a rare title, author name, and exact phrase

2. Dense wins BM25
   - Case 3: query requiring semantic category matching
   - Case 4: query with relation paraphrase between father and son
   - Case 5: comparison query where Dense retrieves both entities

3. Both BM25 and Dense succeed
   - Case 6: query with direct lexical overlap to both gold passages
   - Case 7: query with precise keywords and clear answer relation

4. Both BM25 and Dense fail
   - Case 8: query requiring implicit calculation and attribute comparison

5. Hybrid wins
   - Case 9: BM25 and Dense retrieve complementary entity evidence
   - Case 10: BM25 finds answer evidence while Dense finds bridge evidence
   - Case 11: BM25 and Dense each recover a different partial hit

### Case 1: BM25 wins Dense on exact person names

- Query ID: `q_000009`
- Query: Who is older, Annie Morton or Terry Richardson?
- Type: bridge
- Answer: Terry Richardson
- Gold passages: `Annie Morton::0`, `Annie Morton::2`, `Terry Richardson::0`

Gold evidence sentences:

- `Annie Morton::0`: Annie Morton (born October 8, 1970) is an American model born in Pennsylvania.
- `Annie Morton::2`: She has been photographed by Helmut Newton; Peter Lindbergh; Annie Leibovitz; Richard Avedon; Juergen Teller; Paul Jasmin, Mary Ellen Mark and Terry Richardson, and modeled for Donna Karan, Givenchy, Guerlain, Chanel, "Harper's Bazaar", "Sports Illustrated" and Victoria's Secret.
- `Terry Richardson::0`: Terrence "Uncle Terry" Richardson (born August 14, 1965) is an American fashion and portrait photographer who has shot advertising campaigns for Marc Jacobs, Aldo, Supreme, Sisley, Tom Ford, and Yves Saint Laurent among others.

| Method | Recall@10 | Gold ranks |
|---|---:|---|
| BM25 | 1.000 | Annie Morton::0 rank 1, Annie Morton::2 rank 4, Terry Richardson::0 rank 5 |
| Dense | 0.333 | Annie Morton::0 rank 1, Annie Morton::2 rank -, Terry Richardson::0 rank - |
| Hybrid | 1.000 | Annie Morton::0 rank 1, Annie Morton::2 rank 4, Terry Richardson::0 rank 6 |

BM25 succeeds because the query contains rare entity names, especially `Annie Morton` and `Terry Richardson`. The relevant sentences also contain date-of-birth information and exact names, so lexical matching is very effective. Dense retrieves `Annie Morton::0`, but it drifts toward semantically related "older/sister" passages and misses the Terry Richardson evidence.

### Case 2: BM25 wins Dense on rare title and exact phrase

- Query ID: `q_000089`
- Query: How many copies of Roald Dahl's variation on a popular anecdote sold?
- Type: bridge
- Answer: 250 million
- Gold passages: `Mrs. Bixby and the Colonel's Coat::1`, `Roald Dahl::1`

Gold evidence sentences:

- `Mrs. Bixby and the Colonel's Coat::1`: The story is Dahl's variation on a popular anecdote dating back at least to 1939: a married woman receives a glamorous mink coat from a man with whom she had an affair.
- `Roald Dahl::1`: His books have sold more than 250 million copies worldwide.

| Method | Recall@10 | Gold ranks |
|---|---:|---|
| BM25 | 1.000 | Mrs. Bixby and the Colonel's Coat::1 rank 1, Roald Dahl::1 rank 6 |
| Dense | 0.000 | Mrs. Bixby and the Colonel's Coat::1 rank -, Roald Dahl::1 rank - |
| Hybrid | 1.000 | Mrs. Bixby and the Colonel's Coat::1 rank 2, Roald Dahl::1 rank 8 |

BM25 benefits from the exact phrase `variation on a popular anecdote` and the rare entity `Roald Dahl`. Dense ranks many general Roald Dahl bibliography or collection pages above the actual evidence, because those passages are semantically close to the author but do not contain the required sales evidence.

### Case 3: Dense wins BM25 on semantic category matching

- Query ID: `q_000049`
- Query: Are Ferocactus and Silene both types of plant?
- Type: comparison
- Answer: yes
- Gold passages: `Ferocactus::0`, `Silene::0`

Gold evidence sentences:

- `Ferocactus::0`: Ferocactus is a genus of large barrel-shaped cacti, mostly with large spines and small flowers.
- `Silene::0`: Silene is a genus of flowering plants in the family Caryophyllaceae.

| Method | Recall@10 | Gold ranks |
|---|---:|---|
| BM25 | 0.000 | Ferocactus::0 rank -, Silene::0 rank - |
| Dense | 1.000 | Ferocactus::0 rank 3, Silene::0 rank 1 |
| Hybrid | 1.000 | Ferocactus::0 rank 7, Silene::0 rank 10 |

BM25 over-focuses on exact `Silene` lexical matches and ranks many Silene species or related pages above the main entity passages. Dense succeeds because it captures the semantic relation between `types of plant`, `genus`, `flowering plants`, and `cacti`, so both gold entity definition sentences appear in top 3.

### Case 4: Dense wins BM25 on relation/paraphrase evidence

- Query ID: `q_000025`
- Query: What was the father of Kasper Schmeichel voted to be by the IFFHS in 1992?
- Type: bridge
- Answer: World's Best Goalkeeper
- Gold passages: `Kasper Schmeichel::0`, `Kasper Schmeichel::1`, `Peter Schmeichel::0`

Gold evidence sentences:

- `Kasper Schmeichel::0`: Kasper Peter Schmeichel (] ; born 5 November 1986) is a Danish professional footballer who plays as a goalkeeper for Premier League club Leicester City and the Denmark national team.
- `Kasper Schmeichel::1`: He is the son of former Manchester United and Danish international goalkeeper Peter Schmeichel.
- `Peter Schmeichel::0`: Peter Bolesław Schmeichel MBE (] ; born 18 November 1963) is a Danish former professional footballer who played as a goalkeeper, and was voted the IFFHS World's Best Goalkeeper in 1992 and 1993.

| Method | Recall@10 | Gold ranks |
|---|---:|---|
| BM25 | 0.667 | Kasper Schmeichel::0 rank 7, Kasper Schmeichel::1 rank -, Peter Schmeichel::0 rank 1 |
| Dense | 1.000 | Kasper Schmeichel::0 rank 2, Kasper Schmeichel::1 rank 1, Peter Schmeichel::0 rank 3 |
| Hybrid | 1.000 | Kasper Schmeichel::0 rank 3, Kasper Schmeichel::1 rank 4, Peter Schmeichel::0 rank 1 |

BM25 retrieves the answer-bearing `Peter Schmeichel::0` sentence because it contains `IFFHS`, `1992`, and `goalkeeper`. It misses the bridge sentence `Kasper Schmeichel::1`, which expresses the father relation. Dense is better here because "father of Kasper Schmeichel" maps well to the sentence saying he is the son of Peter Schmeichel.

### Case 5: Dense wins BM25 by retrieving both comparison entities

- Query ID: `q_000001`
- Query: Were Scott Derrickson and Ed Wood of the same nationality?
- Type: comparison
- Answer: yes
- Gold passages: `Scott Derrickson::0`, `Ed Wood::0`

Gold evidence sentences:

- `Ed Wood::0`: Edward Davis Wood Jr. (October 10, 1924 – December 10, 1978) was an American filmmaker, actor, writer, producer, and director.
- `Scott Derrickson::0`: Scott Derrickson (born July 16, 1966) is an American director, screenwriter and producer.

| Method | Recall@10 | Gold ranks |
|---|---:|---|
| BM25 | 0.500 | Scott Derrickson::0 rank 4, Ed Wood::0 rank - |
| Dense | 1.000 | Scott Derrickson::0 rank 2, Ed Wood::0 rank 3 |
| Hybrid | 1.000 | Scott Derrickson::0 rank 1, Ed Wood::0 rank 8 |

BM25 is distracted by passages containing surface matches such as `Ed Wood (film)` and other `Wood` terms. Dense ranks both entities needed for the nationality comparison: `Scott Derrickson::0` and `Ed Wood::0`. Hybrid keeps both gold passages, but the lexical score still allows some `Wood` distractors to rank high.

### Case 6: Both BM25 and Dense succeed with direct lexical overlap

- Query ID: `q_000004`
- Query: Are the Laleli Mosque and Esma Sultan Mansion located in the same neighborhood?
- Type: comparison
- Answer: no
- Gold passages: `Esma Sultan Mansion::0`, `Laleli Mosque::0`

Gold evidence sentences:

- `Esma Sultan Mansion::0`: The Esma Sultan Mansion (Turkish: "Esma Sultan Yalısı" ), a historical yalı (English: waterside mansion ) located at Bosphorus in Ortaköy neighborhood of Istanbul, Turkey and named after its original owner Esma Sultan, is used today as a cultural center after being redeveloped.
- `Laleli Mosque::0`: The Laleli Mosque (Turkish: "Laleli Camii, or Tulip Mosque" ) is an 18th-century Ottoman imperial mosque located in Laleli, Fatih, Istanbul, Turkey.

| Method | Recall@10 | Gold ranks |
|---|---:|---|
| BM25 | 1.000 | Esma Sultan Mansion::0 rank 1, Laleli Mosque::0 rank 2 |
| Dense | 1.000 | Esma Sultan Mansion::0 rank 1, Laleli Mosque::0 rank 2 |
| Hybrid | 1.000 | Esma Sultan Mansion::0 rank 1, Laleli Mosque::0 rank 2 |

Both methods succeed because the query names both entities exactly, and the gold passages are clean first-sentence descriptions containing the same place names and location words. Dense does not need much paraphrase ability here; the query wording and passage wording are already closely aligned.

### Case 7: Both BM25 and Dense succeed with keywords plus answer relation

- Query ID: `q_000011`
- Query: What is the name of the fight song of the university whose main campus is in Lawrence, Kansas and whose branch campuses are in the Kansas City metropolitan area?
- Type: bridge
- Answer: Kansas Song
- Gold passages: `Kansas Song::0`, `University of Kansas::1`, `University of Kansas::2`

Gold evidence sentences:

- `Kansas Song::0`: Kansas Song (We’re From Kansas) is a fight song of the University of Kansas.
- `University of Kansas::1`: The main campus in Lawrence, one of the largest college towns in Kansas, is on Mount Oread, the highest elevation in Lawrence.
- `University of Kansas::2`: Two branch campuses are in the Kansas City metropolitan area: the Edwards Campus in Overland Park, and the university's medical school and hospital in Kansas City.

| Method | Recall@10 | Gold ranks |
|---|---:|---|
| BM25 | 1.000 | Kansas Song::0 rank 3, University of Kansas::1 rank 4, University of Kansas::2 rank 1 |
| Dense | 1.000 | Kansas Song::0 rank 1, University of Kansas::1 rank 5, University of Kansas::2 rank 3 |
| Hybrid | 1.000 | Kansas Song::0 rank 2, University of Kansas::1 rank 4, University of Kansas::2 rank 1 |

BM25 succeeds because `fight song`, `Lawrence`, `Kansas`, `branch campuses`, and `Kansas City metropolitan area` appear directly in the gold evidence. Dense also succeeds because the semantic structure is clear: identify the university from campus clues, then retrieve its fight song.

### Case 8: Both BM25 and Dense fail because the query requires implicit calculation

- Query ID: `q_000024`
- Query: Which performance act has a higher instrument to person ratio, Badly Drawn Boy or Wolf Alice?
- Type: comparison
- Answer: Badly Drawn Boy
- Gold passages: `Badly Drawn Boy::0`, `Wolf Alice::1`

Gold evidence sentences:

- `Badly Drawn Boy::0`: Damon Michael Gough (born 2 October 1969, in Dunstable, Bedfordshire), known by the stage name Badly Drawn Boy, is an English indie singer-songwriter and multi-instrumentalist.
- `Wolf Alice::1`: Its members since 2012 are Ellie Rowsell (vocals, guitar), Joff Oddie (guitars, vocals), Theo Ellis (bass), and Joel Amey (drums, vocals).

| Method | Recall@10 | Gold ranks |
|---|---:|---|
| BM25 | 0.000 | Badly Drawn Boy::0 rank -, Wolf Alice::1 rank - |
| Dense | 0.000 | Badly Drawn Boy::0 rank -, Wolf Alice::1 rank - |
| Hybrid | 0.500 | Badly Drawn Boy::0 rank 7, Wolf Alice::1 rank - |

This is mainly a failure case for implicit calculation and attribute comparison. The query does not directly ask for member count or instrument count, but `instrument-to-person ratio` implies that the retriever needs evidence about both attributes for both acts. `Badly Drawn Boy::0` supports that Badly Drawn Boy is one person and a multi-instrumentalist, while `Wolf Alice::1` gives the member list for Wolf Alice. BM25 retrieves songs, albums, and generic Wolf Alice passages because they share surface music words. Dense also stays near music-related passages but does not reliably select the exact evidence needed for the ratio comparison. Hybrid partially recovers `Badly Drawn Boy::0`, but it still misses `Wolf Alice::1`, so this remains a good example of implicit calculation being hard for retrieval-only methods.

### Case 9: Hybrid succeeds because BM25 and Dense find complementary evidence

- Query ID: `q_000010`
- Query: Are Local H and For Against both from the United States?
- Type: comparison
- Answer: yes
- Gold passages: `For Against::0`, `Local H::0`

Gold evidence sentences:

- `For Against::0`: For Against is a United States post-punk/dream pop band from Lincoln, Nebraska.
- `Local H::0`: Local H is an American rock band originally formed by guitarist and vocalist Scott Lucas, bassist Matt Garcia, drummer Joe Daniels, and lead guitarist John Sparkman in Zion, Illinois in 1987.

| Method | Recall@10 | Gold ranks |
|---|---:|---|
| BM25 | 0.500 | For Against::0 rank 1, Local H::0 rank - |
| Dense | 0.500 | For Against::0 rank -, Local H::0 rank 2 |
| Hybrid | 1.000 | For Against::0 rank 1, Local H::0 rank 4 |

This is a clear Hybrid success case. BM25 finds `For Against::0` because it contains the exact phrase `United States`, but misses `Local H::0`, which says `American` instead. Dense finds `Local H::0` because `American` is semantically equivalent to "from the United States", but misses `For Against::0`. Hybrid combines the two complementary candidate lists and retrieves both gold passages in top 10.

### Case 10: Hybrid succeeds by combining bridge evidence and answer evidence

- Query ID: `q_000070`
- Query: The 2017–18 Wigan Athletic F.C. season will be a year in which the team competes in the league cup known as what for sponsorship reasons?
- Type: bridge
- Answer: Carabao Cup
- Gold passages: `2017–18 Wigan Athletic F.C. season::1`, `EFL Cup::0`

Gold evidence sentences:

- `2017–18 Wigan Athletic F.C. season::1`: Along with competing in the league, the club will also participate in the FA Cup, EFL Cup and EFL Trophy.
- `EFL Cup::0`: The EFL Cup (referred to historically, and colloquially, as simply the League Cup), currently known as the Carabao Cup for sponsorship reasons, is an annual knockout football competition in men's domestic English football.

| Method | Recall@10 | Gold ranks |
|---|---:|---|
| BM25 | 0.500 | 2017–18 Wigan Athletic F.C. season::1 rank -, EFL Cup::0 rank 6 |
| Dense | 0.500 | 2017–18 Wigan Athletic F.C. season::1 rank 5, EFL Cup::0 rank - |
| Hybrid | 1.000 | 2017–18 Wigan Athletic F.C. season::1 rank 10, EFL Cup::0 rank 8 |

This case emphasizes Hybrid success, not base-method failure. BM25 finds the `EFL Cup` answer passage because it contains `League Cup` and `sponsorship reasons`, but it misses the Wigan season bridge sentence. Dense finds the Wigan season bridge sentence because it is semantically close to the season/competition description, but it misses `EFL Cup::0`. Hybrid combines these complementary hits and places both required evidence sentences in top 10.

### Case 11: Hybrid succeeds by combining two partial hits

- Query ID: `q_000013`
- Query: What year did Guns N Roses perform a promo for a movie starring Arnold Schwarzenegger as a former New York Police detective?
- Type: bridge
- Answer: 1999
- Gold passages: `End of Days (film)::1`, `Oh My God (Guns N' Roses song)::0`, `Oh My God (Guns N' Roses song)::1`

Gold evidence sentences:

- `End of Days (film)::1`: The film follows former New York Police Department detective Jericho Cane (Schwarzenegger) after he saves a banker (Byrne) from an assassin, finds himself embroiled in a religious conflict, and must protect an innocent young woman (Tunney) who is chosen by evil forces to conceive the Antichrist with Satan.
- `Oh My God (Guns N' Roses song)::0`: "Oh My God" is a song by Guns N' Roses released in 1999 on the soundtrack to the film "End of Days".
- `Oh My God (Guns N' Roses song)::1`: The song was sent out to radio stations in November 1999 as a promo for the soundtrack and the band.

| Method | Recall@10 | Gold ranks |
|---|---:|---|
| BM25 | 0.333 | End of Days (film)::1 rank 5, Oh My God (Guns N' Roses song)::0 rank -, Oh My God (Guns N' Roses song)::1 rank - |
| Dense | 0.333 | End of Days (film)::1 rank -, Oh My God (Guns N' Roses song)::0 rank 7, Oh My God (Guns N' Roses song)::1 rank - |
| Hybrid | 0.667 | End of Days (film)::1 rank 10, Oh My God (Guns N' Roses song)::0 rank 7, Oh My God (Guns N' Roses song)::1 rank - |

This case shows Hybrid improving an incomplete retrieval result. BM25 focuses on the movie description with `Arnold Schwarzenegger` and `New York Police detective`, retrieving `End of Days (film)::1`. Dense retrieves the song evidence `Oh My God (Guns N' Roses song)::0` because `Guns N' Roses`, soundtrack, and promo are semantically connected. Hybrid combines those two partial hits and improves Recall@10 from 0.333 to 0.667, although it still misses the second song sentence `Oh My God (Guns N' Roses song)::1`.

## 3. 发现和总结

1. BM25 is strongest when the query contains rare exact strings, such as entity names, dates, titles, and exact phrases. In Case 1 and Case 2, BM25 works well because the gold evidence repeats distinctive surface forms like `Annie Morton`, `Terry Richardson`, `Roald Dahl`, and `variation on a popular anecdote`.

2. Dense retrieval is stronger when the query and evidence use different wording but share the same meaning. In Case 3, Dense connects `types of plant` with entity definition sentences containing `genus`, `flowering plants`, and `cacti`. In Case 4, it handles the relation paraphrase between `father of Kasper Schmeichel` and `son of ... Peter Schmeichel`.

3. When the query directly overlaps with the gold passages, both BM25 and Dense can succeed. Case 6 is mostly direct lexical overlap: the query names both entities and the gold passages contain the same place names and location words. Case 7 also has strong keywords such as `fight song`, `Lawrence`, `Kansas`, and `Kansas City metropolitan area`.

4. The clearest shared failure is Case 8. It is not mainly a keyword problem or a semantic similarity problem; it requires implicit calculation and attribute comparison. The query asks for an `instrument-to-person ratio`, so the retriever would need evidence about member count and instrument use for both acts. BM25 and Dense retrieve music-related passages, but neither reliably selects both exact evidence sentences needed for the comparison.

5. Hybrid alpha=0.50 is useful when BM25 and Dense find complementary evidence. In Case 9, BM25 finds the `United States` passage while Dense finds the `American` passage. In Case 10, BM25 finds the answer evidence and Dense finds the bridge evidence. In Case 11, BM25 and Dense each recover a different partial hit. Hybrid improves the final ranking by merging these candidate lists, but it is still not a reasoning model and can still miss evidence when neither base retriever ranks it strongly enough.
