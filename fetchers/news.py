import os
import requests
from datetime import datetime, timedelta


def fetch_financial_news() -> list[dict]:
    """
    Fetch top financial news from the last 24 hours via Finnhub.
    Returns up to 10 items. Returns a placeholder if API key is missing.
    """
    api_key = os.getenv("FINNHUB_API_KEY", "")
    if not api_key:
        return [{"headline": "[News unavailable — set FINNHUB_API_KEY]", "summary": "", "source": "", "datetime": ""}]

    try:
        resp = requests.get(
            "https://finnhub.io/api/v1/news",
            params={"category": "general", "token": api_key},
            timeout=10,
        )
        resp.raise_for_status()
        items = resp.json()
    except Exception as e:
        return [{"headline": f"[News fetch error: {e}]", "summary": "", "source": "", "datetime": ""}]

    cutoff = datetime.now() - timedelta(hours=24)
    news: list[dict] = []

    for item in items:
        ts = item.get("datetime", 0)
        dt = datetime.fromtimestamp(ts) if ts else datetime.now()
        if dt < cutoff:
            continue
        news.append({
            "headline": item.get("headline", ""),
            "summary": item.get("summary", "")[:300],
            "source": item.get("source", ""),
            "datetime": dt.strftime("%Y-%m-%d %H:%M"),
        })
        if len(news) >= 10:
            break

    return news if news else [{"headline": "No news in the last 24 hours", "summary": "", "source": "", "datetime": ""}]
