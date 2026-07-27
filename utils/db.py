import psycopg2
import pandas as pd
import streamlit as st

DB_URL = st.secrets["SUPABASE_DB_URL"]


@st.cache_resource
def _get_connection():
    """Connexion mise en cache pour toute la session Streamlit."""
    return psycopg2.connect(DB_URL, connect_timeout=10)


@st.cache_data(ttl=3600)
def load_rrg_from_db(tickers: tuple[str, ...]) -> pd.DataFrame:
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


def long_to_wide(df_long: pd.DataFrame, tail: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Repivote le format long en deux DataFrames wide (date x ticker), tronqués au tail voulu."""
    rs_ratio = df_long.pivot(index="date", columns="ticker", values="rs_ratio").sort_index()
    rs_momentum = df_long.pivot(index="date", columns="ticker", values="rs_momentum").sort_index()
    return rs_ratio.iloc[-tail:], rs_momentum.iloc[-tail:]