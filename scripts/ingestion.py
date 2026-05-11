import pandas as pd
import requests
import os
from prefect import flow, task

# =====================
# TASK 1: Download TLC
# =====================
@task
def download_tlc_data():
    columns_needed = [
        'tpep_pickup_datetime', 'tpep_dropoff_datetime',
        'passenger_count', 'trip_distance',
        'PULocationID', 'DOLocationID',
        'payment_type', 'fare_amount',
        'tip_amount'
    ]
    months = ['01', '02', '03']
    for m in months:
        url = f"https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2025-{m}.parquet"
        print(f"Downloading TLC data bulan {m}...")
        df = pd.read_parquet(url, columns=columns_needed)
        df.to_parquet(f"data/raw/yellow_tripdata_2025-{m}.parquet", index=False)
        print(f"Selesai bulan {m}: {len(df)} baris")

# ========================
# TASK 2: Download Zona
# ========================
@task
def download_zone_lookup():
    url = "https://d37ci6vzurychx.cloudfront.net/misc/taxi+_zone_lookup.csv"
    print("Downloading zone lookup...")
    df = pd.read_csv(url)
    df.to_csv("data/processed/dim_zones.csv", index=False)
    print(f"Zone lookup selesai: {len(df)} zona")

# ========================
# TASK 3: Fetch Weather
# ========================
@task
def fetch_weather_data():
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
# FLOW UTAMA
# ========================
@flow(name="pipeline-ingestion")
def ingestion_flow():
    download_tlc_data()
    download_zone_lookup()
    fetch_weather_data()
    print("=== INGESTION SELESAI ===")

if __name__ == "__main__":
    ingestion_flow()
