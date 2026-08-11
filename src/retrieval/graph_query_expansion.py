"""
Graph-based query expansion for concept-aware evidence retrieval.

This module only decides how to expand an already-normalized query with a
NetworkX concept graph. It does not run BM25 retrieval, dense retrieval, or
metric evaluation. The returned trace keeps intermediate expansion decisions
visible for later case studies and manual inspection.
"""

import math


# Keep the default blocklist intentionally empty for the first implementation.
# Callers can pass blocked_concepts when they want to filter noisy concepts.
DEFAULT_BLOCKED_CONCEPTS = []
SUPPORTED_RANKING_STRATEGIES = {
    "edge_weight",
    "edge_weight_log_passage_count",
}


def match_query_concepts(query_concepts, graph):
    """
    Match normalized query concepts to graph nodes.

    Args:
        query_concepts: Iterable of Week 4 normalized query concepts.
        graph: NetworkX concept graph.

    Returns:
        A tuple of (matched_graph_nodes, unmatched_query_concepts). Both lists
        preserve the input concept order after removing duplicates.
    """
    seen = set()
    matched_graph_nodes = []
    unmatched_query_concepts = []

    for concept in query_concepts:
        if concept in seen:
            continue
        seen.add(concept)

        if concept in graph:
            matched_graph_nodes.append(concept)
        else:
            unmatched_query_concepts.append(concept)

    return matched_graph_nodes, unmatched_query_concepts


def collect_expansion_candidates(matched_graph_nodes, graph, hop=1, blocked_concepts=None,):
    """
    Collect 1-hop or 2-hop candidate concepts from matched graph nodes.

    Args:
        matched_graph_nodes: Query concepts that exist as graph nodes.
        graph: NetworkX concept graph.
        hop: Number of graph hops to expand. Supported values are 1 and 2.
        blocked_concepts: Optional set of concepts to exclude from candidates.

    Returns:
        A dict keyed by candidate concept. Each value stores the best hop and
        accumulated edge-weight score used by ranking.

    Raises:
        ValueError: If hop is not 1 or 2.
    """
    if hop not in {1, 2}:
        raise ValueError("hop must be 1 or 2")

    if blocked_concepts is None:
        blocked_concepts = DEFAULT_BLOCKED_CONCEPTS
    blocked_concepts = set(blocked_concepts)
    query_node_set = set(matched_graph_nodes)
    candidates = {}

    for source in matched_graph_nodes:
        for neighbor in graph.neighbors(source):
            _add_candidate(
                candidates=candidates,
                concept=neighbor,
                score=_edge_weight(graph, source, neighbor),
                hop=1,
                query_node_set=query_node_set,
                blocked_concepts=blocked_concepts,
            )

            if hop == 1:
                continue

            # For 2-hop expansion, score the path by adding both edge weights.
            for second_hop_neighbor in graph.neighbors(neighbor):
                path_score = (
                    _edge_weight(graph, source, neighbor)
                    + _edge_weight(graph, neighbor, second_hop_neighbor)
                )
                _add_candidate(
                    candidates=candidates,
                    concept=second_hop_neighbor,
                    score=path_score,
                    hop=2,
                    query_node_set=query_node_set,
                    blocked_concepts=blocked_concepts,
                )

    return candidates


def rank_expansion_candidates(candidates, strategy="edge_weight", graph=None):
    """
    Rank collected expansion candidates.

    Args:
        candidates: Candidate dict from collect_expansion_candidates().
        strategy: Ranking strategy. 
            - "edge_weight" sorts by accumulated edge weights. 
            - "edge_weight_log_passage_count" divides that score by
            log(2 + candidate passage_count).
        graph: NetworkX concept graph. Required for
            "edge_weight_log_passage_count" to read candidate passage_count.

    Returns:
        A list of {"concept": str, "score": float, "hop": int} dictionaries.

    Raises:
        ValueError: If strategy is unsupported.
    """
    if strategy not in SUPPORTED_RANKING_STRATEGIES:
        supported = "', '".join(sorted(SUPPORTED_RANKING_STRATEGIES))
        raise ValueError(f"strategy must be one of '{supported}'")
    if strategy == "edge_weight_log_passage_count" and graph is None:
        raise ValueError(
            "graph is required for 'edge_weight_log_passage_count'"
        )

    ranked_candidates = [
        {
            "concept": concept,
            "score": _rank_score(
                concept=concept,
                edge_score=values["score"],
                strategy=strategy,
                graph=graph,
            ),
            "hop": values["hop"],
        }
        for concept, values in candidates.items()
    ]

    # Prefer higher score, then closer hop, then concept text for deterministic ties.
    ranked_candidates.sort(
        key=lambda item: (-item["score"], item["hop"], item["concept"])
    )

    return ranked_candidates


