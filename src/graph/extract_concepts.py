"""
Extract graph-ready concepts from processed HotpotQA queries and passages.

This script reads:
- data/processed/hotpotqa/queries.jsonl
- data/processed/hotpotqa/passages.jsonl

It uses spaCy to extract two concept sources from each text:
(1) named entities from doc.ents
(2) noun phrases from doc.noun_chunks

Concepts are normalized with a small rule-based pipeline: lowercase, remove
most punctuation, remove stop words, remove concepts that are too short, and
deduplicate repeated concepts within the same text. The main outputs are:
- data/processed/concepts/query_concepts.jsonl
- data/processed/concepts/passage_concepts.jsonl

Use --debug to also write records with raw concept text, normalized concept,
and source type for error analysis.
"""

import argparse
import re
import sys
from pathlib import Path

import spacy
from spacy.lang.en.stop_words import STOP_WORDS


PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(PROJECT_ROOT / "src"))

from utils.file_io import load_jsonl, write_jsonl


TOKEN_PATTERN = re.compile(r"[a-z0-9]+(?:'[a-z0-9]+)?")


def normalize_concept(text, min_chars):
    """Normalize one raw entity or noun phrase into a graph concept string."""
    text = text.lower().strip()

    # Keep apostrophes inside words so names such as "Arthur's" remain readable.
    tokens = TOKEN_PATTERN.findall(text)
    tokens = [token for token in tokens if token not in STOP_WORDS]

    normalized = " ".join(tokens).strip()

    if len(normalized) < min_chars:
        return None

    return normalized


def add_candidate(candidates, seen, raw_text, source_type, min_chars):
    """Normalize and append one concept candidate if it has not appeared yet."""
    normalized = normalize_concept(raw_text, min_chars)

    if not normalized or normalized in seen:
        return

    seen.add(normalized)
    candidates.append(
        {
            "raw_text": raw_text,
            "normalized": normalized,
            "source_type": source_type,
        }
    )


def extract_concepts_from_doc(doc, min_chars):
    """Extract deduplicated normalized concepts and debug details from one Doc."""
    candidates = []
    seen = set()

    # Named entities capture people, places, organizations, dates, works, etc.
    for ent in doc.ents:
        add_candidate(candidates, seen, ent.text, "named_entity", min_chars)

    # Noun chunks capture common noun phrases such as roles and object classes.
    for chunk in doc.noun_chunks:
        add_candidate(candidates, seen, chunk.text, "noun_phrase", min_chars)

    concepts = [candidate["normalized"] for candidate in candidates]

    return concepts, candidates


def process_records(records, id_field, text_field, nlp, batch_size, min_chars):
    """Run spaCy over input records and build concept plus debug output rows."""

    # Store the simplified concept-extraction results for each record.
    concept_records = []
    # Store detailed extraction information for inspection and debugging.
    debug_records = []
    texts = (record[text_field] for record in records)

    for record, doc in zip(records, nlp.pipe(texts, batch_size=batch_size)):
        concepts, debug_concepts = extract_concepts_from_doc(doc, min_chars)

        concept_records.append(
            {
                id_field: record[id_field],
                "concepts": concepts,
            }
        )
        debug_records.append(
            {
                id_field: record[id_field],
                "text": record[text_field],
                "concepts": debug_concepts,
            }
        )

    return concept_records, debug_records


def parse_args():
    """Parse command-line arguments for concept extraction paths and settings."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--queries", default="data/processed/hotpotqa/queries.jsonl")
    parser.add_argument("--passages", default="data/processed/hotpotqa/passages.jsonl")
    parser.add_argument(
        "--query_output",
        default="data/processed/concepts/query_concepts.jsonl",
    )
    parser.add_argument(
        "--passage_output",
        default="data/processed/concepts/passage_concepts.jsonl",
    )
    parser.add_argument(
        "--query_debug_output",
        default="data/processed/concepts/query_concepts_debug.jsonl",
    )
    parser.add_argument(
        "--passage_debug_output",
        default="data/processed/concepts/passage_concepts_debug.jsonl",
    )
    parser.add_argument("--model", default="en_core_web_sm")
    parser.add_argument("--batch_size", type=int, default=100)
    parser.add_argument("--min_chars", type=int, default=2)

    # Add a --debug flag; it is False by default and becomes True when included.
    parser.add_argument("--debug", action="store_true")

    return parser.parse_args()


def main():
    """Load data, extract concepts, and write JSONL outputs."""
    args = parse_args()
    nlp = spacy.load(args.model)

    queries = load_jsonl(args.queries)
    passages = load_jsonl(args.passages)

    query_concepts, query_debug = process_records(
        records=queries,
        id_field="query_id",
        text_field="query",
        nlp=nlp,
        batch_size=args.batch_size,
        min_chars=args.min_chars,
    )
    passage_concepts, passage_debug = process_records(
        records=passages,
        id_field="passage_id",
        text_field="passage_text",
        nlp=nlp,
        batch_size=args.batch_size,
        min_chars=args.min_chars,
    )

    write_jsonl(query_concepts, args.query_output)
    write_jsonl(passage_concepts, args.passage_output)

    if args.debug:
        write_jsonl(query_debug, args.query_debug_output)
        write_jsonl(passage_debug, args.passage_debug_output)

    print(f"Wrote query concepts to {args.query_output}")
    print(f"Wrote passage concepts to {args.passage_output}")
    print(f"num_queries: {len(query_concepts)}")
    print(f"num_passages: {len(passage_concepts)}")

    if args.debug:
        print(f"Wrote query concept debug records to {args.query_debug_output}")
        print(f"Wrote passage concept debug records to {args.passage_debug_output}")


if __name__ == "__main__":
    main()
