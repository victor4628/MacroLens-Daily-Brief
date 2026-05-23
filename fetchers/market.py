import yfinance as yf
from datetime import datetime, timedelta

from config.assets import ASSETS, ANOMALY_THRESHOLD


def fetch_market_data() -> tuple[list[dict], list[dict]]:
    """
    Download yesterday's closing prices for all tracked assets.
    Returns (market_data, anomalies) where anomalies are moves >= ANOMALY_THRESHOLD.
    Fetches 7 calendar days to handle weekends and market holidays gracefully.
    """
    end = datetime.now()
    start = end - timedelta(days=7)

    tickers_flat = [t for cat in ASSETS.values() for t in cat]
    try:
        raw = yf.download(
            tickers_flat,
            start=start.strftime("%Y-%m-%d"),
            end=end.strftime("%Y-%m-%d"),
            progress=False,
            auto_adjust=True,
        )
        close = raw["Close"] if "Close" in raw.columns.get_level_values(0) else raw
    except Exception as e:
        print(f"[market] batch download failed: {e}")
        close = None

    market_data: list[dict] = []
    anomalies: list[dict] = []

    for category, tickers in ASSETS.items():
        for ticker, name in tickers.items():
            try:
                if close is not None and ticker in close.columns:
                    series = close[ticker].dropna()
                else:
                    # fallback: individual download
                    series = yf.download(
                        ticker,
                        start=start.strftime("%Y-%m-%d"),
                        end=end.strftime("%Y-%m-%d"),
                        progress=False,
                        auto_adjust=True,
                    )["Close"].dropna()

                if len(series) < 2:
                    continue

                prev_close = float(series.iloc[-2])
                last_close = float(series.iloc[-1])
                ret = (last_close - prev_close) / prev_close

                is_anomaly = abs(ret) >= ANOMALY_THRESHOLD
                if ret > 0.005:
                    signal = "bullish"
                elif ret < -0.005:
                    signal = "bearish"
                else:
                    signal = "neutral"

                asset: dict = {
                    "ticker": ticker,
                    "name": name,
                    "category": category,
                    "price": round(last_close, 4),
                    "prev_close": round(prev_close, 4),
                    "return_1d": round(ret * 100, 2),
                    "is_anomaly": is_anomaly,
                    "signal": signal,
                }
                market_data.append(asset)
                if is_anomaly:
                    anomalies.append(asset)

            except Exception as e:
                print(f"[market] skipping {ticker}: {e}")

    return market_data, anomalies
