import datetime as dt

import pandas as pd
import streamlit as st

from utils.db import load_rrg_from_db, long_to_wide
from utils.rrg_chart import build_rrg_figure, format_labels
from utils.tickers import (
    TICKERS_SECTOR_US, TICKERS_GRANULAR_US,
    TICKERS_SECTOR_EUROPE, TICKERS_GRANULAR_EU,
    TICKERS_FACTOR_US, TICKERS_FACTOR_THEMES,
)


def _render_sector_tab(sector_tickers: dict, granular_tickers: dict, region_label: str, key_suffix: str,
                        asof_date: dt.date):
    """Sector tab with optional drill-down into a given sector's sub-industries."""
    st.markdown(
        f"<h3 style='font-size:20px;font-weight:700;color:#1e293b;margin-top:24px'>"
        f"Relative Rotation Graph — {region_label} Sectors</h3>",
        unsafe_allow_html=True,
    )

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

    df_long = load_rrg_from_db(tuple(tickers_dict.keys()))
    df_long = df_long[df_long["date"] <= pd.Timestamp(asof_date)]
    if df_long.empty:
        st.warning("No RRG data found in the database for this universe at this date.")
        return

    st.caption(f"Latest available data: {df_long['date'].max().date():%d/%m/%Y}")

    rs_ratio, rs_momentum = long_to_wide(df_long, tail)

    available = set(rs_ratio.columns) & set(rs_momentum.columns)
    if len(available) < 2:
        st.warning("Not enough data to build the RRG for this universe.")
        return

    labels = format_labels({t: n for t, n in tickers_dict.items() if t in available})
    fig = build_rrg_figure(rs_ratio, rs_momentum, labels, tail=tail, title=title)
    st.plotly_chart(fig, config={"displayModeBar": False}, use_container_width=True)


def _render_factor_tab(asof_date: dt.date):
    st.markdown(
        "<h3 style='font-size:20px;font-weight:700;color:#1e293b;margin-top:24px'>"
        "Relative Rotation Graph — US Factors</h3>",
        unsafe_allow_html=True,
    )

    theme = st.selectbox("Factor opposition:", list(TICKERS_FACTOR_THEMES.keys()), key="rrg_theme_factor")
    theme_tickers = TICKERS_FACTOR_THEMES[theme]

    tail = st.slider("Tail length (days)", min_value=5, max_value=20, value=10, step=1,
                      key="rrg_tail_factor")

    df_long = load_rrg_from_db(tuple(theme_tickers))
    df_long = df_long[df_long["date"] <= pd.Timestamp(asof_date)]
    if df_long.empty:
        st.warning("No RRG data found in the database for this theme at this date.")
        return

    st.caption(f"Latest available data: {df_long['date'].max().date():%d/%m/%Y}")

    rs_ratio, rs_momentum = long_to_wide(df_long, tail)

    available = set(rs_ratio.columns) & set(rs_momentum.columns)
    if len(available) < 2:
        st.warning("Not enough data to build the RRG for this theme.")
        return

    tickers_dict = {t: TICKERS_FACTOR_US[t] for t in theme_tickers if t in available}
    labels = format_labels(tickers_dict)
    fig = build_rrg_figure(rs_ratio, rs_momentum, labels, tail=tail,
                            title=f"Relative Rotation Graph — {theme}")
    st.plotly_chart(fig, config={"displayModeBar": False}, use_container_width=True)


def rotation_page():
    st.markdown(
        "<h1 style='font-size:28px;font-weight:800;color:#1e293b;margin-bottom:4px'>Rotation Dashboard</h1>",
        unsafe_allow_html=True,
    )

    today = dt.date.today()
    min_date = today - dt.timedelta(days=182)  # ~6 months
    asof_date = st.slider(
        "Reference date",
        min_value=min_date,
        max_value=today,
        value=today,
        format="DD/MM/YYYY",
        help="Go back up to 6 months to see the RRG's position at a past date.",
        key="rrg_asof_date",
    )

    tab_us, tab_europe, tab_factors = st.tabs(["US Sectors", "Europe Sectors", "Factors"])

    with tab_us:
        _render_sector_tab(TICKERS_SECTOR_US, TICKERS_GRANULAR_US, "US", "us", asof_date)

    with tab_europe:
        _render_sector_tab(TICKERS_SECTOR_EUROPE, TICKERS_GRANULAR_EU, "Europe", "eu", asof_date)

    with tab_factors:
        _render_factor_tab(asof_date)