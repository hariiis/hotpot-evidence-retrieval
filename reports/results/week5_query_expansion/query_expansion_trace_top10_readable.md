# Query Expansion Trace Top 10

## 1. q_000001

```json
{
  "query_id": "q_000001",
  "type": "comparison",
  "original_query": "Were Scott Derrickson and Ed Wood of the same nationality?",
  "gold_passage_ids": [
    "Scott Derrickson::0",
    "Ed Wood::0"
  ],
  "answer": "yes",
  "query_concepts": [
    "scott derrickson",
    "ed wood",
    "nationality"
  ],
  "matched_graph_nodes": [
    "scott derrickson",
    "ed wood",
    "nationality"
  ],
  "unmatched_query_concepts": [],
  "expanded_concepts": [
    {
      "concept": "american",
      "score": 3,
      "hop": 1
    },
    {
      "concept": "c robert cargill",
      "score": 2,
      "hop": 1
    },
    {
      "concept": "film",
      "score": 2,
      "hop": 1
    },
    {
      "concept": "1960s",
      "score": 1,
      "hop": 1
    },
    {
      "concept": "1970s",
      "score": 1,
      "hop": 1
    }
  ],
  "expanded_query": "Were Scott Derrickson and Ed Wood of the same nationality? american c robert cargill film 1960s 1970s",
  "gold_concepts": [
    "scott derrickson",
    "july 16 1966",
    "american",
    "american director",
    "screenwriter",
    "producer",
    "edward davis wood jr",
    "october 10 1924",
    "december 10 1978",
    "october",
    "december",
    "american filmmaker",
    "actor",
    "writer",
    "director"
  ],
  "query_gold_overlap": [
    "scott derrickson"
  ],
  "expanded_gold_overlap": [
    "american"
  ]
}
```

## 2. q_000002

```json
{
  "query_id": "q_000002",
  "type": "bridge",
  "original_query": "What government position was held by the woman who portrayed Corliss Archer in the film Kiss and Tell?",
  "gold_passage_ids": [
    "Kiss and Tell (1945 film)::0",
    "Shirley Temple::0",
    "Shirley Temple::1"
  ],
  "answer": "Chief of Protocol",
  "query_concepts": [
    "corliss archer",
    "kiss tell",
    "government position",
    "woman",
    "film",
    "kiss"
  ],
  "matched_graph_nodes": [
    "corliss archer",
    "kiss tell",
    "woman",
    "film",
    "kiss"
  ],
  "unmatched_query_concepts": [
    "government position"
  ],
  "expanded_concepts": [
    {
      "concept": "1945",
      "score": 4,
      "hop": 1
    },
    {
      "concept": "american",
      "score": 4,
      "hop": 1
    },
    {
      "concept": "life",
      "score": 4,
      "hop": 1
    },
    {
      "concept": "soundtrack",
      "score": 4,
      "hop": 1
    },
    {
      "concept": "book",
      "score": 3,
      "hop": 1
    }
  ],
  "expanded_query": "What government position was held by the woman who portrayed Corliss Archer in the film Kiss and Tell? 1945 american life soundtrack book",
  "gold_concepts": [
    "kiss",
    "tell",
    "1945",
    "american",
    "17 year old",
    "shirley temple",
    "corliss archer",
    "1945 american comedy film",
    "17 year old shirley temple",
    "shirley temple black",
    "april 23 1928",
    "february 10 2014",
    "hollywood",
    "1935",
    "april",
    "february",
    "american actress",
    "singer",
    "dancer",
    "businesswoman",
    "diplomat",
    "hollywood's number box office draw",
    "child actress",
    "united states",
    "ghana",
    "czechoslovakia",
    "adult",
    "united states ambassador",
    "chief",
    "protocol"
  ],
  "query_gold_overlap": [
    "corliss archer",
    "kiss"
  ],
  "expanded_gold_overlap": [
    "1945",
    "american"
  ]
}
```

