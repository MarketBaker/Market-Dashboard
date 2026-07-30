import streamlit as st
from datetime import datetime
from dateutil.relativedelta import relativedelta

from my_pages.rotation_page  import rotation_page
from my_pages.dispersion_page import page_dispersion
from my_pages.momentum_page import page_momentum
from my_pages.price_analysis_page import price_analysis_page

st.set_page_config(
    page_title="Navigation",
    layout="wide"
)


if "asof" not in st.session_state:
    st.session_state.asof = datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)+ relativedelta(days=-1)


SECTIONS = {
    "Market Dashboard": [
        "Momentum Analysis",
        "Rotation Analysis",
        "Dispersion Analysis",
        "Price Analysis",
    ],
}




with st.sidebar:
    section = st.selectbox("Section", list(SECTIONS.keys()))
    page = st.selectbox("Page", SECTIONS[section])

if page == "Momentum Analysis":
    page_momentum()

if page == "Rotation Analysis":
    rotation_page()

elif page=="Dispersion Analysis":
    page_dispersion()

elif page=="Price Analysis":
    price_analysis_page()


