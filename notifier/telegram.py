import os
import requests
from datetime import datetime
from pathlib import Path


TELEGRAM_API = "https://api.telegram.org/bot{token}/{method}"


def send_brief(output_path: str, run_date: str, **kwargs) -> bool:
    """Send the daily PDF report to Telegram."""
    token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "")

    if not token or not chat_id:
        print("[telegram] Skipping — TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not set")
        return False

    try:
        display_date = datetime.strptime(run_date, "%Y%m%d").strftime("%B %d, %Y")
    except ValueError:
        display_date = run_date

    md_path = Path(output_path)
    pdf_path = md_path.with_suffix(".pdf")
    send_path = pdf_path if pdf_path.exists() else md_path
    mime = "application/pdf" if send_path.suffix == ".pdf" else "text/markdown"

    if not send_path.exists():
        print("[telegram] No file to send")
        return False

    try:
        with open(send_path, "rb") as f:
            resp = requests.post(
                TELEGRAM_API.format(token=token, method="sendDocument"),
                data={"chat_id": chat_id, "caption": f"MacroLens Daily Brief — {display_date}"},
                files={"document": (send_path.name, f, mime)},
                timeout=60,
            )
        resp.raise_for_status()
        print(f"[telegram] {send_path.suffix.upper()} sent ✓")
        return True
    except Exception as e:
        print(f"[telegram] Failed to send: {e}")
        return False
