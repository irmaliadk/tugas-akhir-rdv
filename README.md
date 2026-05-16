# 🚕 Analisis dan Prediksi Tip Tinggi Taksi NYC 2025

## 📌 Identitas Proyek

| Aspek | Detail |
|---|---|
| **Judul** | Prediksi Tip Tinggi & Analisis Spasial-Temporal Perjalanan Taksi NYC Berbasis Data Cuaca |
| **Mata Kuliah** | Rekayasa Data dan Visualisasi |
| **Periode Data** | Januari – Maret 2025 (3 bulan) |
| **Dataset Utama** | NYC TLC Yellow Taxi Trip Records |
| **Dataset Eksternal** | Open-Meteo Historical Weather API |

---

## 👥 Anggota Kelompok & Pembagian Tugas

| NIM | Nama | Role | Tugas |
|---|---|---|---|
| 235150200111013 | Irmalia Dwi Kautsar | Data Architect & Project Leader | Menentukan tujuan proyek, merancang arsitektur pipeline, mendesain skema data.
| 235150200111045 | Faiz Habibina Umiyabi | Data Engineer | Menulis script ingestion.py (download TLC + weather API), preprocessing.py (ETL dengan DuckDB), feature_engineering.py, mengatur Prefect pipeline |
| 235150201111008 | Muhammad Bagas Anugrah | Data Analyst & ML Engineer | Menulis ml_training.py (Random Forest), membangun dashboard Streamlit (peta, analisis, prediksi), analisis insight dari data |

---

## 🎯 Rumusan Masalah

> **"Faktor-faktor apa saja yang mempengaruhi keputusan penumpang taksi di NYC untuk memberikan tip tinggi (>25% dari tarif), dan bagaimana pola spasial-temporal dari perjalanan dengan tip tinggi tersebut?"**

### Pertanyaan Analisis
1. Di zona/borough mana rata-rata tip tertinggi dan terendah?
2. Bagaimana pengaruh jam dan hari terhadap probabilitas tip tinggi?
3. Apakah kondisi cuaca mempengaruhi kecenderungan memberi tip tinggi?
4. Kombinasi faktor apa yang paling memprediksi tip tinggi?
5. Bagaimana rekomendasi untuk pengemudi berdasarkan temuan data?

---

## 🗂️ Dataset

### 1. NYC TLC Yellow Taxi Trip Records
- **Sumber:** https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page
- **Format:** Parquet
- **Periode:** Januari – Maret 2025
- **Ukuran awal:** ~185 MB (11.198.026 baris)
- **Ukuran setelah cleaning:** ~157 MB (7.335.871 baris)

| Kolom | Tipe | Keterangan | Alasan Dipilih |
|---|---|---|---|
| tpep_pickup_datetime | datetime | Waktu penjemputan | Untuk analisis temporal (jam, hari) |
| tpep_dropoff_datetime | datetime | Waktu menurunkan penumpang | Untuk hitung durasi perjalanan |
| passenger_count | integer | Jumlah penumpang | Fitur ML |
| trip_distance | float | Jarak perjalanan (mil) | Fitur ML, berkorelasi dengan tip |
| PULocationID | integer | ID zona penjemputan | Untuk analisis spasial |
| DOLocationID | integer | ID zona tujuan | Untuk join dengan zona lookup |
| payment_type | integer | Tipe pembayaran | Filter: hanya kartu kredit (type=1) yang mencatat tip |
| fare_amount | float | Tarif dasar | Untuk hitung tip_percentage |
| tip_amount | float | Jumlah tip | Target utama analisis |

### 2. Taxi Zone Lookup Table
- **Sumber:** https://d37ci6vzurychx.cloudfront.net/misc/taxi+_zone_lookup.csv
- **Isi:** 265 zona taksi NYC dengan nama zona dan borough
- **Digunakan untuk:** Menampilkan nama zona di peta dan analisis per wilayah

