import streamlit as st
from utils import load_data
import pandas as pd
import matplotlib.pyplot as plt


def show():
    st.header("📊 Analisis Temporal & Cuaca")

    df = load_data()

    # FILTER SIDEBAR
    st.sidebar.header("Filter Data")
    borough = st.sidebar.multiselect(
        "Borough",
        options=df["PU_Borough"].dropna().unique().tolist(),
        default=df["PU_Borough"].dropna().unique().tolist()
    )
    df_filtered = df[df["PU_Borough"].isin(borough)]

    # METRIK RINGKASAN
    st.subheader("Ringkasan Statistik")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Perjalanan", f"{len(df_filtered):,}")
    col2.metric("Avg Tip", f"{df_filtered['tip_percentage'].mean():.1f}%")
    col3.metric("High Tip Rate (>25%)", f"{df_filtered['high_tip_v2'].mean():.1%}")
    col4.metric("Avg Durasi", f"{df_filtered['duration_minutes'].mean():.1f} menit")

    # GRAFIK 1: Tip per Jam
    st.subheader("Rata-rata Tip per Jam")
    hourly = df_filtered.groupby("hour_of_day")["tip_percentage"].mean().reset_index()
    peak_hour = hourly.loc[hourly["tip_percentage"].idxmax(), "hour_of_day"]
    peak_val = hourly["tip_percentage"].max()
    fig1, ax1 = plt.subplots(figsize=(10, 4))
    ax1.plot(hourly["hour_of_day"], hourly["tip_percentage"], marker="o", color="steelblue")
    ax1.axvline(x=peak_hour, color="red", linestyle="--", alpha=0.5)
    ax1.set_xlabel("Jam")
    ax1.set_ylabel("Rata-rata Tip (%)")
    ax1.set_xticks(range(0, 24))
    ax1.grid(True, alpha=0.3)
    st.pyplot(fig1)
    st.info(f"💡 Tip tertinggi terjadi pada jam **{int(peak_hour)}:00** dengan rata-rata **{peak_val:.1f}%**. "
            f"Pengemudi disarankan aktif pada jam tersebut untuk memaksimalkan pendapatan.")

    # GRAFIK 2: Tip per Hari
    st.subheader("Rata-rata Tip per Hari")
    day_order = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
    daily = df_filtered.groupby("day_of_week")["tip_percentage"].mean().reindex(day_order).reset_index()
    best_day = daily.loc[daily["tip_percentage"].idxmax(), "day_of_week"]
    best_val = daily["tip_percentage"].max()
    fig2, ax2 = plt.subplots(figsize=(10, 4))
    ax2.bar(daily["day_of_week"], daily["tip_percentage"], color="coral")
    ax2.set_xlabel("Hari")
    ax2.set_ylabel("Rata-rata Tip (%)")
    ax2.set_xticklabels(daily["day_of_week"], rotation=30)
    ax2.grid(True, alpha=0.3, axis="y")
    st.pyplot(fig2)
    st.info(f"💡 Hari **{best_day}** menghasilkan rata-rata tip tertinggi sebesar **{best_val:.1f}%**.")

    # GRAFIK 3: Tip per Cuaca
    st.subheader("Rata-rata Tip per Kondisi Cuaca")
    weather = df_filtered.groupby("weather_condition")["tip_percentage"].mean().reset_index()
    best_weather = weather.loc[weather["tip_percentage"].idxmax(), "weather_condition"]
    best_weather_val = weather["tip_percentage"].max()
    fig3, ax3 = plt.subplots(figsize=(8, 4))
    ax3.bar(weather["weather_condition"], weather["tip_percentage"], color="mediumseagreen")
    ax3.set_xlabel("Kondisi Cuaca")
    ax3.set_ylabel("Rata-rata Tip (%)")
    ax3.grid(True, alpha=0.3, axis="y")
    st.pyplot(fig3)
    st.info(f"💡 Kondisi cuaca **{best_weather}** menghasilkan tip tertinggi ({best_weather_val:.1f}%). "
            f"Integrasi data cuaca Open-Meteo membantu mengidentifikasi pola ini.")

    # GRAFIK 4: Distribusi Tip
    st.subheader("Distribusi Tip Percentage")
    fig4, ax4 = plt.subplots(figsize=(10, 4))
    sample = df_filtered["tip_percentage"].sample(min(50000, len(df_filtered)), random_state=42)
    ax4.hist(sample, bins=50, color="mediumpurple", edgecolor="white", range=(0, 50))
    ax4.axvline(x=25, color="red", linestyle="--", label="Threshold High Tip (25%)")
    ax4.set_xlabel("Tip (%)")
    ax4.set_ylabel("Jumlah Perjalanan")
    ax4.legend()
    ax4.grid(True, alpha=0.3)
    st.pyplot(fig4)
    high_tip_pct = df_filtered["high_tip_v2"].mean() * 100
    st.info(f"💡 Sebanyak **{high_tip_pct:.1f}%** perjalanan menghasilkan tip di atas 25%. "
            f"Garis merah menunjukkan batas threshold tip tinggi yang digunakan dalam model ML.")

    # GRAFIK 5: ML Probability Distribution
    st.subheader("Distribusi Probabilitas Prediksi ML")
    fig5, ax5 = plt.subplots(figsize=(10, 4))
    sample_prob = df_filtered["ml_probability"].sample(min(50000, len(df_filtered)), random_state=42)
    ax5.hist(sample_prob, bins=50, color="steelblue", edgecolor="white")
    ax5.axvline(x=0.5, color="red", linestyle="--", label="Threshold Prediksi (0.5)")
    ax5.set_xlabel("Probabilitas Tip Tinggi")
    ax5.set_ylabel("Jumlah Perjalanan")
    ax5.legend()
    ax5.grid(True, alpha=0.3)
    st.pyplot(fig5)
    st.info(f"💡 Grafik ini menunjukkan distribusi probabilitas prediksi model Random Forest. "
            f"Perjalanan dengan probabilitas >0.5 diprediksi menghasilkan tip tinggi (>25%).")
