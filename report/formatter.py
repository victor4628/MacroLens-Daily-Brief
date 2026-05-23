from datetime import datetime


def format_report(state: dict, llm) -> str:
    run_date_raw = state.get("run_date", datetime.now().strftime("%Y%m%d"))
    try:
        run_date_display = datetime.strptime(run_date_raw, "%Y%m%d").strftime("%B %d, %Y")
    except ValueError:
        run_date_display = run_date_raw

    market_data: list[dict] = state.get("market_data", [])
    anomalies: list[dict] = state.get("anomalies", [])
    anomaly_analyses: list[dict] = state.get("anomaly_analyses", [])
    macro_releases: list[dict] = state.get("macro_releases", [])
    calendar_events: list[dict] = state.get("calendar_events", [])
    macro_indicators: dict = state.get("macro_indicators", {})
    sector_analysis: dict = state.get("sector_analysis", {})
    news: list[dict] = state.get("news", [])

    # ── 1. Market Snapshot ────────────────────────────────────────────────────
    snapshot_rows: list[str] = []
    for cat_name in ["US Equities", "US Treasuries", "Credit", "Commodities", "FX", "Crypto"]:
        cat_assets = [a for a in market_data if a.get("category") == cat_name]
        if cat_assets:
            snapshot_rows.append(f"| **{cat_name}** | | | | |")
        for a in cat_assets:
            flag = " ⚠️" if a["is_anomaly"] else ""
            emoji = "🟢" if a["signal"] == "bullish" else "🔴" if a["signal"] == "bearish" else "⚪"
            snapshot_rows.append(
                f"| {a['ticker']}{flag} | {a['name']} | {a['price']:.2f} | {a['return_1d']:+.2f}% | {emoji} {a['signal']} |"
            )

    snapshot_table = (
        "| Ticker | Name | Price | 1D Return | Signal |\n"
        "|--------|------|------:|----------:|--------|\n"
        + "\n".join(snapshot_rows)
    ) if snapshot_rows else "_No market data available._"

    # ── 2. Macro Indicators (FRED) ────────────────────────────────────────────
    if macro_indicators:
        # Merge Fed Funds lower/upper into a single "X.XX% – X.XX%" row
        indicators_display = dict(macro_indicators)
        lower = indicators_display.pop("DFEDTARL", None)
        upper = indicators_display.pop("DFEDTARU", None)
        rows: list[str] = []
        if lower and upper:
            rows.append(
                f"| Fed Funds Rate Target | {lower['value']}% – {upper['value']}% | {lower['date']} |"
            )
        elif lower:
            rows.append(f"| Fed Funds Rate | {lower['value']}% | {lower['date']} |")

        for v in indicators_display.values():
            rows.append(f"| {v['label']} | {v['value']} | {v['date']} |")

        indicators_section = (
            "## 🏦 Key Macro Indicators\n\n"
            "| Indicator | Value | As Of |\n"
            "|-----------|------:|-------|\n"
            + "\n".join(rows)
        )
    else:
        indicators_section = ""

    # ── 3. Anomalies ─────────────────────────────────────────────────────────
    if anomalies:
        analysis_map = {a["ticker"]: a for a in anomaly_analyses}
        anomaly_blocks: list[str] = []
        for a in sorted(anomalies, key=lambda x: abs(x["return_1d"]), reverse=True):
            ticker = a["ticker"]
            ana = analysis_map.get(ticker, {})
            anomaly_blocks.append(
                f"### {ticker} — {a['name']} &nbsp; `{a['return_1d']:+.2f}%`\n\n"
                f"**Cause:** {ana.get('cause', '_Analysis unavailable_')}\n\n"
                f"**Forward Impact:** {ana.get('forward_impact', '_N/A_')}"
            )
        anomaly_section = "## ⚠️ Major Anomalies\n\n" + "\n\n---\n\n".join(anomaly_blocks)
    else:
        anomaly_section = "## ✅ No Major Anomalies\n\nNo assets moved more than ±2% yesterday."

    # ── 4. Macro Releases ─────────────────────────────────────────────────────
    if macro_releases and macro_releases[0].get("event", "").startswith("["):
        macro_table = f"_{macro_releases[0]['event']}_"
    elif macro_releases:
        rows = []
        for r in macro_releases:
            surprise = r.get("surprise") or "—"
            emoji = "✅" if surprise == "beat" else "❌" if surprise == "miss" else "➖"
            country = r.get("country", "")
            rows.append(
                f"| {r.get('event','—')} | {country} | {r.get('actual','—')} | {r.get('forecast','—')} | {r.get('previous','—')} | {emoji} {surprise} |"
            )
        macro_table = (
            "| Event | Country | Actual | Forecast | Previous | Surprise |\n"
            "|-------|---------|-------:|---------:|---------:|:---------|\n"
            + "\n".join(rows)
        )
    else:
        macro_table = "_No major macro releases yesterday._"

    # ── 5. Economic Calendar ──────────────────────────────────────────────────
    if calendar_events:
        cal_rows = "\n".join(
            f"| {e.get('date','—')} | {e.get('event','—')} | {e.get('country','—')} | {e.get('importance','—')} |"
            for e in calendar_events
        )
        calendar_table = (
            "| Date | Event | Country | Importance |\n"
            "|------|-------|---------|------------|\n"
            + cal_rows
        )
    else:
        calendar_table = "_No upcoming macro events in the next 7 days._"

    # ── 6. Sector Heat ────────────────────────────────────────────────────────
    hot = sector_analysis.get("hot_sectors", [])
    hot_reasons = sector_analysis.get("hot_reasons", [])
    cold = sector_analysis.get("cold_but_watching", [])
    cold_reasons = sector_analysis.get("cold_reasons", [])
    sector_summary = sector_analysis.get("summary", "")

    hot_lines = "\n".join(f"- **{s}** — {r}" for s, r in zip(hot, hot_reasons)) or "_None identified._"
    cold_lines = "\n".join(f"- **{s}** — {r}" for s, r in zip(cold, cold_reasons)) or "_None flagged._"

    # ── 7. Daily Conclusion (LLM) ─────────────────────────────────────────────
    context = (
        f"Date: {run_date_display}\n"
        f"Anomalies ({len(anomalies)} assets ≥ ±2%): {', '.join(a['ticker'] for a in anomalies) or 'none'}\n"
        f"Hot sectors: {', '.join(hot) or 'none'}\n"
        f"Cold sectors to watch: {', '.join(cold) or 'none'}\n"
        f"Macro surprises: {', '.join(r.get('event','') for r in macro_releases if r.get('surprise') in ('beat','miss'))[:120] or 'none'}\n"
        f"Top headline: {news[0]['headline'] if news else 'N/A'}"
    )
    try:
        conclusion = llm.invoke(
            f"Based on this market context, write ONE concise sentence summarizing the dominant macro theme:\n\n{context}"
        ).content.strip().strip('"')
    except Exception as e:
        conclusion = f"_(Conclusion generation failed: {e})_"

    # ── Assemble ──────────────────────────────────────────────────────────────
    indicators_block = f"\n\n{indicators_section}\n\n---" if indicators_section else ""

    report = f"""# MacroLens Daily Brief — {run_date_display}

> *Automated macro briefing generated by MacroLens AI*

---

## 📊 Market Snapshot

{snapshot_table}
{indicators_block}

---

{anomaly_section}

---

## 📋 Macro Data Releases — Yesterday

{macro_table}

---

## 📅 Economic Calendar — Next 7 Days

{calendar_table}

---

## 🔥 Sector Heat Map

### Hot Now
{hot_lines}

### Cold but Worth Watching
{cold_lines}

{f"> {sector_summary}" if sector_summary else ""}

---

## 💡 Daily Conclusion

> {conclusion}

---
*Generated: {datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")} | MacroLens v1.0*
"""
    return report
