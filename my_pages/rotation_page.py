import datetime as dt

import streamlit as st
from dateutil.relativedelta import relativedelta

from utils.db import load_tickers, load_sector_parents, load_granular_sectors, load_prices
from utils.indicators import compute_jdk_rs
from utils.rrg_chart import build_rrg_figure, format_labels
from utils.tickers import SPY_TICKER, TICKERS_FACTOR_THEMES

LOOKBACK_MONTHS = 12  # historique chargé pour laisser le temps aux indicateurs de se stabiliser




def _compute_rrg(tickers_dict: dict[str, str], asof_date: dt.date):
    """Récupère les prix depuis la DB et calcule RS-Ratio / RS-Momentum en live."""
    start = asof_date - relativedelta(months=LOOKBACK_MONTHS)
    all_tickers = tuple(sorted(set(tickers_dict) | {SPY_TICKER}))
    prices = load_prices(all_tickers, start, asof_date)
    if prices.empty or SPY_TICKER not in prices.columns:
        return None, None, []

    prices = prices.ffill().dropna(how="all")
    available = [t for t in tickers_dict if t in prices.columns]
    if len(available) < 2:
        return None, None, available

    rs_ratio, rs_momentum = compute_jdk_rs(prices, available, SPY_TICKER)
    return rs_ratio, rs_momentum, available


def _render_rrg_chart(tickers_dict: dict[str, str], asof_date: dt.date, tail: int, title: str):
    rs_ratio, rs_momentum, available = _compute_rrg(tickers_dict, asof_date)
    if rs_ratio is None:
        if not available:
            st.warning("Aucune donnée de prix trouvée en base pour cet univers à cette date.")
        else:
            st.warning("Pas assez de tickers disponibles pour construire le RRG.")
        return

    st.caption(f"Dernière donnée disponible : {rs_ratio.dropna(how='all').index.max():%d/%m/%Y}")

    labels = format_labels({t: tickers_dict[t] for t in available})
    fig = build_rrg_figure(rs_ratio, rs_momentum, labels, tail=tail, title=title)
    st.plotly_chart(fig, config={"displayModeBar": False}, use_container_width=True)


def _render_sector_tab(sector_tickers: dict, granular_tickers: dict, region_label: str, key_suffix: str,
                        asof_date: dt.date):
    """Onglet secteur avec drill-down optionnel vers les sous-industries."""
    st.markdown(
        f"<h3 style='font-size:20px;font-weight:700;color:#1e293b;margin-top:24px'>"
        f"Relative Rotation Graph — {region_label} Sectors</h3>",
        unsafe_allow_html=True,
    )

    if len(sector_tickers) < 2:
        st.warning(f"Pas assez de secteurs {region_label} disponibles en base.")
        return

    drillable = {
        sector_tickers[t]: granular_tickers[t]
        for t in granular_tickers
        if t in sector_tickers
    }

    choice = st.selectbox(
        "ETF universe:",
        [f"{region_label} Sectors (global)"] + sorted(drillable.keys()),
        key=f"rrg_universe_{key_suffix}",
    )

    if choice == f"{region_label} Sectors (global)":
        tickers_dict = sector_tickers
        title = f"Relative Rotation Graph — {region_label} Sectors"
    else:
        tickers_dict = drillable[choice]
        title = f"Relative Rotation Graph — {choice} (sub-industries)"

    tail = st.slider("Tail length (days)", min_value=5, max_value=20, value=10, step=1,
                      key=f"rrg_tail_{key_suffix}")

    _render_rrg_chart(tickers_dict, asof_date, tail, title)


def _render_factor_tab(asof_date: dt.date):
    st.markdown(
        "<h3 style='font-size:20px;font-weight:700;color:#1e293b;margin-top:24px'>"
        "Relative Rotation Graph — US Factors</h3>",
        unsafe_allow_html=True,
    )

    factors = load_tickers("US", "factor")

    theme = st.selectbox("Factor opposition:", list(TICKERS_FACTOR_THEMES.keys()), key="rrg_theme_factor")
    theme_tickers = [t for t in TICKERS_FACTOR_THEMES[theme] if t in factors]

    tail = st.slider("Tail length (days)", min_value=5, max_value=20, value=10, step=1,
                      key="rrg_tail_factor")

    if len(theme_tickers) < 2:
        st.warning("Pas assez de tickers disponibles en base pour ce thème.")
        return

    tickers_dict = {t: factors[t] for t in theme_tickers}
    _render_rrg_chart(tickers_dict, asof_date, tail, f"Relative Rotation Graph — {theme}")


def rotation_page():
    st.markdown(
        "<h1 style='font-size:28px;font-weight:800;color:#1e293b;margin-bottom:4px'>Rotation Dashboard</h1>",
        unsafe_allow_html=True,
    )
    asof = st.session_state.asof
    min_date = asof - dt.timedelta(days=182)  # ~6 months
    asof_date = st.slider(
        "Reference date",
        min_value=min_date,
        max_value=asof,
        value=asof,
        format="DD/MM/YYYY",
        help="Go back up to 6 months to see the RRG's position at a past date.",
        key="rrg_asof_date",
    )

    sectors_us_df = load_sector_parents("US")
    sectors_us = dict(zip(sectors_us_df["ticker"], sectors_us_df["name"]))
    sectors_europe_df = load_sector_parents("Europe")
    sectors_europe = dict(zip(sectors_europe_df["ticker"], sectors_europe_df["name"]))
    granular_us = load_granular_sectors("US")
    granular_eu = load_granular_sectors("Europe")

    tab_us, tab_europe, tab_factors = st.tabs(["US Sectors", "Europe Sectors", "Factors"])

    with tab_us:
        _render_sector_tab(sectors_us, granular_us, "US", "us", asof_date)

    with tab_europe:
        _render_sector_tab(sectors_europe, granular_eu, "Europe", "eu", asof_date)

    with tab_factors:
        _render_factor_tab(asof_date)