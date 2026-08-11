import sys
from pathlib import Path

import networkx as nx


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_DIR))

from retrieval.graph_query_expansion import (  # noqa: E402
    build_expanded_query,
    collect_expansion_candidates,
    expand_query,
    match_query_concepts,
    rank_expansion_candidates,
)


def build_small_graph():
    """Build the toy concept graph used by graph query expansion tests."""
    graph = nx.Graph()

    graph.add_edge("doctor strange", "scott derrickson", weight=3)
    graph.add_edge("doctor strange", "marvel studios", weight=1)
    graph.add_edge("scott derrickson", "horror film", weight=2)

    return graph

## Direct test 4 helpers: match_query_concepts(), collect_expansion_candidates()
##                        rank_expansion_candidates(), build_expanded_query()

def test_match_query_concepts_returns_matched_and_unmatched():
    """match_query_concepts should split input concepts by graph membership."""
    graph = build_small_graph()

    matched, unmatched = match_query_concepts(
        query_concepts=["doctor strange", "blade runner", "doctor strange"],
        graph=graph,
    )

    assert matched == ["doctor strange"]
    assert unmatched == ["blade runner"]


def test_collect_expansion_candidates_returns_weighted_candidates():
    """collect_expansion_candidates should collect neighbors with edge scores."""
    graph = build_small_graph()

    candidates = collect_expansion_candidates(
        matched_graph_nodes=["doctor strange"],
        graph=graph,
        hop=1,
    )

    assert candidates == {
        "scott derrickson": {"score": 3, "hop": 1},
        "marvel studios": {"score": 1, "hop": 1},
    }


def test_rank_expansion_candidates_sorts_by_score_hop_and_concept():
    """rank_expansion_candidates should use deterministic tie-breaking."""
    candidates = {
        "beta": {"score": 2, "hop": 2},
        "alpha": {"score": 2, "hop": 1},
        "gamma": {"score": 3, "hop": 1},
    }

    ranked = rank_expansion_candidates(candidates)

    assert ranked == [
        {"concept": "gamma", "score": 3, "hop": 1},
        {"concept": "alpha", "score": 2, "hop": 1},
        {"concept": "beta", "score": 2, "hop": 2},
    ]


def test_build_expanded_query_appends_selected_concepts():
    """build_expanded_query should append selected concept strings in order."""
    expanded_query = build_expanded_query(
        query="Who directed Doctor Strange?",
        expanded_concepts=[
            {"concept": "scott derrickson", "score": 3, "hop": 1},
            {"concept": "marvel studios", "score": 1, "hop": 1},
        ],
    )

    assert (
        expanded_query
        == "Who directed Doctor Strange? scott derrickson marvel studios"
    )

## Test expand_query()

def test_hop_1_returns_two_direct_neighbors():
    """hop=1 should return the two direct neighbors of the query concept."""
    graph = build_small_graph()

    trace = expand_query(
        query="Who directed Doctor Strange?",
        query_concepts=["doctor strange"],
        graph=graph,
        hop=1,
        top_n=2,
    )

    expanded = [item["concept"] for item in trace["expanded_concepts"]]

    assert expanded == ["scott derrickson", "marvel studios"]


def test_higher_edge_weight_ranks_first():
    """The edge_weight strategy should rank the stronger direct edge first."""
    graph = build_small_graph()

    trace = expand_query(
        query="Who directed Doctor Strange?",
        query_concepts=["doctor strange"],
        graph=graph,
        hop=1,
        top_n=2,
    )

    assert trace["expanded_concepts"][0]["concept"] == "scott derrickson"
    assert (
        trace["expanded_concepts"][0]["score"]
        > trace["expanded_concepts"][1]["score"]
    )


def test_hop_2_can_find_second_hop_neighbor():
    """hop=2 should include concepts two edges away from the query concept."""
    graph = build_small_graph()

    trace = expand_query(
        query="Who directed Doctor Strange?",
        query_concepts=["doctor strange"],
        graph=graph,
        hop=2,
        top_n=3,
    )

    expanded = {item["concept"] for item in trace["expanded_concepts"]}

    assert "horror film" in expanded


def test_original_query_concepts_are_not_repeated_in_expansion():
    """Matched query concepts should not be appended again."""
    graph = build_small_graph()

    trace = expand_query(
        query="Doctor Strange Scott Derrickson",
        query_concepts=["doctor strange", "scott derrickson"],
        graph=graph,
        hop=1,
        top_n=5,
    )

    expanded = {item["concept"] for item in trace["expanded_concepts"]}

    assert "doctor strange" not in expanded
    assert "scott derrickson" not in expanded


def test_query_stays_unchanged_when_no_concepts_match_graph():
    """If no query concept exists in the graph, the query should be unchanged."""
    graph = build_small_graph()
    query = "Who wrote Blade Runner?"

    trace = expand_query(
        query=query,
        query_concepts=["blade runner"],
        graph=graph,
        hop=1,
        top_n=5,
    )

    assert trace["matched_graph_nodes"] == []
    assert trace["unmatched_query_concepts"] == ["blade runner"]
    assert trace["expanded_concepts"] == []
    assert trace["expanded_query"] == query


def test_blocked_concepts_do_not_enter_expansion_results():
    """Concepts passed in blocked_concepts should be filtered before ranking."""
    graph = build_small_graph()

    trace = expand_query(
        query="Who directed Doctor Strange?",
        query_concepts=["doctor strange"],
        graph=graph,
        hop=1,
        top_n=2,
        blocked_concepts=["marvel studios"],
    )

    expanded = {item["concept"] for item in trace["expanded_concepts"]}

    assert "marvel studios" not in expanded

## Test specificity strategy

def test_edge_weight_log_passage_count_downweights_common_candidates():
    """The specificity strategy should penalize high-passage-count concepts."""
    graph = nx.Graph()
    graph.add_edge("doctor strange", "generic film", weight=10)
    graph.add_edge("doctor strange", "scott derrickson", weight=3)
    graph.nodes["generic film"]["passage_count"] = 1000
    graph.nodes["scott derrickson"]["passage_count"] = 1

    baseline_trace = expand_query(
        query="Who directed Doctor Strange?",
        query_concepts=["doctor strange"],
        graph=graph,
        hop=1,
        top_n=2,
        strategy="edge_weight",
    )
    specificity_trace = expand_query(
        query="Who directed Doctor Strange?",
        query_concepts=["doctor strange"],
        graph=graph,
        hop=1,
        top_n=2,
        strategy="edge_weight_log_passage_count",
    )

    assert baseline_trace["expanded_concepts"][0]["concept"] == "generic film"
    assert (
        specificity_trace["expanded_concepts"][0]["concept"]
        == "scott derrickson"
    )
