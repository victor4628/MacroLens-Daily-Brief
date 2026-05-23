import yfinance as yf
from datetime import datetime, timedelta

from config.assets import SECTOR_ETFS


def fetch_sector_performance() -> list[dict]:
    """
    Fetch 1-day, 5-day, and 1-month returns for all US sector ETFs via yfinance.
    Sorted by 1-month performance descending.
    """
    end = datetime.now()
    start = end - timedelta(days=40)  # ~1 month of trading days + buffer

    tickers = list(SECTOR_ETFS.keys())
    try:
        raw = yf.download(
            tickers,
            start=start.strftime("%Y-%m-%d"),
            end=end.strftime("%Y-%m-%d"),
            progress=False,
            auto_adjust=True,
        )
        close = raw["Close"] if "Close" in raw.columns.get_level_values(0) else raw
    except Exception as e:
        print(f"[sectors] batch download failed: {e}")
        close = None

    results: list[dict] = []

    for ticker, sector in SECTOR_ETFS.items():
        try:
            if close is not None and ticker in close.columns:
                series = close[ticker].dropna()
            else:
                series = yf.download(
                    ticker,
                    start=start.strftime("%Y-%m-%d"),
                    end=end.strftime("%Y-%m-%d"),
                    progress=False,
                    auto_adjust=True,
                )["Close"].dropna()

            if len(series) < 2:
                continue

            last = float(series.iloc[-1])
            p1d = float(series.iloc[-2]) if len(series) >= 2 else last
            p5d = float(series.iloc[-6]) if len(series) >= 6 else p1d
            p1m = float(series.iloc[-22]) if len(series) >= 22 else p5d

            results.append({
                "ticker": ticker,
                "sector": sector,
                "price": round(last, 2),
                "return_1d": round((last - p1d) / p1d * 100, 2),
                "return_5d": round((last - p5d) / p5d * 100, 2),
                "return_1m": round((last - p1m) / p1m * 100, 2),
            })
        except Exception as e:
            print(f"[sectors] skipping {ticker}: {e}")

    results.sort(key=lambda x: x["return_1m"], reverse=True)
    return results
