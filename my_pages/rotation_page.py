import streamlit as st

from utils.db import load_rrg_from_db, long_to_wide
from utils.rrg_chart import build_rrg_figure, format_labels
from utils.tickers import (
    TICKERS_SECTOR_US, TICKERS_GRANULAR_US,
    TICKERS_SECTOR_EUROPE, TICKERS_GRANULAR_EU,
    TICKERS_FACTOR_US, TICKERS_FACTOR_THEMES,
)


def _render_sector_tab(sector_tickers: dict, granular_tickers: dict, region_label: str, key_suffix: str):
    """Onglet secteurs avec drill-down optionnel vers les sous-secteurs d'un secteur donné."""
    st.markdown(
        f"<h3 style='font-size:20px;font-weight:700;color:#1e293b;margin-top:24px'>"
        f"Relative Rotation Graph — Secteurs {region_label}</h3>",
        unsafe_allow_html=True,
    )

    drillable = {
        sector_tickers[t]: granular_tickers[t]
        for t in granular_tickers
        if t in sector_tickers
    }

    choice = st.selectbox(
        "Univers d'ETFs :",
        [f"Secteurs {region_label} (global)"] + sorted(drillable.keys()),
        key=f"rrg_universe_{key_suffix}",
    )

    if choice == f"Secteurs {region_label} (global)":
        tickers_dict = sector_tickers
        title = f"Relative Rotation Graph — Secteurs {region_label}"
    else:
        tickers_dict = drillable[choice]
        title = f"Relative Rotation Graph — {choice} (sous-secteurs)"

    tail = st.slider("Longueur de la traîne (jours)", min_value=5, max_value=40, value=12, step=1,
                      key=f"rrg_tail_{key_suffix}")

    df_long = load_rrg_from_db(tuple(tickers_dict.keys()))
    if df_long.empty:
        st.warning("Aucune donnée RRG trouvée en base pour cet univers.")
        return

    rs_ratio, rs_momentum = long_to_wide(df_long, tail)

    available = set(rs_ratio.columns) & set(rs_momentum.columns)
    if len(available) < 2:
        st.warning("Données insuffisantes pour construire le RRG sur cet univers.")
        return

    labels = format_labels({t: n for t, n in tickers_dict.items() if t in available})
    fig = build_rrg_figure(rs_ratio, rs_momentum, labels, tail=tail, title=title)
    st.plotly_chart(fig, config={"displayModeBar": False}, use_container_width=True)


def _render_factor_tab():
    st.markdown(
        "<h3 style='font-size:20px;font-weight:700;color:#1e293b;margin-top:24px'>"
        "Relative Rotation Graph — Facteurs US</h3>",
        unsafe_allow_html=True,
    )

    theme = st.selectbox("Opposition de facteurs :", list(TICKERS_FACTOR_THEMES.keys()), key="rrg_theme_factor")
    theme_tickers = TICKERS_FACTOR_THEMES[theme]

    tail = st.slider("Longueur de la traîne (jours)", min_value=5, max_value=40, value=12, step=1,
                      key="rrg_tail_factor")

    df_long = load_rrg_from_db(tuple(theme_tickers))
    if df_long.empty:
        st.warning("Aucune donnée RRG trouvée en base pour ce thème.")
        return

    rs_ratio, rs_momentum = long_to_wide(df_long, tail)

    available = set(rs_ratio.columns) & set(rs_momentum.columns)
    if len(available) < 2:
        st.warning("Données insuffisantes pour construire le RRG sur ce thème.")
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

    tab_us, tab_europe, tab_factors = st.tabs(["Secteurs US", "Secteurs Europe", "Facteurs"])

    with tab_us:
        _render_sector_tab(TICKERS_SECTOR_US, TICKERS_GRANULAR_US, "US", "us")

    with tab_europe:
        _render_sector_tab(TICKERS_SECTOR_EUROPE, TICKERS_GRANULAR_EU, "Europe", "eu")

    with tab_factors:
        _render_factor_tab()