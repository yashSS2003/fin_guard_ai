"""LangGraph workflow graph for compliance review."""

from __future__ import annotations

from langgraph.graph import StateGraph, END

from src.graph_state import ComplianceState
from src.graph_nodes import (
    node_retrieve_policies,
    node_analyse_compliance,
    node_score_routing,
    node_self_correct,
    node_increment_retry,
    node_finalise,
    edge_after_analyse,
    edge_after_score_routing,
)


def build_compliance_graph() -> StateGraph:
    """Build and compile the LangGraph compliance review workflow."""

    graph = StateGraph(ComplianceState)

    # ── Register nodes ──────────────────────────────────────────────────────
    graph.add_node("retrieve_policies",    node_retrieve_policies)
    graph.add_node("analyse_compliance",   node_analyse_compliance)
    graph.add_node("score_routing",        node_score_routing)
    graph.add_node("self_correct",         node_self_correct)
    graph.add_node("increment_retry",      node_increment_retry)
    graph.add_node("finalise",             node_finalise)

    # ── Entry point ─────────────────────────────────────────────────────────
    graph.set_entry_point("retrieve_policies")

    # ── Fixed edges ─────────────────────────────────────────────────────────
    graph.add_edge("retrieve_policies",  "analyse_compliance")
    graph.add_edge("self_correct",       "analyse_compliance")   # retry after correction
    graph.add_edge("increment_retry",    "analyse_compliance")   # retry after borderline
    graph.add_edge("finalise",           END)

    # ── Conditional edges ───────────────────────────────────────────────────
    graph.add_conditional_edges(
        "analyse_compliance",
        edge_after_analyse,
        {
            "self_correct":   "self_correct",
            "score_routing":  "score_routing",
            "finalise":       "finalise",
        },
    )
    graph.add_conditional_edges(
        "score_routing",
        edge_after_score_routing,
        {
            "increment_retry": "increment_retry",
            "finalise":        "finalise",
        },
    )

    return graph.compile()


# Singleton compiled graph
_compiled_graph = None


def get_compliance_graph():
    global _compiled_graph
    if _compiled_graph is None:
        _compiled_graph = build_compliance_graph()
    return _compiled_graph
