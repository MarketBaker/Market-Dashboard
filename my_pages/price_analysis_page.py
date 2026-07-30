import streamlit as st
import pandas as pd
import numpy as np
from dateutil.relativedelta import relativedelta

from utils.db import load_ohlc, load_prices, load_all_tickers
from utils.graphs import compute_graph, style_dataframe, compute_graph_dual_axis
import plotly.express as px
import plotly.graph_objects as go


def compute_rsi(prices, period=14):
    """
    Calcule le RSI à partir d'une série de prix.

    Parameters:
        prices (pd.Series ou list): Série des prix.
        period (int): Période du RSI (14 par défaut).

    Returns:
        pd.Series: Valeurs du RSI.
    """
    delta = prices.diff()

    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.ewm(alpha=1 / period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / period, adjust=False).mean()

    rs = avg_gain / avg_loss

    rsi = 100 - (100 / (1 + rs))
    return rsi


def compute_bollinger(prices, window=20, k=2):
    """
    Calcule les bandes de Bollinger.

    Parameters:
        prices (pd.Series ou list): Série de prix.
        window (int): Taille de la moyenne mobile.
        k (float): Nombre d'écarts-types.

    Returns:
        pd.DataFrame: colonnes ['middle', 'upper', 'lower']
    """
    middle = prices.rolling(window).mean()
    std = prices.rolling(window).std()

    upper = middle + k * std
    lower = middle - k * std

    return pd.DataFrame({
        "middle": middle,
        "upper": upper,
        "lower": lower
    })


def plot_rsi_graph(series, title, y_title=None,
                        vlines=None,  # liste de dates pour les lignes verticales
                        upper=70, lower=30):

    fig = go.Figure()

    fig.add_trace(go.Scatter(x=series.index, y=series, mode="lines"))

    fig.add_shape(
        type="rect",
        xref="x", yref="y",
        x0=series.index.min(), x1=series.index.max(),
        y0=upper, y1=100,
        fillcolor="lightgrey",
        opacity=0.3,
        line_width=0,
    )

    fig.add_shape(
        type="rect",
        xref="x", yref="y",
        x0=series.index.min(), x1=series.index.max(),
        y0=0, y1=lower,
        fillcolor="lightgrey",
        opacity=0.3,
        line_width=0,
    )

    fig.add_hline(y=upper, line_dash="dash", line_color="grey")
    fig.add_hline(y=lower, line_dash="dash", line_color="grey")

    if vlines is not None:
        for x in vlines:
            fig.add_vline(x=x, line_dash="dot", line_color="red")

    fig.update_layout(
        title=title,
        height=300,
        margin=dict(l=10, r=10, t=40, b=10),
        yaxis_title=y_title,
    )
    fig.update_yaxes(range=[0, 100])

    return fig


def plot_bollinger(prices, boll, title="Bollinger Bands"):
    """
    Trace le prix + bandes de Bollinger.

    Parameters:
        prices (pd.Series): Prix.
        boll (pd.DataFrame): Résultat de compute_bollinger().
        title (str): Titre du graphique.
    """

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=prices.index,
        y=prices,
        name="Price",
        mode="lines"
    ))

    fig.add_trace(go.Scatter(
        x=boll.index,
        y=boll["middle"],
        name="Middle Band",
        line=dict(color="red", width=1)
    ))

    fig.add_trace(go.Scatter(
        x=boll.index,
        y=boll["upper"],
        name="Upper Band",
        line=dict(color="grey", width=1)
    ))

    fig.add_trace(go.Scatter(
        x=boll.index,
        y=boll["lower"],
        name="Lower Band",
        line=dict(color="grey", width=1)
    ))

    fig.add_trace(go.Scatter(
        x=boll.index,
        y=boll["upper"],
        mode="lines",
        line=dict(width=0),
        showlegend=False
    ))
    fig.add_trace(go.Scatter(
        x=boll.index,
        y=boll["lower"],
        mode="lines",
        fill="tonexty",
        fillcolor="rgba(150,150,150,0.15)",
        line=dict(width=0),
        name="Band Area"
    ))

    fig.update_layout(
        title=title,
        height=400,
        margin=dict(l=20, r=20, t=40, b=20),
        showlegend=False,
    )

    return fig


def plot_price_candles(df, title="Price"):
    """
    Trace un chandelier (Open/High/Low/Close) avec MA 7j et MA 20j.
    """
    fig = go.Figure()

    fig.add_trace(
        go.Candlestick(
            x=df.index,
            open=df["Open"],
            high=df["High"],
            low=df["Low"],
            close=df["Close"],
            name="Price"
        )
    )
    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df["MA 7d"],
            line=dict(color="blue", width=1.5),
            name="MA 7d"
        )
    )
    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df["MA 20d"],
            line=dict(color="green", width=1.5),
            name="MA 20d"
        )
    )

    fig.update_layout(
        title=title,
        height=500,
        margin=dict(l=20, r=20, t=40, b=20),
        showlegend=False,
        xaxis=dict(rangeslider=dict(visible=False))
    )

    return fig


