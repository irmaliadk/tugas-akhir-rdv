import pandas as pd
import streamlit as st

@st.cache_data
def load_data():
    """Load fact_trips.parquet dengan sampling 500k baris"""
    df = pd.read_parquet("data/processed/fact_trips.parquet")
    if len(df) > 500000:
        df = df.sample(500000, random_state=42)
    return df
