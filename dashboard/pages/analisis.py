import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

@st.cache_data
def load_data():
    df = pd.read_parquet("data/processed/fact_trips.parquet")
    if len(df) > 500000:
        df = df.sample(500000, random_state=42)
    return df

def show():
    st.header("📊 Analisis Temporal & Cuaca")

    df = load_data()

    # =====================
    # FILTER SIDEBAR
    # =====================
    st.sidebar.header("Filter Data")
    borough = st.sidebar.multiselect(
        "Borough",
        options=df["PU_Borough"].dropna().unique().tolist(),
        default=df["PU_Borough"].dropna().unique().tolist()
    )
    df_filtered = df[df["PU_Borough"].isin(borough)]

    # =====================
    # GRAFIK 1: Tip per Jam
    # =====================
    st.subheader("Rata-rata Tip per Jam")
    hourly = df_filtered.groupby("hour_of_day")["tip_percentage"].mean().reset_index()
    fig1, ax1 = plt.subplots(figsize=(10, 4))
    ax1.plot(hourly["hour_of_day"], hourly["tip_percentage"], marker="o", color="steelblue")
    ax1.set_xlabel("Jam")
    ax1.set_ylabel("Rata-rata Tip (%)")
    ax1.set_xticks(range(0, 24))
    ax1.grid(True, alpha=0.3)
    st.pyplot(fig1)

    # =====================
    # GRAFIK 2: Tip per Hari
    # =====================
    st.subheader("Rata-rata Tip per Hari")
    day_order = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
    daily = df_filtered.groupby("day_of_week")["tip_percentage"].mean().reindex(day_order).reset_index()
    fig2, ax2 = plt.subplots(figsize=(10, 4))
    bars = ax2.bar(daily["day_of_week"], daily["tip_percentage"], color="coral")
    ax2.set_xlabel("Hari")
    ax2.set_ylabel("Rata-rata Tip (%)")
    ax2.set_xticklabels(daily["day_of_week"], rotation=30)
    ax2.grid(True, alpha=0.3, axis="y")
    st.pyplot(fig2)

    # =====================
    # GRAFIK 3: Tip per Cuaca
    # =====================
    st.subheader("Rata-rata Tip per Kondisi Cuaca")
    weather = df_filtered.groupby("weather_condition")["tip_percentage"].mean().reset_index()
    fig3, ax3 = plt.subplots(figsize=(8, 4))
    ax3.bar(weather["weather_condition"], weather["tip_percentage"], color="mediumseagreen")
    ax3.set_xlabel("Kondisi Cuaca")
    ax3.set_ylabel("Rata-rata Tip (%)")
    ax3.grid(True, alpha=0.3, axis="y")
    st.pyplot(fig3)

    # =====================
    # GRAFIK 4: Distribusi Tip
    # =====================
    st.subheader("Distribusi Tip Percentage")
    fig4, ax4 = plt.subplots(figsize=(10, 4))
    sample = df_filtered["tip_percentage"].sample(min(50000, len(df_filtered)), random_state=42)
    ax4.hist(sample, bins=50, color="mediumpurple", edgecolor="white", range=(0, 50))
    ax4.axvline(x=20, color="red", linestyle="--", label="Threshold 20%")
    ax4.set_xlabel("Tip (%)")
    ax4.set_ylabel("Jumlah Perjalanan")
    ax4.legend()
    ax4.grid(True, alpha=0.3)
    st.pyplot(fig4)

    # =====================
    # RINGKASAN STATISTIK
    # =====================
    st.subheader("Ringkasan Statistik")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Perjalanan", f"{len(df_filtered):,}")
    col2.metric("Avg Tip", f"{df_filtered['tip_percentage'].mean():.1f}%")
    col3.metric("High Tip Rate", f"{df_filtered['high_tip'].mean():.1%}")
    col4.metric("Avg Durasi", f"{df_filtered['duration_minutes'].mean():.1f} menit")
