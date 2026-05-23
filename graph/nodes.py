import os
from datetime import datetime
from pathlib import Path

from pydantic import BaseModel

from graph.state import BriefState
from fetchers.market import fetch_market_data
from fetchers.news import fetch_financial_news
from fetchers.calendar import fetch_macro_calendar
from fetchers.macro import fetch_macro_indicators
from fetchers.sectors import fetch_sector_performance
from report.formatter import format_report


# ---------------------------------------------------------------------------
# LLM factory — Anthropic preferred, DeepSeek fallback
# ---------------------------------------------------------------------------

def _get_llm():
    if os.getenv("ANTHROPIC_API_KEY"):
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(
            model=os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6"),
            temperature=0,
        )
    if os.getenv("DEEPSEEK_API_KEY"):
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
            openai_api_key=os.getenv("DEEPSEEK_API_KEY"),
            openai_api_base="https://api.deepseek.com/v1",
            temperature=0,
        )
    raise EnvironmentError(
        "No LLM API key found. Set ANTHROPIC_API_KEY or DEEPSEEK_API_KEY in .env"
    )


# ---------------------------------------------------------------------------
# Pydantic output schemas (v2)
# ---------------------------------------------------------------------------

class AnomalyExplanation(BaseModel):
    ticker: str
    cause: str
    forward_impact: str


class AnomalyAnalysisOutput(BaseModel):
    analyses: list[AnomalyExplanation]


class SectorAnalysisOutput(BaseModel):
    hot_sectors: list[str]
    hot_reasons: list[str]
    cold_but_watching: list[str]
    cold_reasons: list[str]
    summary: str


# ---------------------------------------------------------------------------
# Fetch nodes  (run in parallel in the graph)
# ---------------------------------------------------------------------------

def node_fetch_market_data(state: BriefState) -> dict:
    print("[node] fetch_market_data")
    market_data, anomalies = fetch_market_data()
    return {"market_data": market_data, "anomalies": anomalies}


def node_fetch_news(state: BriefState) -> dict:
    print("[node] fetch_news")
    return {"news": fetch_financial_news()}


def node_fetch_macro_calendar(state: BriefState) -> dict:
    print("[node] fetch_macro_calendar")
    releases, upcoming = fetch_macro_calendar()
    indicators = fetch_macro_indicators()
    return {
        "macro_releases": releases,
        "calendar_events": upcoming,
        "macro_indicators": indicators,
    }


# ---------------------------------------------------------------------------
# Aggregate node — runs after all three fetchers complete
# ---------------------------------------------------------------------------

def node_aggregate(state: BriefState) -> dict:
    print("[node] aggregate — fetching sector performance")
    return {"sector_performance": fetch_sector_performance()}


# ---------------------------------------------------------------------------
# Analysis nodes  (LLM-powered)
# ---------------------------------------------------------------------------

def node_anomaly_analysis(state: BriefState) -> dict:
    print("[node] anomaly_analysis")
    llm = _get_llm()

    anomaly_lines = "\n".join(
        f"- {a['ticker']} ({a['name']}, {a['category']}): {a['return_1d']:+.2f}%"
        for a in state["anomalies"]
    )
    news_lines = "\n".join(
        f"- {n['headline']}"
        for n in state.get("news", [])[:5]
    )

    prompt = f"""You are a senior macro analyst. The following assets had significant price moves (≥2%) yesterday:

{anomaly_lines}

Recent top financial headlines:
{news_lines}

For EACH anomaly ticker, provide a concise explanation.
Return valid JSON only, no markdown fences:
{{"analyses": [{{"ticker": "...", "cause": "one sentence", "forward_impact": "one sentence"}}]}}"""

    structured = llm.with_structured_output(AnomalyAnalysisOutput, method="json_mode")
    result: AnomalyAnalysisOutput = structured.invoke(prompt)
    return {"anomaly_analyses": [a.model_dump() for a in result.analyses]}


def node_sector_analysis(state: BriefState) -> dict:
    print("[node] sector_analysis")
    llm = _get_llm()

    sector_lines = "\n".join(
        f"- {s['sector']} ({s['ticker']}): 1d={s['return_1d']:+.1f}%  5d={s['return_5d']:+.1f}%  1m={s['return_1m']:+.1f}%"
        for s in state.get("sector_performance", [])
    )

    prompt = f"""You are a senior sector strategist. Here is recent sector ETF performance:

{sector_lines}

Identify:
1. Hot sectors right now (strong momentum across timeframes)
2. Cold but worth watching (underperformers with potential mean-reversion)

Return valid JSON only, no markdown fences:
{{"hot_sectors": ["..."], "hot_reasons": ["one reason per sector"],
  "cold_but_watching": ["..."], "cold_reasons": ["one reason per sector"],
  "summary": "one sentence macro theme"}}"""

    structured = llm.with_structured_output(SectorAnalysisOutput, method="json_mode")
    result: SectorAnalysisOutput = structured.invoke(prompt)
    return {"sector_analysis": result.model_dump()}


# ---------------------------------------------------------------------------
# Report + save nodes
# ---------------------------------------------------------------------------

def node_generate_brief(state: BriefState) -> dict:
    print("[node] generate_brief")
    llm = _get_llm()
    md = format_report(state, llm)
    return {"report_markdown": md}


def node_save_output(state: BriefState) -> dict:
    print("[node] save_output")
    run_date = state.get("run_date", datetime.now().strftime("%Y%m%d"))
    out_dir = Path("outputs")
    out_dir.mkdir(exist_ok=True)

    # Save Markdown
    md_path = out_dir / f"brief_{run_date}.md"
    md_path.write_text(state["report_markdown"], encoding="utf-8")
    print(f"Markdown saved → {md_path}")

    # Save PDF (gracefully skipped if WeasyPrint not available)
    from report.pdf_generator import markdown_to_pdf
    pdf_path = out_dir / f"brief_{run_date}.pdf"
    markdown_to_pdf(state["report_markdown"], str(pdf_path))

    return {"output_path": str(md_path)}
