ASSETS: dict[str, dict[str, str]] = {
    "US Equities": {
        "SPY": "S&P 500 ETF",
        "QQQ": "Nasdaq 100 ETF",
        "DIA": "Dow Jones ETF",
        "IWM": "Russell 2000 ETF",
        "XLK": "Technology ETF",
        "XLF": "Financials ETF",
    },
    "US Treasuries": {
        "SHY": "2Y Treasury ETF",
        "IEF": "10Y Treasury ETF",
        "TLT": "20Y+ Treasury ETF",
    },
    "Credit": {
        "LQD": "Investment Grade Bond ETF",
        "HYG": "High Yield Bond ETF",
    },
    "Commodities": {
        "GLD": "Gold ETF",
        "SLV": "Silver ETF",
        "USO": "Oil ETF",
        "UNG": "Natural Gas ETF",
    },
    "FX": {
        "UUP": "US Dollar Index ETF",
        "FXE": "Euro ETF",
        "FXY": "Japanese Yen ETF",
    },
    "Crypto": {
        "BTC-USD": "Bitcoin",
        "ETH-USD": "Ethereum",
    },
}

SECTOR_ETFS: dict[str, str] = {
    "XLK": "Technology",
    "XLF": "Financials",
    "XLV": "Healthcare",
    "XLE": "Energy",
    "XLI": "Industrials",
    "XLC": "Communication Services",
    "XLY": "Consumer Discretionary",
    "XLP": "Consumer Staples",
    "XLB": "Materials",
    "XLRE": "Real Estate",
    "XLU": "Utilities",
}

ANOMALY_THRESHOLD = 0.02  # flag moves >= 2%
