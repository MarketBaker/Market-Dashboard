import streamlit as st
import psycopg2
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

DB_URL = st.secrets["SUPABASE_DB_URL"]


@st.cache_resource
def _get_connection():
    """Connexion mise en cache pour toute la session Streamlit."""
    return psycopg2.connect(DB_URL, connect_timeout=10)



@st.cache_data(ttl=3600)
def _load_rrg_from_db(tickers: tuple[str, ...]) -> pd.DataFrame:
    """
    Lit l'historique RRG pour une liste de tickers depuis Supabase.
    Retourne un DataFrame long (date, ticker, rs_ratio, rs_momentum).
    """
    conn = _get_connection()
    query = """
        SELECT date, ticker, rs_ratio, rs_momentum
        FROM rrg_indicators
        WHERE ticker IN %(tickers)s
        ORDER BY date ASC
    """
    df = pd.read_sql(query, conn, params={"tickers": tickers})
    df["date"] = pd.to_datetime(df["date"])
    return df


def _long_to_wide(df_long: pd.DataFrame, tail: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Repivote le format long en deux DataFrames wide (date x ticker), tronqués au tail voulu."""
    rs_ratio = df_long.pivot(index="date", columns="ticker", values="rs_ratio").sort_index()
    rs_momentum = df_long.pivot(index="date", columns="ticker", values="rs_momentum").sort_index()
    return rs_ratio.iloc[-tail:], rs_momentum.iloc[-tail:]


def _build_rrg_figure(rs_ratio: pd.DataFrame, rs_momentum: pd.DataFrame, labels: dict, tail: int = 12,
                       title: str = "Relative Rotation Graph — Secteurs US vs SPY") -> go.Figure:
    fig = go.Figure()
    palette = px.colors.qualitative.Dark24
    colors = {ticker: palette[i % len(palette)] for i, ticker in enumerate(labels)}

    all_x, all_y = [], []

    for ticker, label in labels.items():
        if ticker not in rs_ratio.columns or ticker not in rs_momentum.columns:
            continue
        x = rs_ratio[ticker].dropna()
        y = rs_momentum[ticker].dropna()
        idx = x.index.intersection(y.index)[-tail:]
        if idx.empty:
            continue
        x, y = x.loc[idx], y.loc[idx]
        color = colors[ticker]
        all_x.extend(x.tolist())
        all_y.extend(y.tolist())

        fig.add_trace(go.Scatter(
            x=x, y=y, mode="lines+markers", name=label,
            line=dict(color=color, width=1.5),
            marker=dict(size=5, color=color),
            opacity=0.7,
            hovertemplate=f"{label}<br>RS-Ratio: %{{x:.2f}}<br>RS-Momentum: %{{y:.2f}}<extra></extra>",
        ))
        fig.add_trace(go.Scatter(
            x=[x.iloc[-1]], y=[y.iloc[-1]], mode="markers+text",
            marker=dict(size=12, color=color, line=dict(color="black", width=1)),
            text=[label], textposition="top center",
            showlegend=False, hoverinfo="skip",
        ))

    if all_x and all_y:
        pad_x = max((max(all_x) - min(all_x)) * 0.15, 1)
        pad_y = max((max(all_y) - min(all_y)) * 0.15, 1)
        x_range = [min(all_x) - pad_x, max(all_x) + pad_x]
        y_range = [min(all_y) - pad_y, max(all_y) + pad_y]
    else:
        x_range, y_range = [95, 105], [95, 105]

    quadrants = [
        dict(x0=100, x1=x_range[1], y0=100, y1=y_range[1], color="rgba(46,204,113,0.12)"),   # Leading
        dict(x0=100, x1=x_range[1], y0=y_range[0], y1=100, color="rgba(241,196,15,0.12)"),   # Weakening
        dict(x0=x_range[0], x1=100, y0=y_range[0], y1=100, color="rgba(231,76,60,0.12)"),    # Lagging
        dict(x0=x_range[0], x1=100, y0=100, y1=y_range[1], color="rgba(52,152,219,0.12)"),   # Improving
    ]
    for q in quadrants:
        fig.add_shape(type="rect", x0=q["x0"], x1=q["x1"], y0=q["y0"], y1=q["y1"],
                      fillcolor=q["color"], line=dict(width=0), layer="below")

    quadrant_labels = [
        ("Leading", x_range[1], y_range[1], "right", "top"),
        ("Weakening", x_range[1], y_range[0], "right", "bottom"),
        ("Lagging", x_range[0], y_range[0], "left", "bottom"),
        ("Improving", x_range[0], y_range[1], "left", "top"),
    ]
    for text, x, y, xanchor, yanchor in quadrant_labels:
        fig.add_annotation(x=x, y=y, text=text, showarrow=False,
                            xanchor=xanchor, yanchor=yanchor,
                            font=dict(size=13, color="#94a3b8"))

    fig.add_hline(y=100, line=dict(color="grey", width=1))
    fig.add_vline(x=100, line=dict(color="grey", width=1))

    fig.update_layout(
        title=dict(text=title, font=dict(size=22)),
        xaxis=dict(title="JdK RS-Ratio", range=x_range, showgrid=True, gridcolor="#DFDFDF",
                   zeroline=False, showline=True, linecolor="black"),
        yaxis=dict(title="JdK RS-Momentum", range=y_range, showgrid=True, gridcolor="#DFDFDF",
                   zeroline=False, showline=True, linecolor="black"),
        plot_bgcolor="white",
        height=700,
        margin=dict(l=0, r=20, t=80, b=40),
        legend=dict(font=dict(size=13), orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
    )
    return fig

TICKERS_SECTOR_US = {
    "XLK": "Technologie",
    "XLV": "Santé",
    "XLF": "Finance",
    "XLI": "Industrie",
    "XLY": "Conso. Discrétionnaire",
    "XLP": "Conso. de Base",
    "XLB": "Matériaux",
    "XLE": "Énergie",
    "XLU": "Utilities",
    "XLC": "Télécom",
}

def rotation_page():
    st.markdown(
        "<h3 style='font-size:20px;font-weight:700;color:#1e293b;margin-top:24px'>Relative Rotation Graph — Secteurs US</h3>",
        unsafe_allow_html=True,
    )

    tail = st.slider("Longueur de la traîne (jours)", min_value=5, max_value=40, value=12, step=1, key="rrg_tail_us")

    df_long = _load_rrg_from_db(tuple(TICKERS_SECTOR_US.keys()))

    if df_long.empty:
        st.warning("Aucune donnée RRG trouvée en base pour cet univers.")
        return


    rs_ratio, rs_momentum = _long_to_wide(df_long, tail)

    available_tickers = set(rs_ratio.columns) & set(rs_momentum.columns)
    if len(available_tickers) < 2:
        st.warning("Données insuffisantes pour construire le RRG sur cet univers.")
        return

    fig = _build_rrg_figure(rs_ratio, rs_momentum, TICKERS_SECTOR_US, tail=tail, title="US Sectors Rotation")
    st.plotly_chart(fig, config={"displayModeBar": False}, use_container_width=True)