## 3. q_000003

```json
{
  "query_id": "q_000003",
  "type": "bridge",
  "original_query": "What science fantasy young adult series, told in first person, has a set of companion books narrating the stories of enslaved worlds and alien species?",
  "gold_passage_ids": [
    "The Hork-Bajir Chronicles::0",
    "The Hork-Bajir Chronicles::1",
    "The Hork-Bajir Chronicles::2",
    "Animorphs::0",
    "Animorphs::1"
  ],
  "answer": "Animorphs",
  "query_concepts": [
    "science fantasy young adult series",
    "person",
    "set",
    "companion books",
    "stories",
    "enslaved worlds",
    "alien species"
  ],
  "matched_graph_nodes": [
    "person",
    "set",
    "companion books",
    "stories"
  ],
  "unmatched_query_concepts": [
    "science fantasy young adult series",
    "enslaved worlds",
    "alien species"
  ],
  "expanded_concepts": [
    {
      "concept": "assistant secretaries",
      "score": 2,
      "hop": 1
    },
    {
      "concept": "books",
      "score": 2,
      "hop": 1
    },
    {
      "concept": "united states",
      "score": 2,
      "hop": 1
    },
    {
      "concept": "1917",
      "score": 1,
      "hop": 1
    },
    {
      "concept": "2011",
      "score": 1,
      "hop": 1
    }
  ],
  "expanded_query": "What science fantasy young adult series, told in first person, has a set of companion books narrating the stories of enslaved worlds and alien species? assistant secretaries books united states 1917 2011",
  "gold_concepts": [
    "second",
    "k applegate",
    "hork bajir chronicles",
    "second companion book",
    "animorphs series",
    "23",
    "pretender",
    "ellimist chronicles",
    "andalite chronicles",
    "respect",
    "continuity",
    "series",
    "place",
    "book",
    "events",
    "story",
    "time",
    "tobias",
    "jara hamee",
    "yeerks",
    "hork bajir",
    "aldrea",
    "andalite",
    "dak hamee",
    "valley",
    "free hork bajir",
    "companion",
    "world",
    "invasion",
    "katherine applegate",
    "michael grant",
    "scholastic",
    "animorphs",
    "science fantasy series",
    "young adult books",
    "husband",
    "person",
    "main characters",
    "turns",
    "books",
    "perspectives"
  ],
  "query_gold_overlap": [
    "person"
  ],
  "expanded_gold_overlap": [
    "books"
  ]
}
```

## 4. q_000004

```json
{
  "query_id": "q_000004",
  "type": "comparison",
  "original_query": "Are the Laleli Mosque and Esma Sultan Mansion located in the same neighborhood?",
  "gold_passage_ids": [
    "Laleli Mosque::0",
    "Esma Sultan Mansion::0"
  ],
  "answer": "no",
  "query_concepts": [
    "laleli mosque",
    "esma",
    "sultan mansion",
    "laleli mosque esma sultan mansion",
    "neighborhood"
  ],
  "matched_graph_nodes": [
    "laleli mosque",
    "esma"
  ],
  "unmatched_query_concepts": [
    "sultan mansion",
    "laleli mosque esma sultan mansion",
    "neighborhood"
  ],
  "expanded_concepts": [
    {
      "concept": "esma sultan",
      "score": 3,
      "hop": 1
    },
    {
      "concept": "ottoman",
      "score": 3,
      "hop": 1
    },
    {
      "concept": "18th century",
      "score": 1,
      "hop": 1
    },
    {
      "concept": "18th century ottoman imperial mosque",
      "score": 1,
      "hop": 1
    },
    {
      "concept": "bridegroom",
      "score": 1,
      "hop": 1
    }
  ],
  "expanded_query": "Are the Laleli Mosque and Esma Sultan Mansion located in the same neighborhood? esma sultan ottoman 18th century 18th century ottoman imperial mosque bridegroom",
  "gold_concepts": [
    "laleli mosque",
    "turkish",
    "laleli camii",
    "tulip mosque",
    "18th century",
    "ottoman",
    "laleli",
    "fatih",
    "istanbul",
    "turkey",
    "18th century ottoman imperial mosque",
    "laleli fatih istanbul turkey",
    "english",
    "bosphorus ortak y",
    "esma sultan",
    "today",
    "esma sultan mansion",
    "esma sultan yal s",
    "historical yal",
    "waterside mansion",
    "bosphorus",
    "ortak y neighborhood",
    "original owner",
    "cultural center"
  ],
  "query_gold_overlap": [
    "laleli mosque"
  ],
  "expanded_gold_overlap": [
    "esma sultan",
    "ottoman",
    "18th century",
    "18th century ottoman imperial mosque"
  ]
}
```