### 3. Open-Meteo Historical Weather API (Data Eksternal - Bonus)
- **Sumber:** https://archive-api.open-meteo.com/v1/archive
- **Lokasi:** NYC (lat=40.7128, lon=-74.0060)
- **Periode:** 1 Januari – 31 Maret 2025
- **Kolom:** temperature_2m_max, rain_sum, snowfall_sum → dikategorikan menjadi: Clear, Light Rain, Heavy Rain, Snow
- **Digunakan untuk:** Analisis pengaruh cuaca terhadap tip, fitur ML

---

## 🏗️ Arsitektur Pipeline

```text
┌────────────────────┐     ┌────────────────────┐     ┌────────────────────┐
│ NYC TLC Website    │     │ Open-Meteo API     │     │ Zone Lookup CSV    │
│ (Taxi Dataset)     │     │ (Weather Data)     │     │ (Zona NYC)         │
└─────────┬──────────┘     └─────────┬──────────┘     └─────────┬──────────┘
          │                          │                          │
          └────────────────┬─────────┴─────────┬────────────────┘
                           ▼
┌──────────────────────────────────────────────────────────────────────┐
│                  PHASE 1 — DATA INGESTION                           │
│                  scripts/ingestion.py                               │
│                  Orchestrasi: Prefect                               │
└──────────────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────────────┐
│                           DATA RAW                                  │
│                                                                      │
│ data/raw/yellow_tripdata_2025-01.parquet                            │
│ data/raw/yellow_tripdata_2025-02.parquet                            │
│ data/raw/yellow_tripdata_2025-03.parquet                            │
│                                                                      │
│ data/processed/dim_weather.parquet                                  │
│ data/processed/dim_zones.csv                                        │
└──────────────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────────────┐
│             PHASE 2 — PREPROCESSING & CLEANING                      │
│             scripts/preprocessing.py                                │
│             Tools: DuckDB + Pandas                                  │
└──────────────────────────────────────────────────────────────────────┘
                           │
                           ▼
        Filter anomali + Join cuaca & zona + Feature Engineering
                           │
                           ▼
┌──────────────────────────────────────────────────────────────────────┐
│                  PHASE 3 — DATA STORAGE                             │
│                  data/processed/fact_trips.parquet                  │
│                  Format: Parquet (Data Lake)                        │
└──────────────────────────────────────────────────────────────────────┘
                           │
              ┌────────────┴────────────┐
              ▼                         ▼

┌───────────────────────────┐   ┌────────────────────────────┐
│     PHASE 4 — ANALISIS    │   │  PHASE 5 — MACHINE LEARNING│
│     DuckDB / Pandas       │   │  Random Forest             │
│                            │   │  scikit-learn             │
└───────────────────────────┘   └────────────────────────────┘
              │                         │
              └────────────┬────────────┘
                           ▼
┌──────────────────────────────────────────────────────────────────────┐
│                 PHASE 6 — VISUALISASI                               │
│                 dashboard/app.py                                    │
│                 Tools: Streamlit + Folium                           │
└──────────────────────────────────────────────────────────────────────┘
```

## 🔧 Penjelasan Tahapan Pipeline

### Phase 1 — Data Ingestion (`scripts/ingestion.py`)
- Download 3 file Parquet TLC (Jan-Mar 2025) dari URL resmi
- Download zone lookup CSV
- Fetch data cuaca harian dari Open-Meteo API
- Dikategorikan menjadi 4 kondisi: Clear, Light Rain, Heavy Rain, Snow
- **Otomasi:** Menggunakan Prefect `@flow` dan `@task` dengan retry otomatis (2x)
- **Efisiensi:** Cek file sudah ada sebelum download ulang

### Phase 2 — Preprocessing & Cleaning (`scripts/preprocessing.py`)
Menggunakan **DuckDB** (SQL) untuk efisiensi memori:

| Langkah | Query SQL | Alasan |
|---|---|---|
| Filter payment_type = 1 | WHERE payment_type = 1 | Hanya kartu kredit yang mencatat tip |
| Hapus fare <= 0 | AND fare_amount > 0 | Tarif tidak logis |
| Hapus distance <= 0 | AND trip_distance > 0 | Jarak tidak logis |
| Hapus tip negatif | AND tip_amount >= 0 | Tip tidak mungkin negatif |
| Hapus passenger <= 0 | AND passenger_count > 0 | Jumlah penumpang tidak logis |
| Hapus missing lokasi | AND PULocationID IS NOT NULL | Data lokasi wajib untuk peta |
| Join zona | LEFT JOIN dim_zones | Dapatkan nama zona & borough |
| Join cuaca | LEFT JOIN dim_weather | Dapatkan kondisi cuaca per tanggal |

