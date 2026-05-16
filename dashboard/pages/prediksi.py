import streamlit as st
import pandas as pd
import joblib

@st.cache_resource
def load_model():
    model = joblib.load("data/models/random_forest_tip_model.pkl")
    le_day = joblib.load("data/models/le_day.pkl")
    le_weather = joblib.load("data/models/le_weather.pkl")
    return model, le_day, le_weather

@st.cache_data
def load_zones():
    zones = pd.read_csv("data/processed/dim_zones.csv")
    return zones[["LocationID", "Zone", "Borough"]].dropna()

def show():
    st.header("🤖 Prediksi Tip Tinggi")
    st.markdown("Masukkan detail perjalanan untuk memprediksi apakah penumpang akan memberikan tip tinggi (>20%)")

    model, le_day, le_weather = load_model()
    zones = load_zones()

    # Buat pilihan zona: "Nama Zona (Borough)" -> LocationID
    zone_options = {
        f"{row['Zone']} ({row['Borough']})": row['LocationID']
        for _, row in zones.iterrows()
    }

    col1, col2 = st.columns(2)

    with col1:
        jam = st.slider("Jam Penjemputan", 0, 23, 12)
        hari = st.selectbox("Hari", ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"])
        jarak = st.number_input("Jarak Perjalanan (mil)", min_value=0.1, max_value=50.0, value=2.5, step=0.1)
        durasi = st.number_input("Estimasi Durasi (menit)", min_value=1, max_value=120, value=15)

    with col2:
        penumpang = st.number_input("Jumlah Penumpang", min_value=1, max_value=6, value=1)
        zona_label = st.selectbox("Zona Penjemputan", options=list(zone_options.keys()))
        zona_id = zone_options[zona_label]
        cuaca = st.selectbox("Kondisi Cuaca", ["Clear", "Light Rain", "Heavy Rain", "Snow"])

    if st.button("🔍 Prediksi Sekarang", type="primary"):
        try:
            hari_encoded = le_day.transform([hari])[0]
        except:
            st.error("Hari tidak dikenal oleh model. Coba pilih hari lain.")
            return

        try:
            cuaca_encoded = le_weather.transform([cuaca])[0]
        except:
            st.error("Kondisi cuaca tidak dikenal oleh model. Coba pilih kondisi lain.")
            return

        input_data = pd.DataFrame([{
            "hour_of_day": jam,
            "day_of_week": hari_encoded,
            "trip_distance": jarak,
            "passenger_count": penumpang,
            "PULocationID": zona_id,
            "weather_condition": cuaca_encoded,
            "duration_minutes": durasi
        }])

        pred = model.predict(input_data)[0]
        prob = model.predict_proba(input_data)[0]

        st.divider()

        if pred == 1:
            st.success("✅ **Kemungkinan Tip Tinggi (>20%)**")
        else:
            st.warning("⚠️ **Kemungkinan Tip Rendah atau Normal**")

        col_a, col_b = st.columns(2)
        col_a.metric("Probabilitas Tip Tinggi", f"{prob[1]:.1%}")
        col_b.metric("Probabilitas Tip Normal", f"{prob[0]:.1%}")

        st.divider()
        st.subheader("💡 Rekomendasi untuk Pengemudi")
        if prob[1] >= 0.7:
            st.info(f"Kondisi sangat baik! Perjalanan dari **{zona_label}** pada jam **{jam}:00** "
                    f"hari **{hari}** berpotensi tinggi menghasilkan tip >20%.")
        elif prob[1] >= 0.5:
            st.info(f"Kondisi cukup baik. Berikan pelayanan terbaik untuk meningkatkan peluang tip tinggi.")
        else:
            st.info(f"Pertimbangkan mencari penumpang di zona atau jam yang berbeda "
                    f"untuk peluang tip lebih tinggi.")
