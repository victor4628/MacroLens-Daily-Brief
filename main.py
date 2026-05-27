import os
import sys
from datetime import datetime
from zoneinfo import ZoneInfo
from dotenv import load_dotenv

load_dotenv()

# Enable LangSmith tracing when key is present
if os.getenv("LANGSMITH_API_KEY"):
    os.environ.setdefault("LANGCHAIN_TRACING_V2", "true")
    os.environ.setdefault("LANGCHAIN_PROJECT", "macrolens-daily-brief")

from graph.builder import build_graph
from graph.state import BriefState
from notifier.telegram import send_brief


def main() -> dict:
    eastern = ZoneInfo("America/New_York")
    run_date = datetime.now(eastern).strftime("%Y%m%d")
    print(f"\n{'='*50}")
    print(f"  MacroLens Daily Brief — {run_date}")
    print(f"{'='*50}\n")

    graph = build_graph()

    initial_state: BriefState = {
        "run_date": run_date,
        "market_data": [],
        "anomalies": [],
        "news": [],
        "macro_releases": [],
        "calendar_events": [],
        "macro_indicators": {},
        "sector_performance": [],
        "anomaly_analyses": [],
        "sector_analysis": {},
        "report_markdown": "",
        "output_path": "",
    }

    result = graph.invoke(initial_state)

    print(f"\n✅ Done — report saved to: {result['output_path']}")
    print(f"   Anomalies detected: {len(result.get('anomalies', []))}")
    print(f"   Assets tracked:     {len(result.get('market_data', []))}\n")

    send_brief(
        output_path=result["output_path"],
        run_date=run_date,
        anomalies=result.get("anomalies", []),
        sector_analysis=result.get("sector_analysis", {}),
        macro_indicators=result.get("macro_indicators", {}),
        report_markdown=result["report_markdown"],
    )

    return result


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
