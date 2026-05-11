import pandas as pd

def process_one_month(filepath, zones, weather):
    df = pd.read_parquet(filepath)
    df = df[df["payment_type"] == 1]
    df = df[df["fare_amount"] > 0]
    df = df[df["trip_distance"] > 0]
    df = df[df["tip_amount"] >= 0]
    df = df[df["passenger_count"] > 0]
    df = df.dropna(subset=["PULocationID", "DOLocationID"])
    df = df.merge(zones, left_on="PULocationID", right_on="LocationID", how="left")
    df = df.rename(columns={"Zone": "PU_Zone", "Borough": "PU_Borough"})
    df = df.drop(columns=["LocationID"])
    df["tpep_pickup_datetime"] = pd.to_datetime(df["tpep_pickup_datetime"])
    df["tpep_dropoff_datetime"] = pd.to_datetime(df["tpep_dropoff_datetime"])
    df["pickup_date"] = df["tpep_pickup_datetime"].dt.date
    weather["date"] = pd.to_datetime(weather["date"]).dt.date
    df = df.merge(weather, left_on="pickup_date", right_on="date", how="left")
    df = df.drop(columns=["date"])
    df["hour_of_day"] = df["tpep_pickup_datetime"].dt.hour
    df["day_of_week"] = df["tpep_pickup_datetime"].dt.day_name()
    df["month"] = df["tpep_pickup_datetime"].dt.month
    df["duration_minutes"] = (df["tpep_dropoff_datetime"] - df["tpep_pickup_datetime"]).dt.total_seconds() / 60
    df = df[(df["duration_minutes"] > 0) & (df["duration_minutes"] < 180)]
    df["tip_percentage"] = (df["tip_amount"] / df["fare_amount"]) * 100
    df["high_tip"] = (df["tip_percentage"] > 20).astype(int)
    return df

zones = pd.read_csv("data/processed/dim_zones.csv")[["LocationID", "Zone", "Borough"]]
weather = pd.read_parquet("data/processed/dim_weather.parquet")

months = ["01", "02", "03"]
results = []
for m in months:
    print(f"Proses bulan {m}...")
    df = process_one_month(f"data/raw/yellow_tripdata_2025-{m}.parquet", zones, weather.copy())
    results.append(df)
    print(f"Bulan {m} selesai: {len(df)} baris")

print("Menggabungkan semua bulan...")
final = pd.concat(results, ignore_index=True)
print(f"Total final: {len(final)} baris")
final.to_parquet("data/processed/fact_trips.parquet", index=False)
print("=== SELESAI ===")