def build_expanded_query(query, expanded_concepts):
    """
    Append selected expansion concepts to the original query text.

    Args:
        query: Original natural-language query.
        expanded_concepts: Ranked concept dicts selected for expansion.

    Returns:
        The original query followed by selected concept strings.
    """
    if not expanded_concepts:
        return query

    expansion_text = " ".join(item["concept"] for item in expanded_concepts)
    return f"{query} {expansion_text}"


def expand_query(query, query_concepts, graph, hop=1, top_n=5, strategy="edge_weight", blocked_concepts=None,):
    """
    Expand a query with graph-neighbor concepts and return a full trace.

    Args:
        query: Original question text.
        query_concepts: Week 4 normalized concepts extracted from the query.
        graph: NetworkX concept graph.
        hop: Expansion depth. Use 0 for no expansion, or 1/2 for graph neighbors.
        top_n: Maximum number of concepts to append to the query.
        strategy: Candidate ranking strategy. Supported values are
            "edge_weight" and "edge_weight_log_passage_count".
        blocked_concepts: Optional set of concepts to filter from expansion.

    Returns:
        A dictionary with original query, input concepts, matched graph nodes,
        unmatched concepts, selected expansion concepts, and expanded query.

    Raises:
        ValueError: If hop is not 0, 1, or 2, or if top_n is negative.
    """

    if hop not in {0, 1, 2}:
        raise ValueError("hop must be 0, 1, or 2")
    if top_n < 0:
        raise ValueError("top_n must be greater than or equal to 0")

    query_concepts = list(query_concepts)
    matched_graph_nodes, unmatched_query_concepts = match_query_concepts(
        query_concepts,
        graph,
    )

    trace = {
        "original_query": query,
        "query_concepts": query_concepts,
        "matched_graph_nodes": matched_graph_nodes,
        "unmatched_query_concepts": unmatched_query_concepts,
        "expanded_concepts": [],
        "expanded_query": query,
    }

    # No-expansion cases still return the same trace shape for downstream use.
    if hop == 0 or top_n == 0 or not matched_graph_nodes:
        return trace

    candidates = collect_expansion_candidates(
        matched_graph_nodes=matched_graph_nodes,
        graph=graph,
        hop=hop,
        blocked_concepts=blocked_concepts,
    )
    ranked_candidates = rank_expansion_candidates(
        candidates,
        strategy=strategy,
        graph=graph,
    )
    expanded_concepts = ranked_candidates[:top_n]

    trace["expanded_concepts"] = expanded_concepts
    trace["expanded_query"] = build_expanded_query(query, expanded_concepts)

    return trace


## Helper Fucntions

def _edge_weight(graph, source, target):
    """Return edge weight, defaulting to 1 when the graph edge has no weight."""
    return graph[source][target].get("weight", 1)


def _rank_score(concept, edge_score, strategy, graph):
    """Return the ranking score for one candidate under the chosen strategy."""
    if strategy == "edge_weight":
        return edge_score

    passage_count = _node_passage_count(graph, concept)
    return edge_score / math.log(2 + passage_count)


def _node_passage_count(graph, concept):
    """Return candidate passage_count with a safe floor for log scoring."""
    return max(1, graph.nodes[concept].get("passage_count", 1))


def _add_candidate(
    candidates,
    concept,
    score,
    hop,
    query_node_set,
    blocked_concepts,
):
    """Add or update one candidate concept if it is allowed for expansion."""
    if concept in query_node_set or concept in blocked_concepts:
        return

    if concept not in candidates:
        candidates[concept] = {"score": 0, "hop": hop}

    # Multiple paths can reach the same candidate; accumulate evidence from all paths.
    candidates[concept]["score"] += score
    candidates[concept]["hop"] = min(candidates[concept]["hop"], hop)
