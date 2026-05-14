import pandas as pd

def add_time_features(df):
    """Tambah fitur waktu dari kolom datetime"""
    df['tpep_pickup_datetime'] = pd.to_datetime(df['tpep_pickup_datetime'])
    df['tpep_dropoff_datetime'] = pd.to_datetime(df['tpep_dropoff_datetime'])
    df['hour_of_day'] = df['tpep_pickup_datetime'].dt.hour
    df['day_of_week'] = df['tpep_pickup_datetime'].dt.day_name()
    df['month'] = df['tpep_pickup_datetime'].dt.month
    return df

def add_trip_features(df):
    """Tambah fitur durasi dan tip"""
    df['duration_minutes'] = (
        df['tpep_dropoff_datetime'] - df['tpep_pickup_datetime']
    ).dt.total_seconds() / 60
    df = df[(df['duration_minutes'] > 0) & (df['duration_minutes'] < 180)]
    df['tip_percentage'] = (df['tip_amount'] / df['fare_amount']) * 100
    df['high_tip'] = (df['tip_percentage'] > 20).astype(int)
    return df

def run_feature_engineering(df):
    """Jalankan semua feature engineering"""
    print("Menjalankan feature engineering...")
    df = add_time_features(df)
    df = add_trip_features(df)
    print(f"Data final: {len(df)} baris")
    print(f"Proporsi high_tip: {df['high_tip'].mean():.2%}")
    return df

if __name__ == "__main__":
    print("Loading data...")
    df = pd.read_parquet("data/processed/fact_trips.parquet")
    df = run_feature_engineering(df)
    df.to_parquet("data/processed/fact_trips.parquet", index=False)
    print("=== FEATURE ENGINEERING SELESAI ===")