## 5. q_000005

```json
{
  "query_id": "q_000005",
  "type": "bridge",
  "original_query": "The director of the romantic comedy \"Big Stone Gap\" is based in what New York city?",
  "gold_passage_ids": [
    "Big Stone Gap (film)::0",
    "Adriana Trigiani::0"
  ],
  "answer": "Greenwich Village, New York City",
  "query_concepts": [
    "big stone gap",
    "new york",
    "director",
    "romantic comedy",
    "new york city"
  ],
  "matched_graph_nodes": [
    "big stone gap",
    "new york",
    "director",
    "new york city"
  ],
  "unmatched_query_concepts": [
    "romantic comedy"
  ],
  "expanded_concepts": [
    {
      "concept": "american",
      "score": 10,
      "hop": 1
    },
    {
      "concept": "united states",
      "score": 8,
      "hop": 1
    },
    {
      "concept": "national intelligence",
      "score": 5,
      "hop": 1
    },
    {
      "concept": "paris",
      "score": 5,
      "hop": 1
    },
    {
      "concept": "producer",
      "score": 5,
      "hop": 1
    }
  ],
  "expanded_query": "The director of the romantic comedy \"Big Stone Gap\" is based in what New York city? american united states national intelligence paris producer",
  "gold_concepts": [
    "big stone gap",
    "2014",
    "american",
    "adriana trigiani",
    "donna gigliotti",
    "altar identity studios",
    "media society",
    "2014 american drama romantic comedy film",
    "subsidiary",
    "italian",
    "sixteen",
    "greenwich village",
    "new york city",
    "italian american best selling author",
    "sixteen books",
    "television writer",
    "film director",
    "entrepreneur"
  ],
  "query_gold_overlap": [
    "big stone gap",
    "new york city"
  ],
  "expanded_gold_overlap": [
    "american"
  ]
}
```

## 6. q_000006

```json
{
  "query_id": "q_000006",
  "type": "bridge",
  "original_query": "2014 S/S is the debut album of a South Korean boy group that was formed by who?",
  "gold_passage_ids": [
    "2014 S/S::0",
    "Winner (band)::0"
  ],
  "answer": "YG Entertainment",
  "query_concepts": [
    "s s",
    "south korean",
    "2014 s s",
    "debut album",
    "south korean boy group"
  ],
  "matched_graph_nodes": [
    "s s",
    "south korean",
    "2014 s s",
    "debut album",
    "south korean boy group"
  ],
  "unmatched_query_concepts": [],
  "expanded_concepts": [
    {
      "concept": "2013",
      "score": 4,
      "hop": 1
    },
    {
      "concept": "2014",
      "score": 4,
      "hop": 1
    },
    {
      "concept": "2015",
      "score": 4,
      "hop": 1
    },
    {
      "concept": "hangul",
      "score": 4,
      "hop": 1
    },
    {
      "concept": "korean",
      "score": 4,
      "hop": 1
    }
  ],
  "expanded_query": "2014 S/S is the debut album of a South Korean boy group that was formed by who? 2013 2014 2015 hangul korean",
  "gold_concepts": [
    "s s",
    "south korean",
    "2014 s s",
    "debut album",
    "south korean group winner",
    "2013",
    "yg entertainment",
    "2014",
    "winner",
    "hangul",
    "south korean boy group"
  ],
  "query_gold_overlap": [
    "s s",
    "south korean",
    "2014 s s",
    "debut album",
    "south korean boy group"
  ],
  "expanded_gold_overlap": [
    "2013",
    "2014",
    "hangul"
  ]
}
```

