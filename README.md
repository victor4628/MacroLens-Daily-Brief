# MacroLens Daily Brief

An automated daily macro market briefing agent that runs every weekday via GitHub Actions, fetches real-time market and macro data, orchestrates LLM analysis with LangGraph, and commits a Markdown report to this repo.

---

## Architecture

```
                    ┌──────────────────────────────────────────────────┐
                    │                  LangGraph StateGraph              │
                    │                                                    │
                    │   ┌─────────────────┐                             │
                    │   │ fetch_market_data│──┐                         │
  GitHub Actions    │   └─────────────────┘  │                         │
  (cron 08:00 EST) ─┤   ┌─────────────────┐  ├──► aggregate ──┐        │
        │           │   │   fetch_news    │──┘                │        │
        ▼           │   └─────────────────┘                   │ cond.  │
   python main.py   │   ┌─────────────────┐  ┌──────────────┐ │ edge   │
                    │   │fetch_macro_cal. │──┘ (parallel     │ │        │
                    │   └─────────────────┘    fan-in)       ▼ ▼        │
                    │                                                    │
                    │   anomalies?  ──yes──► anomaly_analysis ──┐       │
                    │       │                                    │       │
                    │      no                                    ▼       │
                    │       └────────────────────────► sector_analysis  │
                    │                                        │           │
                    │                               generate_brief       │
                    │                                        │           │
                    │                               save_output          │
                    │                               outputs/brief_*.md  │
                    └──────────────────────────────────────────────────┘

  Data sources                          LLM providers
  ────────────                          ─────────────
  yfinance       → prices / returns     Anthropic Claude  (preferred)
  Finnhub        → news + econ calendar DeepSeek V4       (fallback)
  FRED API       → macro indicators
```

---

## Why LangGraph instead of plain LangChain?

| Concern | LangChain | LangGraph |
|---------|-----------|-----------|
| **Conditional logic** | Hard to express "only call this LLM if condition X is true" without custom code | First-class `add_conditional_edges` — the anomaly branch is a native graph edge |
| **Parallel execution** | Sequential chains by default; parallelism requires explicit `RunnableParallel` nesting | Fan-out from `START` to multiple nodes runs them in a single super-step automatically |
| **State management** | Each chain returns a new value; sharing state across steps needs manual plumbing | `BriefState` TypedDict is the single source of truth — every node reads and writes it |
| **Observability** | LangSmith traces individual chain calls | LangSmith traces the full graph execution with step-by-step node visibility |
| **Restartability** | No built-in checkpoint mechanism | `MemorySaver` / `SqliteSaver` checkpoints let you resume from any node after a failure |

For a pipeline with **conditional branching** (anomaly path / no-anomaly path) and **parallel data fetching**, LangGraph's graph abstraction is the correct level of abstraction — LangChain would require manual orchestration that LangGraph gives you for free.

---

## Setup

### 1. Clone and install

```bash
git clone https://github.com/YOUR_USERNAME/macrolens-daily-brief.git
cd macrolens-daily-brief
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure API keys

```bash
cp .env.example .env
# edit .env and fill in your keys
```

| Key | Required | Where to get it |
|-----|----------|-----------------|
| `ANTHROPIC_API_KEY` | One of these two | [console.anthropic.com](https://console.anthropic.com) |
| `DEEPSEEK_API_KEY`  | One of these two | [platform.deepseek.com](https://platform.deepseek.com) |
| `FINNHUB_API_KEY`   | Yes | [finnhub.io](https://finnhub.io) — free tier |
| `FRED_API_KEY`      | No (degrades gracefully) | [fred.stlouisfed.org/docs/api/api_key.html](https://fred.stlouisfed.org/docs/api/api_key.html) |
| `LANGSMITH_API_KEY` | No (optional tracing) | [smith.langchain.com](https://smith.langchain.com) |

### 3. Run locally

```bash
python main.py
# report appears at outputs/brief_YYYYMMDD.md
```

---

## GitHub Actions setup

1. Push this repo to GitHub.
2. Go to **Settings → Secrets and variables → Actions** and add your API keys as repository secrets (same names as in `.env.example`).
3. The workflow runs automatically at **08:00 EST every weekday** and commits the report to `outputs/`.
4. To trigger manually: **Actions → MacroLens Daily Brief → Run workflow**.

---

## Output format

Each report contains:

1. **Market Snapshot** — price table with 1D return and signal for all tracked assets, anomalies flagged with ⚠️
2. **Key Macro Indicators** — FRED data (VIX, yield spread, breakeven inflation, USD index)
3. **Major Anomalies** — LLM-generated cause and forward impact for every asset that moved ≥ 2%
4. **Macro Data Releases** — yesterday's actual vs forecast with beat/miss label
5. **Economic Calendar** — next 7 days of macro events
6. **Sector Heat Map** — LLM-identified hot sectors and cold-but-watching sectors
7. **Daily Conclusion** — one-sentence macro theme for the day

---

## Project structure

```
macrolens/
├── main.py               # entry point
├── config/
│   └── assets.py         # all tickers and thresholds
├── graph/
│   ├── state.py          # BriefState TypedDict
│   ├── nodes.py          # all 8 LangGraph node functions
│   ├── edges.py          # conditional routing logic
│   └── builder.py        # StateGraph assembly
├── fetchers/
│   ├── market.py         # yfinance prices + anomaly detection
│   ├── news.py           # Finnhub financial news
│   ├── calendar.py       # Finnhub economic calendar
│   ├── macro.py          # FRED macro indicators
│   └── sectors.py        # yfinance sector ETF returns
├── report/
│   └── formatter.py      # Markdown report assembly
├── outputs/              # generated reports (auto-committed by CI)
└── .github/workflows/
    └── daily_brief.yml   # GitHub Actions schedule
```
