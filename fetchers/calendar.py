import os
import requests
from datetime import datetime, timedelta

# ---------------------------------------------------------------------------
# Whitelist: keyword sets per country
# An event matches if its name contains ANY of the listed substrings (case-insensitive)
# ---------------------------------------------------------------------------

US_KEYWORDS = [
    # Inflation
    "cpi", "consumer price",
    "pce", "personal consumption expenditure",
    # Jobs
    "nonfarm", "non-farm", "payroll",
    "unemployment rate",
    # Growth
    "gdp",
    "ism manufacturing", "ism services", "ism non-manufacturing",
    # Housing
    "housing starts",
    # Fed
    "fomc", "fed funds", "interest rate decision",
    "powell", "fed chair",
    # Energy inventories
    "eia crude", "crude oil inventories", "crude oil stocks",
    "eia natural gas", "natural gas stocks", "natural gas storage",
]

# For JP/UK/EU: only central bank rate decisions
CB_KEYWORDS = [
    "interest rate decision",
    "rate decision",
    "policy rate",
    "bank rate",
]

# Countries and their keyword lists
COUNTRY_FILTERS: dict[str, list[str]] = {
    "us": US_KEYWORDS,
    "jp": CB_KEYWORDS,   # BoJ
    "gb": CB_KEYWORDS,   # BoE
    "eu": CB_KEYWORDS,   # ECB
}


def _matches(event_name: str, keywords: list[str]) -> bool:
    name_lower = event_name.lower()
    return any(kw in name_lower for kw in keywords)


def fetch_macro_calendar() -> tuple[list[dict], list[dict]]:
    """
    Fetch economic calendar from Finnhub, filtered to high-signal events only.

    Returns:
        releases  — yesterday's reported data (actual not None) matching whitelist
        upcoming  — next 7 days of whitelisted events, deduped
    """
    api_key = os.getenv("FINNHUB_API_KEY", "")
    if not api_key:
        placeholder = [{"event": "[Calendar unavailable — set FINNHUB_API_KEY]",
                        "actual": None, "forecast": None, "previous": None,
                        "surprise": None, "country": "", "date": ""}]
        return placeholder, []

    from zoneinfo import ZoneInfo
    eastern = ZoneInfo("America/New_York")
    today = datetime.now(eastern)
    tomorrow = today + timedelta(days=1)
    week_out = today + timedelta(days=8)

    try:
        resp = requests.get(
            "https://finnhub.io/api/v1/calendar/economic",
            params={
                "from": today.strftime("%Y-%m-%d"),
                "to": week_out.strftime("%Y-%m-%d"),
                "token": api_key,
            },
            timeout=10,
        )
        resp.raise_for_status()
        events = resp.json().get("economicCalendar", [])
    except Exception as e:
        return [{"event": f"[Calendar error: {e}]", "actual": None,
                 "forecast": None, "previous": None, "surprise": None,
                 "country": "", "date": ""}], []

    releases: list[dict] = []
    upcoming: list[dict] = []
    seen_upcoming: set[str] = set()

    today_str = today.strftime("%Y-%m-%d")
    tomorrow_str = tomorrow.strftime("%Y-%m-%d")

    for ev in events:
        event_date = (ev.get("time") or "")[:10]
        country = (ev.get("country") or "").lower()
        event_name = ev.get("event", "")

        # skip countries we don't care about
        if country not in COUNTRY_FILTERS:
            continue

        # check against that country's keyword whitelist
        if not _matches(event_name, COUNTRY_FILTERS[country]):
            continue

        if event_date == today_str:
            actual = ev.get("actual")
            if actual is None:
                continue          # only show released data

            forecast = ev.get("estimate")
            surprise = None
            if forecast is not None:
                try:
                    diff = float(actual) - float(forecast)
                    surprise = "beat" if diff > 0 else "miss" if diff < 0 else "in-line"
                except (TypeError, ValueError):
                    pass

            releases.append({
                "event": event_name,
                "country": country.upper(),
                "actual": actual,
                "forecast": forecast,
                "previous": ev.get("prev"),
                "surprise": surprise,
                "date": event_date,
            })

        elif event_date >= tomorrow_str:
            importance = (ev.get("impact") or "").lower()
            if importance not in ("high", "medium"):
                continue

            key = f"{event_date}|{event_name}|{country}"
            if key in seen_upcoming:
                continue
            seen_upcoming.add(key)

            upcoming.append({
                "date": event_date,
                "event": event_name,
                "country": country.upper(),
                "importance": importance,
            })

    # US first, then others; within same country sort by event name
    country_order = {"us": 0, "eu": 1, "gb": 2, "jp": 3}
    releases.sort(key=lambda x: (country_order.get(x["country"].lower(), 9), x["event"]))
    upcoming.sort(key=lambda x: (x["date"], country_order.get(x["country"].lower(), 9)))

    if not releases:
        releases = [{"event": "No major macro releases today", "country": "",
                     "actual": None, "forecast": None, "previous": None,
                     "surprise": None, "date": today_str}]

    return releases, upcoming[:30]