## 7. q_000007

```json
{
  "query_id": "q_000007",
  "type": "bridge",
  "original_query": "Who was known by his stage name Aladin and helped organizations improve their performance as a consultant?",
  "gold_passage_ids": [
    "Eenasul Fateh::0",
    "Management consulting::0"
  ],
  "answer": "Eenasul Fateh",
  "query_concepts": [
    "aladin",
    "stage",
    "organizations",
    "performance",
    "consultant"
  ],
  "matched_graph_nodes": [
    "aladin",
    "stage",
    "organizations",
    "performance",
    "consultant"
  ],
  "unmatched_query_concepts": [],
  "expanded_concepts": [
    {
      "concept": "american",
      "score": 4,
      "hop": 1
    },
    {
      "concept": "record producer",
      "score": 3,
      "hop": 1
    },
    {
      "concept": "23 1977",
      "score": 2,
      "hop": 1
    },
    {
      "concept": "3 april 1959",
      "score": 2,
      "hop": 1
    },
    {
      "concept": "album",
      "score": 2,
      "hop": 1
    }
  ],
  "expanded_query": "Who was known by his stage name Aladin and helped organizations improve their performance as a consultant? american record producer 23 1977 3 april 1959 album",
  "gold_concepts": [
    "eenasul fateh",
    "bengali",
    "3 april 1959",
    "aladin",
    "bangladeshi",
    "magician",
    "stage",
    "bangladeshi british cultural practitioner",
    "live artist",
    "international management consultant",
    "management consulting",
    "practice",
    "organizations",
    "performance",
    "analysis",
    "existing organizational problems",
    "development",
    "plans",
    "improvement"
  ],
  "query_gold_overlap": [
    "aladin",
    "stage",
    "organizations",
    "performance"
  ],
  "expanded_gold_overlap": [
    "3 april 1959"
  ]
}
```

## 8. q_000008

```json
{
  "query_id": "q_000008",
  "type": "bridge",
  "original_query": "The arena where the Lewiston Maineiacs played their home games can seat how many people?",
  "gold_passage_ids": [
    "Lewiston Maineiacs::1",
    "Androscoggin Bank Colisée::0"
  ],
  "answer": "3,677 seated",
  "query_concepts": [
    "arena",
    "lewiston maineiacs",
    "home games",
    "people"
  ],
  "matched_graph_nodes": [
    "arena",
    "lewiston maineiacs",
    "home games",
    "people"
  ],
  "unmatched_query_concepts": [],
  "expanded_concepts": [
    {
      "concept": "members",
      "score": 12,
      "hop": 1
    },
    {
      "concept": "buffaloes",
      "score": 8,
      "hop": 1
    },
    {
      "concept": "boulder",
      "score": 7,
      "hop": 1
    },
    {
      "concept": "pac 12 conference",
      "score": 7,
      "hop": 1
    },
    {
      "concept": "america east conference",
      "score": 6,
      "hop": 1
    }
  ],
  "expanded_query": "The arena where the Lewiston Maineiacs played their home games can seat how many people? members buffaloes boulder pac 12 conference america east conference",
  "gold_concepts": [
    "androscoggin bank colis e",
    "team",
    "home games",
    "central maine",
    "lewiston colisee",
    "4 000",
    "3 677",
    "lewiston",
    "maine",
    "1958",
    "central maine civic center",
    "4 000 capacity",
    "multi purpose arena"
  ],
  "query_gold_overlap": [
    "home games"
  ],
  "expanded_gold_overlap": []
}
```

