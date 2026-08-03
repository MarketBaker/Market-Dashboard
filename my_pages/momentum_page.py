import pandas as pd
import numpy as np
import streamlit as st
import plotly.graph_objects as go
from dateutil.relativedelta import relativedelta
from utils.db import load_sector_parents, load_prices, load_granular_sectors, load_regions
from utils.tickers import SPY_TICKER, STX50_TICKER, ROC_WINDOWS, ROC_WEIGHTS
from utils.indicators import compute_composite_score, compute_rs_vs_benchmark, compute_roc
# ─────────────────────────────────────────────
#  HELPERS — DISPLAY
# ─────────────────────────────────────────────

def _regime_color(label: str) -> str:
    return {"RISK-ON": "#16a34a", "RISK-OFF": "#dc2626", "NEUTRE": "#d97706"}.get(label, "#6b7280")


def _signal_color(val: float, positive_is_good: bool = True) -> str:
    if val is None:
        return "#6b7280"
    if positive_is_good:
        return "#16a34a" if val > 0 else "#dc2626"
    return "#dc2626" if val > 0 else "#16a34a"


def _metric_card(col, label: str, value: str, sub: str = "", color: str = "#1e293b"):
    col.markdown(
        f"""
        <div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:10px;
                    padding:14px 18px;text-align:center;height:100%">
            <div style="font-size:12px;color:#64748b;text-transform:uppercase;
                        letter-spacing:0.05em;margin-bottom:4px">{label}</div>
            <div style="font-size:24px;font-weight:700;color:{color}">{value}</div>
            <div style="font-size:12px;color:#64748b;margin-top:4px">{sub}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _section_header(title: str, subtitle: str = ""):
    st.markdown(
        f"""
        <div style="margin:28px 0 12px 0">
            <span style="font-size:18px;font-weight:700;color:#1e293b">{title}</span>
            {"<span style='font-size:13px;color:#64748b;margin-left:10px'>" + subtitle + "</span>" if subtitle else ""}
        </div>
        <hr style="margin:0 0 16px 0;border:none;border-top:2px solid #e2e8f0"/>
        """,
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────
#  BLOC 2 — RANKING SECTORIEL US
# ─────────────────────────────────────────────

def _render_heatmap(prices: pd.DataFrame, dict_tickers: dict, index: str, chart_key: str):
    """Renders the ROC/RS heatmap + bar chart expander for a given set of tickers."""
    tickers = list(dict_tickers.keys()) + [index]
    available = [t for t in tickers if t in prices.columns]
    if not available:
        st.warning("Données indisponibles pour ce sous-groupe.")
        return

    sector_prices = prices[available]
    roc_df = compute_roc(sector_prices, ROC_WINDOWS)
    rs_df  = compute_rs_vs_benchmark(sector_prices, index, {"1M": 21, "3M": 63, "6M": 180})

    roc_display = roc_df.drop(index=index, errors="ignore")
    score = compute_composite_score(roc_display, ROC_WEIGHTS)
    score.index   = [f"{t} - {dict_tickers.get(t)}" for t in score.index]

    display = roc_display.copy()

    if not rs_df.empty:
        rs_display = rs_df.copy()
        display = display.join(rs_display, how="left")

    display.index = [f"{dict_tickers.get(t)}- {t}" for t in display.index]
    display["Score"] = score
    display = display.sort_values("Score", ascending=False)

    heatmap_cols = [c for c in ["1S", "1M", "3M", "6M", "RS_1M", "RS_3M", "RS_6M", "Score"] if c in display.columns]
    heatmap_data = display[heatmap_cols].copy()
    col_labels = {
        "1S": "ROC 1S", "1M": "ROC 1M", "3M": "ROC 3M", "6M": "ROC 6M",
        "RS_1M": "RS 1M", "RS_3M": "RS 3M", "RS_6M": "RS 6M", "Score": "Score ★",
    }
    z    = heatmap_data.values.astype(float)
    text = [[f"{v:+.1f}%" if not np.isnan(v) else "N/A" for v in row] for row in z]

    fig = go.Figure(go.Heatmap(
        z=z,
        x=[col_labels.get(c, c) for c in heatmap_cols],
        y=list(heatmap_data.index),
        text=text, texttemplate="%{text}", textfont={"size": 12},
        colorscale="RdYlGn", zmid=0, showscale=True,
        colorbar=dict(title="% / Score", thickness=14),
    ))
    fig.update_layout(
        height=max(350, 45 * len(heatmap_data) + 80),
        margin=dict(l=10, r=10, t=30, b=10),
        plot_bgcolor="white",
        xaxis=dict(side="top"),
        yaxis=dict(autorange="reversed"),
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False},
                    key=f"heatmap_{chart_key}")

    with st.expander("Bar chart — Score composite"):
        bar_colors = ["#16a34a" if v >= 0 else "#dc2626" for v in display["Score"]]
        fig2 = go.Figure(go.Bar(
            x=list(display.index), y=display["Score"].tolist(),
            marker_color=bar_colors,
            text=[f"{v:+.1f}" for v in display["Score"]],
            textposition="outside",
        ))
        fig2.update_layout(
            height=380, margin=dict(l=10, r=10, t=20, b=10),
            plot_bgcolor="white",
            yaxis=dict(zeroline=True, zerolinecolor="black", zerolinewidth=2),
        )
        st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False},
                        key=f"bar_{chart_key}")


def show_sector_ranking(prices: pd.DataFrame, dict_tickers: dict, title: str, index: str,
                        granular_map: dict | None = None):
    _section_header(title, f"ROC · Relative Strength vs {index} · Score composite")

    available_top = [t for t in list(dict_tickers.keys()) + [index] if t in prices.columns]
    if not available_top:
        st.warning("Données sectorielles indisponibles.")
        return

    _render_heatmap(prices, dict_tickers, index, chart_key=title)

    # ── Drill-down ────────────────────────────────────────────────────────────
    if granular_map:
        # Keep only sectors that have granular data AND price data for at least one sub-ticker
        drillable = {
            dict_tickers[t]: granular_map[t]
            for t in granular_map
            if t in dict_tickers and any(s in prices.columns for s in granular_map[t])
        }
        if drillable:
            st.markdown(
                "<div style='margin:20px 0 8px 0;font-size:15px;font-weight:600;color:#1e293b'>"
                "Drill-down sous-sectoriel</div>",
                unsafe_allow_html=True,
            )
            choice = st.selectbox(
                "Zoomer sur un secteur :",
                ["— Choisir —"] + sorted(drillable.keys()),
                key=f"drill_{title}",
            )
            if choice != "— Choisir —":
                sub_tickers = drillable[choice]
                st.markdown(
                    f"<div style='font-size:13px;color:#64748b;margin-bottom:8px'>"
                    f"Sous-secteurs · <b>{choice}</b> — benchmark : {index}</div>",
                    unsafe_allow_html=True,
                )
                _render_heatmap(prices, sub_tickers, index, chart_key=f"{title}_{choice}")





def page_momentum():
    st.markdown(
        "<h1 style='font-size:28px;font-weight:800;color:#1e293b;margin-bottom:4px'>Momentum Dashboard</h1>",
        unsafe_allow_html=True,
    )

    asof = st.session_state.asof
    default_start = asof + relativedelta(months=-12)

    #TODO too many calls here
    tickers_us_df = load_regions("US")
    tickers_us = dict(zip(tickers_us_df["ticker"], tickers_us_df["name"]))
    tickers_europe_df = load_regions("Europe")
    tickers_europe = dict(zip(tickers_europe_df["ticker"], tickers_europe_df["name"]))

    prices_us = load_prices(tuple(tickers_us), default_start, asof)
    prices_eu = load_prices(tuple(tickers_europe), default_start, asof)

    sectors_us_df = load_sector_parents("US")
    sectors_us = dict(zip(sectors_us_df["ticker"], sectors_us_df["name"]))
    sectors_europe_df = load_sector_parents("Europe")
    sectors_europe = dict(zip(sectors_europe_df["ticker"], sectors_europe_df["name"]))
    granular_us = load_granular_sectors("US")
    granular_eu = load_granular_sectors("Europe")


    st.markdown("<div style='margin:8px 0'/>", unsafe_allow_html=True)
    t_us, t_eu = st.tabs(
        ["Ranking US", "Ranking EU"]
    )
    with t_us:
        show_sector_ranking(prices_us, sectors_us, "Ranking sectoriel US", SPY_TICKER,
                            granular_map=granular_us)
    with t_eu:
        show_sector_ranking(prices_eu, sectors_europe, "Ranking sectoriel EU", STX50_TICKER,
                            granular_map=granular_eu)
