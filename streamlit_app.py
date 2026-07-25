import streamlit as st
import psycopg2
import pandas as pd
import json

DB_URL = st.secrets["SUPABASE_DB_URL"]

@st.cache_data(ttl=3600)  # cache 1h pour éviter de spam la DB à chaque interaction
def load_indicators():
    conn = psycopg2.connect(DB_URL, connect_timeout=10)
    df = pd.read_sql("SELECT * FROM indicators ORDER BY date DESC", conn)
    conn.close()
    return df

st.title("📊 Market Indicators Dashboard")

df = load_indicators()
latest_date = df["date"].max()
st.caption(f"Dernière mise à jour : {latest_date}")

st.dataframe(df[df["date"] == latest_date][["indicator_name", "value"]])