## 9. q_000009

```json
{
  "query_id": "q_000009",
  "type": "bridge",
  "original_query": "Who is older, Annie Morton or Terry Richardson?",
  "gold_passage_ids": [
    "Annie Morton::0",
    "Annie Morton::2",
    "Terry Richardson::0"
  ],
  "answer": "Terry Richardson",
  "query_concepts": [
    "annie morton",
    "terry richardson"
  ],
  "matched_graph_nodes": [
    "annie morton",
    "terry richardson"
  ],
  "unmatched_query_concepts": [],
  "expanded_concepts": [
    {
      "concept": "american",
      "score": 3,
      "hop": 1
    },
    {
      "concept": "film",
      "score": 2,
      "hop": 1
    },
    {
      "concept": "juergen teller",
      "score": 2,
      "hop": 1
    },
    {
      "concept": "marc jacobs",
      "score": 2,
      "hop": 1
    },
    {
      "concept": "peter lindbergh",
      "score": 2,
      "hop": 1
    }
  ],
  "expanded_query": "Who is older, Annie Morton or Terry Richardson? american film juergen teller marc jacobs peter lindbergh",
  "gold_concepts": [
    "annie morton",
    "october 8 1970",
    "american",
    "pennsylvania",
    "american model",
    "helmut newton",
    "peter lindbergh",
    "annie leibovitz",
    "richard avedon",
    "juergen teller",
    "paul jasmin",
    "mary ellen mark",
    "terry richardson",
    "donna karan",
    "guerlain",
    "chanel",
    "harper's bazaar",
    "sports illustrated",
    "victoria's secret",
    "givenchy",
    "august 14 1965",
    "marc jacobs",
    "aldo",
    "supreme",
    "sisley",
    "tom ford",
    "yves saint laurent",
    "terrence uncle terry richardson",
    "american fashion",
    "portrait photographer",
    "advertising campaigns"
  ],
  "query_gold_overlap": [
    "annie morton",
    "terry richardson"
  ],
  "expanded_gold_overlap": [
    "american",
    "juergen teller",
    "marc jacobs",
    "peter lindbergh"
  ]
}
```

## 10. q_000010

```json
{
  "query_id": "q_000010",
  "type": "comparison",
  "original_query": "Are Local H and For Against both from the United States?",
  "gold_passage_ids": [
    "Local H::0",
    "For Against::0"
  ],
  "answer": "yes",
  "query_concepts": [
    "local h",
    "united states"
  ],
  "matched_graph_nodes": [
    "local h",
    "united states"
  ],
  "unmatched_query_concepts": [],
  "expanded_concepts": [
    {
      "concept": "united kingdom",
      "score": 7,
      "hop": 1
    },
    {
      "concept": "canada",
      "score": 5,
      "hop": 1
    },
    {
      "concept": "president",
      "score": 5,
      "hop": 1
    },
    {
      "concept": "senate",
      "score": 5,
      "hop": 1
    },
    {
      "concept": "virginia",
      "score": 5,
      "hop": 1
    }
  ],
  "expanded_query": "Are Local H and For Against both from the United States? united kingdom canada president senate virginia",
  "gold_concepts": [
    "american",
    "scott lucas",
    "matt garcia",
    "joe daniels",
    "john sparkman",
    "zion",
    "illinois",
    "1987",
    "local h",
    "american rock band",
    "guitarist",
    "bassist matt garcia",
    "drummer joe daniels",
    "lead guitarist john sparkman",
    "united states",
    "lincoln",
    "nebraska",
    "united states post punk dream pop band"
  ],
  "query_gold_overlap": [
    "local h",
    "united states"
  ],
  "expanded_gold_overlap": []
}
```
