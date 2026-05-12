# 🚕 Analisis Tip Taksi NYC 2025

## Deskripsi
Proyek ini menganalisis faktor-faktor yang mempengaruhi pemberian tip tinggi (>20%) pada perjalanan taksi di NYC, dengan integrasi data cuaca eksternal dan prediksi menggunakan machine learning.

## Periode Data
Januari – Maret 2025 (3 bulan)

## Dataset
- NYC TLC Yellow Taxi Trip Records (Jan-Mar 2025)
- Taxi Zone Lookup Table
- Open-Meteo Historical Weather API

## Pipeline
1. **Data Ingestion** — Download data TLC, zone lookup, dan weather API
2. **Preprocessing & Cleaning** — Filter anomali, join data eksternal
3. **Feature Engineering** — Buat kolom turunan (jam, hari, durasi, tip_percentage, high_tip)
4. **Machine Learning** — Random Forest untuk prediksi tip tinggi
5. **Visualisasi** — Dashboard Streamlit interaktif

## Cara Menjalankan

### 1. Install dependencies
pip install -r requirements.txt

### 2. Jalankan pipeline
python scripts/ingestion.py
python scripts/preprocessing.py
python scripts/ml_training.py

### 3. Jalankan dashboard
streamlit run dashboard/app.py

## Tools
- Python, Pandas, Scikit-learn
- Streamlit, Folium
- Prefect (pipeline orchestration)
- GitHub Codespaces

### Struktur Folder

```text
tugas-akhir-rdv/
├── data/
│   ├── raw/          # Data mentah TLC
│   ├── processed/    # Data bersih + weather + zones
│   └── models/       # Model ML (.pkl)
├── scripts/          # Pipeline scripts
├── dashboard/        # Streamlit app
└── laporan/          # Dokumentasi
