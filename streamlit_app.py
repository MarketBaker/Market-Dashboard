import streamlit as st
from my_pages.rotation_page  import rotation_page


st.set_page_config(
    page_title="Navigation",
    layout="wide"
)

rotation_page()



