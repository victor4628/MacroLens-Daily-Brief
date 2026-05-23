import os
import requests
from pathlib import Path


TELEGRAM_API = "https://api.telegram.org/bot{token}/{method}"


def _token() -> str:
    return os.getenv("TELEGRAM_BOT_TOKEN", "")


def _chat_id() -> str:
    return os.getenv("TELEGRAM_CHAT_ID", "")


def send_brief(report_markdown: str, output_path: str, run_date: str) -> bool:
    """
    Send the daily brief to Telegram.
    1. Text message with key highlights (parsed from the report)
    2. The .md file as a document attachment
    """
    token = _token()
    chat_id = _chat_id()

    if not token or not chat_id:
        print("[telegram] Skipping — TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not set")
        return False

    # ── Build a short summary text from the report ────────────────────────────
    lines = report_markdown.splitlines()

    def extract_section(header: str) -> list[str]:
        """Extract lines under a given markdown header until the next header."""
        result, inside = [], False
        for line in lines:
            if line.strip().startswith(header):
                inside = True
                continue
            if inside:
                if line.startswith("## ") or line.startswith("---"):
                    break
                if line.strip():
                    result.append(line.strip())
        return result

    conclusion_lines = extract_section("## 💡 Daily Conclusion")
    conclusion = " ".join(conclusion_lines).replace(">", "").strip()

    anomaly_lines = extract_section("## ⚠️ Major Anomalies")
    anomaly_text = "\n".join(anomaly_lines[:6]) if anomaly_lines else "✅ No major anomalies"

    sector_lines = extract_section("### Hot Now")
    sector_text = "\n".join(sector_lines[:4]) if sector_lines else "—"

    # format date nicely: 20260522 → May 22, 2026
    try:
        from datetime import datetime
        display_date = datetime.strptime(run_date, "%Y%m%d").strftime("%B %d, %Y")
    except ValueError:
        display_date = run_date

    message = (
        f"📊 *MacroLens Daily Brief — {display_date}*\n\n"
        f"💡 *Conclusion*\n{conclusion}\n\n"
        f"⚠️ *Anomalies*\n{anomaly_text}\n\n"
        f"🔥 *Hot Sectors*\n{sector_text}"
    )

    # ── 1. Send text summary ──────────────────────────────────────────────────
    try:
        resp = requests.post(
            TELEGRAM_API.format(token=token, method="sendMessage"),
            json={
                "chat_id": chat_id,
                "text": message,
                "parse_mode": "Markdown",
            },
            timeout=15,
        )
        resp.raise_for_status()
        print("[telegram] Text message sent ✓")
    except Exception as e:
        print(f"[telegram] Failed to send text: {e}")
        return False

    # ── 2. Send PDF (preferred) or MD as fallback ─────────────────────────────
    md_path = Path(output_path)
    pdf_path = md_path.with_suffix(".pdf")

    send_path = pdf_path if pdf_path.exists() else md_path
    mime = "application/pdf" if send_path.suffix == ".pdf" else "text/markdown"

    if send_path.exists():
        try:
            with open(send_path, "rb") as f:
                resp = requests.post(
                    TELEGRAM_API.format(token=token, method="sendDocument"),
                    data={"chat_id": chat_id, "caption": f"Full report — {display_date}"},
                    files={"document": (send_path.name, f, mime)},
                    timeout=30,
                )
            resp.raise_for_status()
            print(f"[telegram] {send_path.suffix.upper()} sent ✓")
        except Exception as e:
            print(f"[telegram] Failed to send document: {e}")

    return True
