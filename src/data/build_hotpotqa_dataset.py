"""
Build a sentence-level evidence retrieval dataset from HotpotQA.

This script reads a HotpotQA raw JSON file and converts it into
three JSONL files used for evidence-retrieval experiments, plus 
one text file that records the latest run settings.

1. queries.jsonl
   - Data structure: list of dicts, one dict per query.
   - Contents: query_id, question text, answer, and question type.

2. passages.jsonl
   - Data structure: dict keyed by passage_id; each value is a passage dict.
   - Contents: passage_id, title, sentence_index, and sentence-level passage_text.

3. qrels.jsonl
   - Data structure: list of dicts, one dict per query-passage relevance label.
   - Contents: query_id, gold passage_id, and relevance score.

4. latest_run.txt
   - Contents: latest input path, output directory, num_examples, 
    mode, output file paths, and summary statistics.

Retrieval setting:
- retrieval unit: sentence
- relevance = 1 means the passage is a gold evidence sentence
- Gold evidence comes from HotpotQA supporting_facts.

Supported passage pool modes:
- mode = pooled:
    passage_id = title::sentence_index
    passages from all questions are merged into one shared passage pool.
- mode = per_question:
    passage_id = query_id::title::sentence_index
    each question keeps its own context-specific passage pool.
"""

import json
import os
import argparse
from datetime import datetime

# 1. Parse command-line arguments
parser = argparse.ArgumentParser()

parser.add_argument("--input", required=True)
parser.add_argument("--output_dir", required=True)
parser.add_argument("--num_examples", type=int, default=None)
parser.add_argument("--mode", choices=["pooled", "per_question"], default="pooled")

args = parser.parse_args()

# Generate a passage_id differently depending on whether passages are shared globally or kept query-specific.
def make_passage_id(title, sentence_idx, query_id, mode):
    if mode == "pooled":
        return f"{title}::{sentence_idx}"
    elif mode == "per_question":
        return f"{query_id}::{title}::{sentence_idx}"
    else:
        raise ValueError(f"Unknown mode:{mode}")

# 2. Set input and output paths
input_path = args.input
output_dir = args.output_dir

queries_path = os.path.join(output_dir, "queries.jsonl")
passages_path = os.path.join(output_dir, "passages.jsonl")
qrels_path = os.path.join(output_dir, "qrels.jsonl")
latest_run_path = os.path.join(output_dir, "latest_run.txt")

# 3. Make sure output directory exists
os.makedirs(output_dir, exist_ok=True)

# 4. Read HotpotQA raw data
with open(input_path,"r",encoding="utf-8") as f:
    raw_data = json.load(f)

# Optionally keep only the first N examples for testing
if args.num_examples is not None:
    raw_data = raw_data[:args.num_examples]

# 5. Create containers
queries = []
passages = {}
qrels = []

# 6. Loop over HotpotQA example
for i, example in enumerate(raw_data):
    query_id = f"q_{i + 1:06d}"

     # ---------- generate queries ----------
    query_record = {    
        "query_id": query_id,
        "query": example["question"],
        "answer": example["answer"],
        "type": example["type"]
    }

    queries.append(query_record)

    # ---------- generate passages ----------
    for title, sentences in example["context"]:
        for sentence_idx, sentence in enumerate(sentences):
            # # Filter out empty sentences
            passage_text = sentence.strip()

            if not passage_text:
                continue

            passage_id = make_passage_id(
                title = title,
                sentence_idx = sentence_idx,
                query_id = query_id,
                mode = args.mode
            )

            passage_record = {
                "passage_id": passage_id,
                "title": title,
                "sentence_index": sentence_idx,
                "passage_text": sentence
            }

            passages[passage_id] = passage_record

    # ---------- generate qrels ----------
    for title, sentence_idx in example["supporting_facts"]:
        passage_id = make_passage_id(
                title = title,
                sentence_idx = sentence_idx,
                query_id = query_id,
                mode = args.mode
            )

        qrel_record = {
            "query_id": query_id,
            "passage_id": passage_id,
            "relevance": 1
        }

        qrels.append(qrel_record)

# 7. Check whether passage_ids in qrels really exist
missing = []

for qrel in qrels:
    if qrel["passage_id"] not in passages:
        missing.append(qrel)

print("number of missing qrels:", len(missing))

# 8. Write queries.jsonl, passages.jsonl, and qrels.jsonl.
with open(queries_path, "w", encoding="utf-8") as f:
    for query in queries:
        f.write(json.dumps(query, ensure_ascii=False) + "\n")

with open(passages_path, "w", encoding="utf-8") as f:
    for passage in passages.values():
        f.write(json.dumps(passage, ensure_ascii=False) + "\n")

with open(qrels_path, "w", encoding="utf-8") as f:
    for qrel in qrels:
        f.write(json.dumps(qrel, ensure_ascii=False) + "\n")

# 9. Write latest run settings and summary to a text file
with open(latest_run_path, "w", encoding="utf-8") as f:
    f.write("Latest HotpotQA dataset build run\n")
    f.write("=" * 40 + "\n")

    f.write(f"run_time: {datetime.now().isoformat(timespec='seconds')}\n")
    f.write(f"input: {args.input}\n")
    f.write(f"output_dir: {args.output_dir}\n")
    f.write(f"num_examples: {args.num_examples}\n")
    f.write(f"mode: {args.mode}\n")

    f.write("\nOutput files:\n")
    f.write(f"queries_path: {queries_path}\n")
    f.write(f"passages_path: {passages_path}\n")
    f.write(f"qrels_path: {qrels_path}\n")

    f.write("\nSummary:\n")
    f.write(f"num_queries: {len(queries)}\n")
    f.write(f"num_passages: {len(passages)}\n")
    f.write(f"num_qrels: {len(qrels)}\n")
    f.write(f"num_missing_qrels: {len(missing)}\n")

# 10. Print information to check
print("Done.")
print("mode:", args.mode)
print("num_queries:", len(queries))
print("num_passages:", len(passages))
print("num_qrels:", len(qrels))