**Feature Engineering (DuckDB SQL):**

| Kolom Baru | Cara Hitung | Kegunaan |
|---|---|---|
| hour_of_day | HOUR(pickup_datetime) | Analisis per jam |
| day_of_week | DAYNAME(pickup_datetime) | Analisis per hari |
| month | MONTH(pickup_datetime) | Analisis per bulan |
| duration_minutes | DATEDIFF('minute', pickup, dropoff) | Durasi perjalanan |
| tip_percentage | (tip_amount / fare_amount) * 100 | Persentase tip |
| high_tip_v2 | 1 jika tip_percentage > 25 | Target ML |

### Phase 3 — Data Storage
Format penyimpanan: **Parquet** (Data Lake approach)

| File | Ukuran | Isi |
|---|---|---|
| data/raw/yellow_tripdata_2025-*.parquet | ~185 MB | Data mentah TLC |
| data/processed/fact_trips.parquet | ~157 MB | Data bersih + fitur turunan + hasil prediksi ML |
| data/processed/dim_zones.csv | 11 KB | Lookup 265 zona taksi |
| data/processed/dim_weather.parquet | 4.9 KB | Data cuaca harian NYC |
| data/models/random_forest_tip_model.pkl | ~MB | Model ML terlatih |

**Skema Data (Star Schema):**
fact_trips ──── dim_zones (via PULocationID → LocationID)
──── dim_weather (via pickup_date → date)

### Phase 4 — Analisis
Query agregasi menggunakan Pandas terhadap `fact_trips.parquet`:
- Rata-rata tip per jam, per hari, per kondisi cuaca
- Rata-rata tip per zona dan borough
- Distribusi tip percentage

### Phase 5 — Machine Learning (`scripts/ml_training.py`)
- **Model:** Random Forest Classifier (scikit-learn)
- **Target:** high_tip_v2 (1 jika tip > 25%)
- **Fitur:** hour_of_day, day_of_week, trip_distance, passenger_count, PULocationID, weather_condition, duration_minutes
- **Training:** 80% train, 20% test, sample 500.000 baris
- **class_weight='balanced'** untuk menangani ketidakseimbangan kelas
- **Hasil:** Accuracy 72%, F1-score kelas 1: 0.79
- **Output:** Model disimpan ke `data/models/`, hasil prediksi disimpan ke `fact_trips.parquet`

**Feature Importance:**
| Fitur | Importance |
|---|---|
| duration_minutes | 44.78% |
| trip_distance | 39.09% |
| PULocationID | 8.36% |
| hour_of_day | 5.52% |
| day_of_week | 1.44% |
| passenger_count | 0.44% |
| weather_condition | 0.35% |

### Phase 6 — Visualisasi Dashboard (`dashboard/app.py`)
Dashboard Streamlit dengan 3 halaman:

**🗺️ Halaman Peta:**
- Choropleth map NYC per borough berdasarkan rata-rata tip
- Tooltip interaktif saat hover (avg tip, total trips, high tip rate)
- Filter: rentang jam, hari, kondisi cuaca
- Tabel semua 251 zona aktif dengan pagination & fitur pencarian

**📊 Halaman Analisis:**
- Grafik tip per jam (line chart)
- Grafik tip per hari (bar chart)
- Grafik tip per kondisi cuaca (bar chart)
- Distribusi tip percentage (histogram)
- Distribusi probabilitas prediksi ML
- Insight otomatis di bawah setiap grafik
- Filter: borough

**🤖 Halaman Prediksi:**
- Form input: jam, hari, zona (dropdown 265 nama zona), jarak, durasi, jumlah penumpang, cuaca
- Output: probabilitas tip tinggi dari model Random Forest
- Rekomendasi otomatis untuk pengemudi

---

