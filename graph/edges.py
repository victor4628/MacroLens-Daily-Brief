from graph.state import BriefState


def route_after_aggregate(state: BriefState) -> str:
    """
    Conditional routing after the aggregate node.
    If any asset triggered the anomaly threshold, run anomaly_analysis first.
    Otherwise skip straight to sector_analysis.
    """
    if state.get("anomalies"):
        return "anomaly_analysis"
    return "sector_analysis"
