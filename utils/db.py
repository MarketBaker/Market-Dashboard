import datetime as dt
import psycopg2
import pandas as pd
import streamlit as st

DB_URL = st.secrets["SUPABASE_DB_URL"]


@st.cache_resource
def _get_connection():
    """Connexion mise en cache pour toute la session Streamlit."""
    return psycopg2.connect(DB_URL, connect_timeout=10)


@st.cache_data(ttl=3600)
def load_tickers(region: str, category: str) -> dict[str, str]:
    """Retourne {ticker: name} pour les tickers de premier niveau (sub_sector NULL)
    d'une region/category donnée (ex: region='US', category='factor')."""
    conn = _get_connection()
    query = """
        SELECT ticker, name FROM tickers
        WHERE region = %(region)s AND category = %(category)s AND sub_sector IS NULL
        ORDER BY ticker
    """
    df = pd.read_sql(query, conn, params={"region": region, "category": category})
    return dict(zip(df["ticker"], df["name"]))


@st.cache_data(ttl=3600)
def load_sector_parents(region: str) -> pd.DataFrame:
    """Retourne (ticker, name, sector) pour les ETF secteur de premier niveau d'une région."""
    conn = _get_connection()
    query = """
        SELECT ticker, name, sector FROM tickers
        WHERE region = %(region)s AND category = 'sector' AND sub_sector IS NULL
        ORDER BY ticker
    """
    return pd.read_sql(query, conn, params={"region": region})


@st.cache_data(ttl=3600)
def load_granular_tickers(region: str) -> pd.DataFrame:
    """Retourne (ticker, name, sector, sub_sector) pour les tickers de drill-down d'une région."""
    conn = _get_connection()
    query = """
        SELECT ticker, name, sector, sub_sector FROM tickers
        WHERE region = %(region)s AND category = 'sector' AND sub_sector IS NOT NULL
        ORDER BY ticker
    """
    return pd.read_sql(query, conn, params={"region": region})


@st.cache_data(ttl=3600)
def load_dispersion_tickers(region: str) -> pd.DataFrame:
    """Retourne (ticker, name, sector, sub_sector) pour les tickers de drill-down d'une région."""
    conn = _get_connection()
    query = """
        SELECT ticker, name, sector, sub_sector FROM tickers
        WHERE region = %(region)s AND category = 'sector' AND sub_sector IS NOT NULL
        ORDER BY ticker
    """
    return pd.read_sql(query, conn, params={"region": region})


@st.cache_data(ttl=3600)
def load_prices(tickers: tuple[str, ...], start: dt.date, end: dt.date) -> pd.DataFrame:
    """
    Lit les prix de clôture depuis la table `prices` pour une liste de tickers
    entre deux dates. Retourne un DataFrame wide (index=date, colonnes=ticker).
    """
    conn = _get_connection()
    query = """
        SELECT date, ticker, close
        FROM prices
        WHERE ticker IN %(tickers)s AND date BETWEEN %(start)s AND %(end)s
        ORDER BY date ASC
    """
    df = pd.read_sql(query, conn, params={"tickers": tickers, "start": start, "end": end})
    if df.empty:
        return df
    df["date"] = pd.to_datetime(df["date"])
    return df.pivot(index="date", columns="ticker", values="close").sort_index()

@st.cache_data(ttl=3600)
def load_all_tickers() -> pd.DataFrame:
    """Retourne tous les tickers connus de la table `tickers` (ticker, name, region, category)."""
    conn = _get_connection()
    query = "SELECT ticker, name, region, category FROM tickers ORDER BY ticker"
    return pd.read_sql(query, conn)


@st.cache_data(ttl=3600)
def load_ohlc(ticker: str, start: dt.date, end: dt.date) -> pd.DataFrame:
    """
    Lit l'OHLC depuis la table `prices` pour un ticker unique entre deux dates.
    Retourne un DataFrame indexé par date avec les colonnes Open, High, Low, Close.
    """
    conn = _get_connection()
    query = """
        SELECT date, open, high, low, close
        FROM prices
        WHERE ticker = %(ticker)s AND date BETWEEN %(start)s AND %(end)s
        ORDER BY date ASC
    """
    df = pd.read_sql(query, conn, params={"ticker": ticker, "start": start, "end": end})
    if df.empty:
        return df
    df["date"] = pd.to_datetime(df["date"])
    df = df.set_index("date").sort_index()
    df.columns = ["Open", "High", "Low", "Close"]
    return df


@st.cache_data(ttl=3600)
def load_granular_sectors(region: str) -> dict[str, dict[str, str]]:
    """Construit {ticker_secteur_parent: {ticker_granulaire: nom}} depuis la DB,
    en reliant chaque ticker de drill-down à son secteur parent via la colonne `sector`."""
    parents = load_sector_parents(region)
    children = load_granular_tickers(region)
    parent_ticker_by_sector = dict(zip(parents["sector"], parents["ticker"]))

    grouped: dict[str, dict[str, str]] = {}
    for _, row in children.iterrows():
        parent_ticker = parent_ticker_by_sector.get(row["sector"])
        if parent_ticker is None:
            continue
        grouped.setdefault(parent_ticker, {})[row["ticker"]] = row["name"]
    return grouped

@st.cache_data(ttl=3600)
def load_regions(region: str) -> pd.DataFrame:
    """Retourne (ticker, name, sector) pour les ETF d'une région."""
    conn = _get_connection()
    query = """
        SELECT ticker, name, sector, region FROM tickers
        WHERE region = %(region)s and sector != 'stock'
        ORDER BY ticker
    """
    return pd.read_sql(query, conn, params={"region": region})