## 🛠️ Tools yang Digunakan

| Kategori | Tool | Alasan |
|---|---|---|
| Pipeline Orchestration | Prefect | Direkomendasikan dosen, mudah untuk pemula |
| ETL/Processing | DuckDB | Direkomendasikan dosen, efisien untuk data besar |
| Storage | Parquet | Direkomendasikan dosen, format data lake modern |
| Machine Learning | scikit-learn (Random Forest) | Standar industri untuk klasifikasi |
| Dashboard | Streamlit | Direkomendasikan dosen, gratis, pure Python |
| Peta Interaktif | Folium | Direkomendasikan dosen, mendukung geospatial |
| Environment | GitHub Codespaces | Cloud-based, tidak perlu install lokal |

---

## 🚀 Cara Menjalankan

### Prasyarat
- Akun GitHub dengan akses Codespaces
- Atau Python 3.10+ terinstall lokal

### 1. Clone Repository
```bash
git clone https://github.com/[username]/tugas-akhir-rdv.git
cd tugas-akhir-rdv
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Jalankan Pipeline (Urut)
```bash
# Step 1: Download semua data
python scripts/ingestion.py

# Step 2: Preprocessing & Feature Engineering (DuckDB)
python scripts/preprocessing.py

# Step 3: Verifikasi feature engineering
python scripts/feature_engineering.py

# Step 4: Training model ML
python scripts/ml_training.py
```

### 4. Jalankan Dashboard
```bash
streamlit run dashboard/app.py
```

Buka browser di `http://localhost:8501`

---


## 📁 Struktur Folder

```text
tugas-akhir-rdv/
│
├── README.md
│   └── Dokumentasi proyek
│
├── requirements.txt
│   └── Library yang dibutuhkan
│
├── .gitignore
│   └── Abaikan file data mentah & model
│
├── data/
│   │
│   ├── raw/
│   │   └── Data mentah TLC (tidak di-push ke Git)
│   │
│   ├── processed/
│   │   └── Data bersih, zona, cuaca, dan GeoJSON
│   │
│   └── models/
│       └── Model Machine Learning (.pkl)
│
├── scripts/
│   │
│   ├── ingestion.py
│   │   └── Download data (Prefect pipeline)
│   │
│   ├── preprocessing.py
│   │   └── Cleaning & ETL (DuckDB)
│   │
│   ├── feature_engineering.py
│   │   └── Verifikasi & statistik fitur
│   │
│   ├── ml_training.py
│   │   └── Training Random Forest
│   │
│   └── utils.py
│       └── Fungsi shared seperti load_data()
│
├── dashboard/
│   │
│   ├── app.py
│   │   └── Main Streamlit app
│   │
│   └── pages/
│       │
│       ├── peta.py
│       │   └── Halaman peta interaktif
│       │
│       ├── analisis.py
│       │   └── Analisis temporal & cuaca
│       │
│       └── prediksi.py
│           └── Halaman prediksi Machine Learning
│
└── laporan/
    │
    ├── Laporan_Tugas_Akhir_RDV.pdf
    │   └── Laporan final proyek
    │
    └── slide_presentasi.pdf
        └── Slide presentasi
```


## 📊 Hasil & Insight Utama

⚠️ Isi bagian ini setelah melihat hasil dashboard

1. Zona terbaik: [Isi dari tabel zona di dashboard]
2. Jam terbaik: [Isi dari grafik jam di dashboard]
3. Hari terbaik: [Isi dari grafik hari di dashboard]
4. Pengaruh cuaca: [Isi dari grafik cuaca di dashboard]
5. Akurasi model ML: 72% dengan threshold tip >25%


## 📝 Catatan Teknis

- Data fact_trips.parquet tidak di-push ke GitHub karena ukurannya 157MB (melebihi batas 100MB GitHub). File ini di-generate ulang dengan menjalankan pipeline dari awal.
- Zona taksi Staten Island (12 zona) tidak memiliki data trip karena taksi kuning NYC jarang beroperasi di sana.
- Model ML menggunakan sample 500.000 baris dari 7.3 juta baris untuk efisiensi memori di GitHub Codespaces.