def _performance_decomposition(histo, window=20):
    log_intraday = np.log(histo["Close"] / histo["Open"])
    log_overnight = np.log(histo["Open"] / histo["Close"].shift(1))
    log_return = np.log(histo["Close"]) - np.log(histo["Close"].shift(1))

    roll_intraday = log_intraday.rolling(window).sum()
    roll_overnight = log_overnight.rolling(window).sum()
    roll_return = log_return.rolling(window).sum()

    all_returns = pd.concat([roll_intraday, roll_overnight, roll_return], axis=1)
    all_returns.columns = ["Intraday Performance", "Overnight Performance", "Day Over Day Performance"]
    return all_returns


def _gain_frequency_indicator(histo, window=14):
    day_over_day_return = histo["Close"].pct_change()
    up_days = day_over_day_return > 0

    mean_up = day_over_day_return.where(day_over_day_return > 0).rolling(window, min_periods=1).mean() * 100
    mean_down = -day_over_day_return.where(day_over_day_return < 0).rolling(window, min_periods=1).mean() * 100
    freq_up = up_days.rolling(window).mean() * 100

    all_metrics = pd.concat([mean_up, mean_down, freq_up], axis=1)
    all_metrics.columns = ["Average Gain", "Average Loss", "Up Frenquency"]
    return all_metrics


def _compute_atr(histo, window=14):
    prev_close = histo["Close"].shift(1)
    true_range = pd.concat([
        histo["High"] - histo["Low"],
        (histo["High"] - prev_close).abs(),
        (histo["Low"] - prev_close).abs()
    ], axis=1).max(axis=1)

    atr_pct = (true_range / prev_close * 100)
    rolling_atr = atr_pct.rolling(window).mean()
    return rolling_atr


def _select_ticker(tickers_df, label, key, default=None):
    options = tickers_df["ticker"].tolist()
    names = dict(zip(tickers_df["ticker"], tickers_df["name"]))
    index = options.index(default) if default in options else 0
    return st.selectbox(
        label,
        options=options,
        index=index,
        format_func=lambda t: f"{t} — {names[t]}",
        key=key,
    )


