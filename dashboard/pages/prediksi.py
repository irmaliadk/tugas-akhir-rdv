import streamlit as st
import pandas as pd
import joblib
import numpy as np

@st.cache_resource
def load_model():
    model = joblib.load("data/models/random_forest_tip_model.pkl")
    le_day = joblib.load("data/models/le_day.pkl")
    le_weather = joblib.load("data/models/le_weather.pkl")
    return model, le_day, le_weather

def show():
    st.header("🤖 Prediksi Tip Tinggi")
    st.markdown("Masukkan detail perjalanan untuk memprediksi apakah penumpang akan memberikan tip tinggi (>20%)")

    model, le_day, le_weather = load_model()

    # =====================
    # FORM INPUT
    # =====================
    col1, col2 = st.columns(2)

    with col1:
        jam = st.slider("Jam Penjemputan", 0, 23, 12)
        hari = st.selectbox("Hari", ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"])
        jarak = st.number_input("Jarak Perjalanan (mil)", min_value=0.1, max_value=50.0, value=2.5, step=0.1)
        durasi = st.number_input("Estimasi Durasi (menit)", min_value=1, max_value=120, value=15)

    with col2:
        penumpang = st.number_input("Jumlah Penumpang", min_value=1, max_value=6, value=1)
        zona = st.number_input("Zona Penjemputan (LocationID 1-265)", min_value=1, max_value=265, value=161)
        cuaca = st.selectbox("Kondisi Cuaca", ["Clear", "Light Rain", "Heavy Rain", "Snow"])

    # =====================
    # PREDIKSI
    # =====================
    if st.button("🔍 Prediksi Sekarang", type="primary"):
        try:
            hari_encoded = le_day.transform([hari])[0]
            cuaca_encoded = le_weather.transform([cuaca])[0]
        except:
            # Jika label tidak dikenal, gunakan 0
            hari_encoded = 0
            cuaca_encoded = 0

        input_data = pd.DataFrame([{
            "hour_of_day": jam,
            "day_of_week": hari_encoded,
            "trip_distance": jarak,
            "passenger_count": penumpang,
            "PULocationID": zona,
            "weather_condition": cuaca_encoded,
            "duration_minutes": durasi
        }])

        pred = model.predict(input_data)[0]
        prob = model.predict_proba(input_data)[0]

        st.divider()

        if pred == 1:
            st.success(f"✅ **Kemungkinan Tip Tinggi (>20%)**")
        else:
            st.warning(f"⚠️ **Kemungkinan Tip Rendah atau Normal**")

        col_a, col_b = st.columns(2)
        col_a.metric("Probabilitas Tip Tinggi", f"{prob[1]:.1%}")
        col_b.metric("Probabilitas Tip Normal", f"{prob[0]:.1%}")

        st.divider()
        st.subheader("💡 Rekomendasi untuk Pengemudi")
        if prob[1] >= 0.7:
            st.info("Kondisi sangat baik! Perjalanan ini berpotensi menghasilkan tip tinggi.")
        elif prob[1] >= 0.5:
            st.info("Kondisi cukup baik. Berikan pelayanan terbaik untuk meningkatkan peluang tip tinggi.")
        else:
            st.info("Pertimbangkan mencari penumpang di zona atau jam yang berbeda untuk peluang tip lebih tinggi.")
