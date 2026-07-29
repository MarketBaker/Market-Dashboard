"""Calcul en live des indicateurs JdK RS-Ratio / RS-Momentum (Relative Rotation Graphs)."""
import pandas as pd
import numpy as np

def compute_jdk_rs(prices: pd.DataFrame, tickers: list[str], benchmark: str,
                    smooth_window: int = 15, z_window: int = 15, roc_window: int = 4
                    ) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    JdK RS-Ratio / RS-Momentum (méthode Julius de Kempenaer) : force relative
    lissée, recentrée en z-score à 100.
    """
    ref = prices[benchmark]
    rs = 100 * prices[tickers].div(ref, axis=0)
    rs_smooth = rs.rolling(smooth_window).mean()

    roll_mean = rs_smooth.rolling(z_window).mean()
    roll_std = rs_smooth.rolling(z_window).std()
    rs_ratio = 100 + (rs_smooth - roll_mean) / roll_std

    roc = 100 * rs_ratio / rs_ratio.shift(roc_window)
    roc_mean = roc.rolling(z_window).mean()
    roc_std = roc.rolling(z_window).std()
    rs_momentum = 100 + (roc - roc_mean) / roc_std

    return rs_ratio, rs_momentum


def compute_roc(prices: pd.DataFrame, windows: dict[str, int]) -> pd.DataFrame:
    """
    Rate of Change for each window.
    Returns a DataFrame with MultiIndex columns (ticker, window).
    """
    result = {}
    last = prices.iloc[-1]
    for label, n in windows.items():
        if len(prices) > n:
            ref = prices.iloc[-(n + 1)]
            roc = (last / ref - 1) * 100
        else:
            roc = pd.Series(np.nan, index=prices.columns)
        result[label] = roc
    return pd.DataFrame(result)  # index = tickers, columns = window labels


def compute_rs_vs_benchmark(prices: pd.DataFrame, benchmark_ticker: str, windows: dict[str, int]) -> pd.DataFrame:
    """
    Relative strength of each ticker vs benchmark for each window.
    RS = ROC(ticker) - ROC(benchmark)
    """
    if benchmark_ticker not in prices.columns:
        return pd.DataFrame()

    roc = compute_roc(prices, windows)
    benchmark_roc = roc.loc[benchmark_ticker]
    rs = roc.sub(benchmark_roc, axis=1)
    rs = rs.drop(index=benchmark_ticker, errors="ignore")
    rs.columns = [f"RS_{w}" for w in rs.columns]
    return rs

def compute_composite_score(roc_df: pd.DataFrame, weights: dict[str, float]) -> pd.Series:
    """
    Weighted composite momentum score from ROC windows.
    """
    score = pd.Series(0.0, index=roc_df.index)
    for window, w in weights.items():
        if window in roc_df.columns:
            score += roc_df[window].fillna(0) * w
    return score.rename("Score")