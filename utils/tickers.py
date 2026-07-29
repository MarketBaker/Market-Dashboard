SPY_TICKER = "SPY"
STX50_TICKER = "^STOXX"


TICKERS_FACTOR_THEMES = {
    "Value vs Growth":             ["VLUE", "IWF"],
    "Quality vs Value":            ["QUAL", "VLUE"],
    "Momentum vs Low Volatility":  ["MTUM", "USMV"],
    "High Beta vs Low Volatility": ["SPHB", "USMV"],
    "Quality vs High Beta":        ["QUAL", "SPHB"],
    "Size vs Quality":             ["SIZE", "QUAL"],
}


# ROC windows in trading days (approx)
ROC_WINDOWS = {
    "1S": 5,
    "1M": 21,
    "3M": 63,
    "6M": 126,
}

# Score composite weights (sum = 1)
ROC_WEIGHTS = {
    "1S": 0.15,
    "1M": 0.35,
    "3M": 0.30,
    "6M": 0.20,
}