import os
import requests
from datetime import datetime, timedelta


FRED_BASE = "https://api.stlouisfed.org/fred/series/observations"

# Key macro indicators available on FRED
FRED_SERIES: dict[str, str] = {
    "DFEDTARL": "Fed Funds Rate Lower Bound (%)",
    "DFEDTARU": "Fed Funds Rate Upper Bound (%)",
    "T10YIE": "10Y Breakeven Inflation (%)",
    "T10Y2Y": "10Y-2Y Yield Spread (bp)",
    "VIXCLS": "VIX",
    "DTWEXBGS": "USD Index (Broad)",
}


def fetch_macro_indicators() -> dict:
    """
    Fetch latest values for key macro indicators from FRED.
    Returns empty dict if FRED_API_KEY is not set.
    """
    api_key = os.getenv("FRED_API_KEY", "")
    if not api_key:
        return {}

    end = datetime.now()
    start = end - timedelta(days=30)  # wider window to catch monthly series
    indicators: dict = {}

    for series_id, label in FRED_SERIES.items():
        try:
            resp = requests.get(
                FRED_BASE,
                params={
                    "series_id": series_id,
                    "api_key": api_key,
                    "file_type": "json",
                    "observation_start": start.strftime("%Y-%m-%d"),
                    "observation_end": end.strftime("%Y-%m-%d"),
                    "sort_order": "desc",
                    "limit": 1,
                },
                timeout=10,
            )
            resp.raise_for_status()
            obs = resp.json().get("observations", [])
            if obs and obs[0]["value"] not in (".", ""):
                indicators[series_id] = {
                    "label": label,
                    "value": float(obs[0]["value"]),
                    "date": obs[0]["date"],
                }
        except Exception as e:
            print(f"[macro] FRED {series_id}: {e}")

    return indicators
