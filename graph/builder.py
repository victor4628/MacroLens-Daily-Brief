from langgraph.graph import StateGraph, START, END

from graph.state import BriefState
from graph.nodes import (
    node_fetch_market_data,
    node_fetch_news,
    node_fetch_macro_calendar,
    node_aggregate,
    node_anomaly_analysis,
    node_sector_analysis,
    node_generate_brief,
    node_save_output,
)
from graph.edges import route_after_aggregate


def build_graph():
    """
    Assemble the MacroLens StateGraph.

    Topology:
        ┌─ fetch_market_data ─┐
    START─┤─ fetch_news        ─┼─► aggregate ─► [conditional] ─► sector_analysis
        └─ fetch_macro_calendar┘                       │
                                                anomaly_analysis ─►┘
        sector_analysis ─► generate_brief ─► save_output ─► END
    """
    g = StateGraph(BriefState)

    # nodes
    g.add_node("fetch_market_data", node_fetch_market_data)
    g.add_node("fetch_news", node_fetch_news)
    g.add_node("fetch_macro_calendar", node_fetch_macro_calendar)
    g.add_node("aggregate", node_aggregate)
    g.add_node("anomaly_analysis", node_anomaly_analysis)
    g.add_node("sector_analysis", node_sector_analysis)
    g.add_node("generate_brief", node_generate_brief)
    g.add_node("save_output", node_save_output)

    # parallel fan-out from START → all three fetchers
    g.add_edge(START, "fetch_market_data")
    g.add_edge(START, "fetch_news")
    g.add_edge(START, "fetch_macro_calendar")

    # fan-in → aggregate (runs once all three fetchers complete)
    g.add_edge("fetch_market_data", "aggregate")
    g.add_edge("fetch_news", "aggregate")
    g.add_edge("fetch_macro_calendar", "aggregate")

    # conditional routing: anomaly path or direct to sectors
    g.add_conditional_edges(
        "aggregate",
        route_after_aggregate,
        {
            "anomaly_analysis": "anomaly_analysis",
            "sector_analysis": "sector_analysis",
        },
    )

    g.add_edge("anomaly_analysis", "sector_analysis")
    g.add_edge("sector_analysis", "generate_brief")
    g.add_edge("generate_brief", "save_output")
    g.add_edge("save_output", END)

    return g.compile()
