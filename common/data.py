import pandas as pd
import streamlit as st

@st.cache_data(ttl=60*60*6)
def load_name_lookup():
    return pd.read_csv("data/nse_stocks_.csv")
