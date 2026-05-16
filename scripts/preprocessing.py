import duckdb
import pandas as pd
import os

def run_preprocessing():
    os.makedirs("data/processed", exist_ok=True)
    
    con = duckdb.connect()
    
    print("Loading raw data dengan DuckDB...")
    con.execute("""
        CREATE VIEW raw_trips AS
        SELECT * FROM read_parquet('data/raw/yellow_tripdata_2025-*.parquet')
    """)
    
    total = con.execute("SELECT COUNT(*) FROM raw_trips").fetchone()[0]
    print(f"Total baris awal: {total:,}")

    print("Membersihkan data...")
    con.execute("""
        CREATE VIEW clean_trips AS
        SELECT
            tpep_pickup_datetime,
            tpep_dropoff_datetime,
            passenger_count,
            trip_distance,
            PULocationID,
            DOLocationID,
            payment_type,
            fare_amount,
            tip_amount
        FROM raw_trips
        WHERE
            -- Hanya kartu kredit (tip tercatat)
            payment_type = 1
            -- Hapus anomali tarif dan jarak
            AND fare_amount > 0
            AND trip_distance > 0
            -- Tip tidak mungkin negatif
            AND tip_amount >= 0
            -- Jumlah penumpang harus logis
            AND passenger_count > 0
            -- Lokasi harus ada
            AND PULocationID IS NOT NULL
            AND DOLocationID IS NOT NULL
    """)

    after_clean = con.execute("SELECT COUNT(*) FROM clean_trips").fetchone()[0]
    print(f"Setelah cleaning: {after_clean:,}")

    print("Join dengan zona dan cuaca...")
    con.execute("""
        CREATE VIEW trips_with_zones AS
        SELECT
            t.*,
            z.Zone AS PU_Zone,
            z.Borough AS PU_Borough
        FROM clean_trips t
        LEFT JOIN read_csv('data/processed/dim_zones.csv') z
            ON t.PULocationID = z.LocationID
    """)

    con.execute("""
        CREATE VIEW trips_with_weather AS
        SELECT
            t.*,
            w.temp_max,
            w.rain_sum,
            w.snowfall_sum,
            w.weather_condition
        FROM trips_with_zones t
        LEFT JOIN read_parquet('data/processed/dim_weather.parquet') w
            ON CAST(t.tpep_pickup_datetime AS DATE) = w.date
    """)

    print("Feature engineering...")
    con.execute("""
        CREATE VIEW fact_trips_view AS
        SELECT
            *,
            -- Fitur waktu
            HOUR(tpep_pickup_datetime)                          AS hour_of_day,
            DAYNAME(tpep_pickup_datetime)                       AS day_of_week,
            MONTH(tpep_pickup_datetime)                         AS month,
            CAST(tpep_pickup_datetime AS DATE)                  AS pickup_date,
            -- Durasi perjalanan
            DATEDIFF('minute', tpep_pickup_datetime, tpep_dropoff_datetime) AS duration_minutes,
            -- Tip features
            ROUND((tip_amount / fare_amount) * 100, 2)         AS tip_percentage,
            CASE WHEN (tip_amount / fare_amount) * 100 > 20
                 THEN 1 ELSE 0 END                             AS high_tip
        FROM trips_with_weather
        WHERE
            DATEDIFF('minute', tpep_pickup_datetime, tpep_dropoff_datetime) > 0
            AND DATEDIFF('minute', tpep_pickup_datetime, tpep_dropoff_datetime) < 180
            AND (tip_amount / fare_amount) * 100 <= 100
    """)

    final_count = con.execute("SELECT COUNT(*) FROM fact_trips_view").fetchone()[0]
    high_tip_rate = con.execute("SELECT AVG(high_tip) FROM fact_trips_view").fetchone()[0]
    print(f"Data final: {final_count:,} baris")
    print(f"Proporsi high_tip: {high_tip_rate:.2%}")

    print("Menyimpan fact_trips.parquet...")
    con.execute("""
        COPY fact_trips_view TO 'data/processed/fact_trips.parquet'
        (FORMAT PARQUET)
    """)

    con.close()
    print("=== PREPROCESSING SELESAI ===")

if __name__ == "__main__":
    run_preprocessing()
