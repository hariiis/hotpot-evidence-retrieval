# BM25 Failure + Successful Case Analysis

## Complete Failures

Queries with `recall_at_10 = 0.0`:

- q_000008
- q_000022
- q_000024
- q_000042
- q_000049
- q_000060
- q_000071

## Successful Example 1: q_000004

Query:

Are the Laleli Mosque and Esma Sultan Mansion located in the same neighborhood?

Gold passage IDs:

- Laleli Mosque::0
- Esma Sultan Mansion::0

BM25 Top-10 passage IDs:

- Esma Sultan Mansion::0
- Laleli Mosque::0
- Sultan Ahmed Mosque::0
- Esma Sultan (daughter of Abdul Hamid I)::0
- Esma Sultan::0
- Gevheri Kadın::1
- Esma Sultan (daughter of Ahmed III)::0
- Küçük Hüseyin Pasha::1
- Djamaâ el Kebir::0
- Sultan Ahmed Mosque::1

Why BM25 succeeded:

Both gold passages contain the exact entity names from the query, and both include strong location terms such as "located", "Istanbul", and the relevant place names. Because the question's evidence is concentrated in the first sentence of each entity page, lexical matching is enough to rank both gold passages at positions 1 and 2.

## Successful Example 2: q_000011

Query:

What is the name of the fight song of the university whose main campus is in Lawrence, Kansas and whose branch campuses are in the Kansas City metropolitan area?

Gold passage IDs:

- Kansas Song::0
- University of Kansas::1
- University of Kansas::2

BM25 Top-10 passage IDs:

- University of Kansas::2
- University of Missouri–Kansas City::0
- Kansas Song::0
- University of Kansas::1
- Downtown Kansas City::0
- Kansas City metropolitan area::0
- North Kansas City, Missouri::0
- University of Missouri–Kansas City::1
- University of the Incarnate Word::0
- Kansas City jazz::0

Why BM25 succeeded:

The query uses highly specific lexical anchors: "fight song", "University", "Lawrence", "Kansas", "branch campuses", and "Kansas City metropolitan area". Those terms appear directly in the gold evidence sentences, so BM25 retrieves all three required passages within the top 4 even though one distractor, University of Missouri–Kansas City::0, also shares many Kansas City terms.

## Failure Example 1: q_000008

Query:

The arena where the Lewiston Maineiacs played their home games can seat how many people?

Gold passage IDs:

- Lewiston Maineiacs::1
- Androscoggin Bank Colisée::0

BM25 Top-10 passage IDs:

- Billings Bulls::1
- Case Gym::4
- 2006–07 QMJHL season::3
- Billings Bulls::2
- 2009–10 VCU Rams men's basketball team::2
- Dwyer Arena::1
- Case Gym::5
- 2009 Colorado Buffaloes football team::1
- 2012–13 VCU Rams men's basketball team::2
- 2013–14 VCU Rams men's basketball team::2

Why BM25 failed:

BM25 matched surface words such as "home games", "arena", and "Lewiston Maineiacs", but it did not bridge from the team sentence to the arena entity "Androscoggin Bank Colisée". The gold answer requires retrieving both the team-home-arena sentence and the arena-capacity sentence, but the capacity sentence has limited direct overlap with the full query.

## Failure Example 2: q_000042

Query:

Where is the company that Sachin Warrier worked for as a software engineer headquartered?

Gold passage IDs:

- Sachin Warrier::3
- Tata Consultancy Services::0

BM25 Top-10 passage IDs:

- Alec Muffett::2
- Wes McKinney::3
- Clean Power Finance::0
- Sachin Bansal::0
- Sachin Warrier::0
- Lead programmer::0
- William Connolley::2
- Muthuchippi Poloru::2
- Wes McKinney::4
- Lead programmer::1

Why BM25 failed:

The query contains generic terms like "software engineer", "company", and "headquartered", which retrieve other software-company passages. BM25 does not infer that the missing bridge entity is "Tata Consultancy Services" from the Sachin Warrier evidence sentence, so the gold headquarters passage is not recovered in the top 10.
