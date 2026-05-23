from typing import TypedDict


class BriefState(TypedDict):
    run_date: str                     # YYYYMMDD
    market_data: list[dict]           # all tracked assets
    anomalies: list[dict]             # assets that moved >= ANOMALY_THRESHOLD
    news: list[dict]                  # top financial headlines
    macro_releases: list[dict]        # yesterday's data releases (actual vs forecast)
    calendar_events: list[dict]       # upcoming macro events (next 7 days)
    macro_indicators: dict            # FRED indicators (VIX, spreads, etc.)
    sector_performance: list[dict]    # 1d/5d/1m returns per sector ETF
    anomaly_analyses: list[dict]      # LLM-generated cause + forward impact per anomaly
    sector_analysis: dict             # LLM-generated hot/cold sector breakdown
    report_markdown: str              # final assembled Markdown report
    output_path: str                  # path where report was saved
