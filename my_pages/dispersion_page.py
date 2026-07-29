import numpy as np
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from dateutil.relativedelta import relativedelta
from utils.db import load_sector_parents, load_prices

TICKERS_DISPERSION = {
    "^DSPX": "SP500 Dispersion",
    "^VIX": "SP500 Implied Volatility",
    "^SPXEW": "SP500 EQUAL WEIGHT",
    "^SPX": "SP500",
}


def show_stacked_dispersion(prices):
    """
    Empile 2 graphiques (VIX/VIXEQ/Dispersion, puis écart de performance
    SP500 vs SP500 Equal Weight) avec un axe des dates partagé.
    """
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.06,
        subplot_titles=(
            "VIX, VIXEQ, Dispersion",
            "Écart de performance cumulée : SP500 vs SP500 Equal Weight",
        ),
        row_heights=[0.5, 0.5],
    )

    row1 = [
        ("^VIX", TICKERS_DISPERSION.get("^VIX", "VIX"), "dark blue"),
        ("VIXEQ", TICKERS_DISPERSION.get("VIXEQ", "VIXEQ"), "orange"),
        ("^DSPX", TICKERS_DISPERSION.get("^DSPX", "SP500 Dispersion"), "red"),
    ]
    for ticker, name, color in row1:
        if ticker not in prices.columns:
            continue
        series = prices[ticker].dropna()
        fig.add_trace(
            go.Scatter(
                x=series.index,
                y=series.values,
                name=name,
                mode="lines",
                line=dict(color=color),
                legend="legend1",
            ),
            row=1, col=1,
        )

    if "^SPX" in prices.columns and "^SPXEW" in prices.columns:
        spx = prices["^SPX"].dropna()
        spxew = prices["^SPXEW"].dropna()
        idx = spx.index.intersection(spxew.index)
        ret_spx = spx.loc[idx] / spx.loc[idx].iloc[0] - 1
        ret_spxew = spxew.loc[idx] / spxew.loc[idx].iloc[0] - 1
        diff = (ret_spx - ret_spxew) * 100
        fig.add_trace(
            go.Scatter(
                x=diff.index,
                y=diff.values,
                name="SP500 / SP500 EW (perf %)",
                mode="lines",
                line=dict(color="green"),
                legend="legend2",
            ),
            row=2, col=1,
        )

    fig.update_xaxes(showgrid=True, matches="x")
    fig.update_yaxes(showgrid=True, gridcolor="#DFDFDF")

    domain1 = fig.layout.yaxis.domain
    domain2 = fig.layout.yaxis2.domain

    fig.update_layout(
        height=800,
        plot_bgcolor="white",
        margin=dict(l=0, r=20, t=60, b=40),
        legend1=dict(
            font=dict(size=12), orientation="h",
            yanchor="top", y=domain1[1], xanchor="center", x=0.5,
            bgcolor="rgba(255,255,255,0.6)",
        ),
        legend2=dict(
            font=dict(size=12), orientation="h",
            yanchor="top", y=domain2[1], xanchor="center", x=0.5,
            bgcolor="rgba(255,255,255,0.6)",
        ),
        hovermode="x unified",
    )

    st.plotly_chart(fig, config={"displayModeBar": False}, width="stretch", key="stacked_dispersion")


def show_sector_dispersion(spx, prices_sector, roll_window=30):
    """
    Empile 2 graphiques : dispersion réalisée entre le SP500 et ses secteurs
    (analogue réalisé de la relation VIXEQ² = VIX² + DSPX²), puis corrélation
    moyenne implicite du portefeuille de secteurs (décomposition de variance,
    à la CBOE, appliquée aux vols réalisées).
    """
    spx = spx.dropna()
    sectors = prices_sector.dropna(how="all")
    idx = spx.index.intersection(sectors.index)
    spx = spx.loc[idx]
    sectors = sectors.loc[idx].ffill()
    n = sectors.shape[1]

    ret_spx = spx.pct_change()
    ret_sectors = sectors.pct_change()

    vol_spx = ret_spx.rolling(roll_window).std() * np.sqrt(252) * 100
    vol_sectors = ret_sectors.rolling(roll_window).std() * np.sqrt(252) * 100
    var_spx = vol_spx ** 2

    # Dispersion réalisée : vol moyenne des secteurs vs vol de l'indice, en quadrature
    avg_vol_sectors = vol_sectors.mean(axis=1)  # moyenne simple des vols
    dispersion = np.sqrt((avg_vol_sectors ** 2 - var_spx).clip(lower=0))

    # Corrélation moyenne implicite du portefeuille (décomposition de variance) :
    avg_var_sectors = (vol_sectors ** 2).mean(axis=1)  # moyenne des vols²

    denom = avg_vol_sectors ** 2 - avg_var_sectors / n
    rho_avg = (var_spx - avg_var_sectors / n) / denom


    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.08,
        subplot_titles=(
            "Dispersion réalisée : SP500 vs secteurs (vol composants vs vol indice)",
            "Corrélation moyenne implicite du portefeuille de secteurs",
        ),
        row_heights=[0.5, 0.5],
    )

    fig.add_trace(
        go.Scatter(
            x=dispersion.index, y=dispersion.values,
            name="Dispersion réalisée (secteurs vs SP500)",
            mode="lines", line=dict(color="red"),
            legend="legend1",
        ),
        row=1, col=1,
    )

    fig.add_trace(
        go.Scatter(
            x=rho_avg.index, y=rho_avg.values,
            name="Corrélation moyenne implicite (secteurs)",
            mode="lines", line=dict(color="purple"),
            legend="legend2",
        ),
        row=2, col=1,
    )

    fig.update_xaxes(showgrid=True, matches="x")
    fig.update_yaxes(showgrid=True, gridcolor="#DFDFDF")
    fig.update_yaxes(range=[-1, 1], row=2, col=1)

    domain1 = fig.layout.yaxis.domain
    domain2 = fig.layout.yaxis2.domain

    fig.update_layout(
        height=800,
        plot_bgcolor="white",
        margin=dict(l=0, r=20, t=60, b=40),
        legend1=dict(
            font=dict(size=12), orientation="h",
            yanchor="top", y=domain1[1], xanchor="center", x=0.5,
            bgcolor="rgba(255,255,255,0.6)",
        ),
        legend2=dict(
            font=dict(size=11), orientation="h",
            yanchor="top", y=domain2[1], xanchor="center", x=0.5,
            bgcolor="rgba(255,255,255,0.6)",
        ),
        hovermode="x unified",
    )

    st.plotly_chart(fig, config={"displayModeBar": False}, width="stretch", key="sector_dispersion")


def page_dispersion():
    st.markdown(
        "<h1 style='font-size:28px;font-weight:800;color:#1e293b;margin-bottom:4px'>Dispersion Dashboard</h1>",
        unsafe_allow_html=True,
    )

    tab_global, tab_sector = st.tabs(
        ["Global", "US Sectors"]
    )


    asof = st.session_state.asof
    default_start = asof + relativedelta(months=-12)


    prices = load_prices(tuple(TICKERS_DISPERSION.keys()), default_start, asof)
    prices["VIXEQ"] = np.sqrt(prices["^VIX"]*prices["^VIX"] + prices["^DSPX"]*prices["^DSPX"])

    sectors_us_df = load_sector_parents("US")
    sectors_us = dict(zip(sectors_us_df["ticker"], sectors_us_df["name"]))
    prices_sector = load_prices(tuple(sectors_us), default_start, asof)

    with tab_global:
        show_stacked_dispersion(prices)

    with tab_sector:
        show_sector_dispersion(prices["^SPX"], prices_sector)

















