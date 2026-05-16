import pandas as pd
import requests
import os
from prefect import flow, task
from prefect.schedules import Cron

# =====================
# TASK 1: Download TLC
# =====================
@task(name="download-tlc-data", retries=2, retry_delay_seconds=30)
def download_tlc_data():
    """
    Download data NYC TLC Yellow Taxi Trip Records
    Periode: Januari - Maret 2025
    Kolom dipilih secara spesifik untuk efisiensi memori
    """
    os.makedirs("data/raw", exist_ok=True)
    columns_needed = [
        'tpep_pickup_datetime',  # Waktu penjemputan
        'tpep_dropoff_datetime', # Waktu menurunkan penumpang
        'passenger_count',       # Jumlah penumpang
        'trip_distance',         # Jarak perjalanan (mil)
        'PULocationID',          # ID zona penjemputan
        'DOLocationID',          # ID zona tujuan
        'payment_type',          # Tipe pembayaran (1=kartu kredit)
        'fare_amount',           # Tarif dasar
        'tip_amount'             # Jumlah tip
    ]
    months = ['01', '02', '03']
    for m in months:
        filepath = f"data/raw/yellow_tripdata_2025-{m}.parquet"
        if os.path.exists(filepath):
            print(f"Bulan {m} sudah ada, skip download.")
            continue
        url = f"https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2025-{m}.parquet"
        print(f"Downloading TLC data bulan {m}...")
        df = pd.read_parquet(url, columns=columns_needed)
        df.to_parquet(filepath, index=False)
        print(f"Selesai bulan {m}: {len(df):,} baris")

# ========================
# TASK 2: Download Zona
# ========================
@task(name="download-zone-lookup", retries=2, retry_delay_seconds=30)
def download_zone_lookup():
    """Download taxi zone lookup table dari NYC TLC"""
    os.makedirs("data/processed", exist_ok=True)
    if os.path.exists("data/processed/dim_zones.csv"):
        print("Zone lookup sudah ada, skip download.")
        return
    url = "https://d37ci6vzurychx.cloudfront.net/misc/taxi+_zone_lookup.csv"
    print("Downloading zone lookup...")
    df = pd.read_csv(url)
    df.to_csv("data/processed/dim_zones.csv", index=False)
    print(f"Zone lookup selesai: {len(df)} zona")

# ========================
# TASK 3: Fetch Weather
# ========================
@task(name="fetch-weather-data", retries=2, retry_delay_seconds=30)
def fetch_weather_data():
    """
    Fetch historical weather data dari Open-Meteo API
    Lokasi: NYC (lat=40.7128, lon=-74.0060)
    Periode: Januari - Maret 2025
    """
    os.makedirs("data/processed", exist_ok=True)
    if os.path.exists("data/processed/dim_weather.parquet"):
        print("Weather data sudah ada, skip fetch.")
        return
    print("Fetching weather data dari Open-Meteo...")
    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": 40.7128,
        "longitude": -74.0060,
        "start_date": "2025-01-01",
        "end_date": "2025-03-31",
        "daily": "temperature_2m_max,rain_sum,snowfall_sum",
        "timezone": "America/New_York"
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    data = response.json()
    df = pd.DataFrame({
        "date": data["daily"]["time"],
        "temp_max": data["daily"]["temperature_2m_max"],
        "rain_sum": data["daily"]["rain_sum"],
        "snowfall_sum": data["daily"]["snowfall_sum"]
    })
    df["date"] = pd.to_datetime(df["date"])
    def categorize_weather(row):
        if row["snowfall_sum"] > 0:
            return "Snow"
        elif row["rain_sum"] > 5:
            return "Heavy Rain"
        elif row["rain_sum"] > 0:
            return "Light Rain"
        else:
            return "Clear"
    df["weather_condition"] = df.apply(categorize_weather, axis=1)
    df.to_parquet("data/processed/dim_weather.parquet", index=False)
    print(f"Weather data selesai: {len(df)} hari")

# ========================
# FLOW UTAMA + SCHEDULING
# ========================
@flow(
    name="pipeline-ingestion",
    description="Pipeline ingestion data NYC TLC + Weather, dijadwalkan setiap hari jam 00:00"
)
def ingestion_flow():
    download_tlc_data()
    download_zone_lookup()
    fetch_weather_data()
    print("=== INGESTION SELESAI ===")

if __name__ == "__main__":
    # Jalankan sekali langsung
    ingestion_flow()