def price_analysis_page():

    tickers_df = load_all_tickers()

    default_start = st.session_state.asof + relativedelta(months=-12)

    selected_dates = st.slider(
        "Choisis une range :",
        min_value=default_start,
        max_value=st.session_state.asof,
        value=(default_start, st.session_state.asof),
        format="DD/MM/YYYY"
    )
    ticker = _select_ticker(tickers_df, "Ticker :", key="ticker0", default="NVDA")
    histo = load_ohlc(ticker, selected_dates[0], selected_dates[1])

    if histo is None or histo.empty:
        st.warning("No Ticker found")
        return

    if len(histo) <= 1:
        st.warning("Please select more than one date")
        return

    histo["MA 7d"] = histo["Close"].rolling(5).mean()
    histo["MA 20d"] = histo["Close"].rolling(20).mean()
    perf = 100 * (histo["Close"].iloc[-1] / histo["Close"].iloc[0] - 1)

    closing_prices = histo[["Close", "MA 7d", "MA 20d"]].rename(columns={"Close": ticker})

    tab_technical_analysis, tab_momentum, tab_single, tab_correl = st.tabs(
        ["Technical Analysis", "Momentum", "Returns analysis", "Correlation analysis"]
    )

    with tab_technical_analysis:
        st.metric(label="Historical Performance", value=f"{np.round(perf, 2)} %")

        fig = plot_price_candles(histo)
        st.plotly_chart(fig, width='stretch', config={"displayModeBar": False})

        rolling_atr = _compute_atr(histo)
        fig_price_atr = compute_graph(rolling_atr.to_frame(), [],
                                       "Average True Range - Volatility",
                                       "Date",
                                       "Volatility")
        st.plotly_chart(fig_price_atr, config={"displayModeBar": False}, width='stretch', key="fig_price_atr")

        rsi = compute_rsi(histo["Close"])
        fig_rsi = plot_rsi_graph(rsi, "RSI")
        st.plotly_chart(fig_rsi, config={"displayModeBar": False}, width='stretch', key="fig_rsi")

        bollinger = compute_bollinger(histo["Close"])
        fig_bollinger = plot_bollinger(histo["Close"], bollinger)
        st.plotly_chart(fig_bollinger, config={"displayModeBar": False}, width='stretch', key="fig_bollinger")

    with tab_momentum:
        all_returns = _performance_decomposition(histo)
        fig_price_performance = compute_graph(all_returns, [],
                                    "Historical Performance - Intraday vs Overnight vs Day Over Day",
                                    "Date",
                                    "Performance")
        st.plotly_chart(fig_price_performance, config={"displayModeBar": False}, width='stretch', key="fig_price_performance")

        frequency_indicator = _gain_frequency_indicator(histo)

        fig_price_correl = compute_graph_dual_axis(frequency_indicator,
                                   "Average Gain",
                                   "Up Frenquency",
                                   "Historical Prices", "Average Loss")
        st.plotly_chart(fig_price_correl, config={"displayModeBar": False}, width='stretch', key="frequency_indicator")

    with tab_single:
        st.metric(label="Historical Performance", value=f"{np.round(perf, 2)} %")

        fig_price = compute_graph(closing_prices, [],
                                    "Historical Price",
                                    "Date",
                                    "Price")
        st.plotly_chart(fig_price, config={"displayModeBar": False}, width='stretch', key="fig_price_2")

        st.header("Quantiles")
        default_window = st.text_input("Please select a rolling window: ", value=5, key="default_window")
        try:
            default_window = int(default_window)
        except:
            st.warning("Default window must be an integer.")
            return

        rel_returns = closing_prices[[ticker]].pct_change(default_window).iloc[default_window:]

        q = [0.99, 0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2, 0.1, 0.01]
        df_quantiles = rel_returns.quantile(q)
        df_quantiles.index *= 100

        distribution_col = st.columns(2)
        fig = px.histogram(
            100 * rel_returns,
            nbins=30,
            histnorm='probability density',
            title="Distribution des rendements"
        )
        distribution_col[0].plotly_chart(fig)
        distribution_col[1].table(style_dataframe(df_quantiles, percent_cols=[ticker]))

        shock_choice = st.columns(2)
        shock_type = shock_choice[0].selectbox("Absolute or Relative: ", ("Absolute", "Relative"), key="shock_type")

        if shock_type == "Absolute":
            message = "Please select a shock: "
        else:
            message = "Please select a % shock: "

        return_to_check = shock_choice[1].text_input(message, value=3, key="return_to_check")

        if shock_type == "Relative":
            try:
                return_to_check = float(return_to_check) / 100
            except:
                st.warning("Return must be a number.")

            if return_to_check >= 0:
                proba = 100 * (rel_returns.values >= return_to_check).sum() / len(rel_returns)
            else:
                proba = 100 * (rel_returns.values < return_to_check).sum() / len(rel_returns)

            equivalent = return_to_check * closing_prices[ticker].iloc[-1]
            shock_choice[0].metric(label="Equivalent", value=f"{np.round(equivalent, 2)}")

        else:
            try:
                return_to_check = float(return_to_check) / closing_prices[ticker].iloc[-1]
            except:
                st.warning("Return must be a number.")

            if return_to_check >= 0:
                proba = 100 * (rel_returns.values >= return_to_check).sum() / len(rel_returns)
            else:
                proba = 100 * (rel_returns.values < return_to_check).sum() / len(rel_returns)

            equivalent = 100 * return_to_check
            shock_choice[0].metric(label="Equivalent", value=f"{np.round(equivalent, 2)} %")

        shock_choice[1].metric(label="Historical Probability", value=f"{np.round(proba, 2)} %")

    with tab_correl:
        ticker2 = _select_ticker(tickers_df, "Please select a ticker: ", key="ticker2", default="^GSPC")

        histo2 = load_prices(tuple([ticker2]), selected_dates[0], selected_dates[1])
        if histo2 is None or histo2.empty:
            st.warning("No Ticker found")
            return

        histo_full = pd.concat([closing_prices[[ticker]], histo2], axis=1)
        log_returns = (np.log(histo_full) - np.log(histo_full.shift(1))).iloc[1:]
        correl = 100 * log_returns.corr().iloc[1, 0]

        to_show = st.columns(3)
        perf2 = 100 * (histo2[ticker2].iloc[-1] / histo2[ticker2].iloc[0] - 1)

        to_show[0].metric(label=f"Historical Performance {ticker}", value=f"{np.round(perf, 2)} %")
        to_show[1].metric(label=f"Historical Performance {ticker2}", value=f"{np.round(perf2, 2)} %")
        to_show[2].metric(label="Correlation", value=f"{np.round(correl, 2)} %")

        fig_price_correl = compute_graph_dual_axis(histo_full,
                                   histo_full.columns[0],
                                   histo_full.columns[1],
                                   "Historical Prices")
        st.plotly_chart(fig_price_correl, config={"displayModeBar": False}, width='stretch', key="fig_price_correl")