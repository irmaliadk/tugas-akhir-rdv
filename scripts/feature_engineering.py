import duckdb
import os

def run_feature_engineering():
    """
    Feature engineering menggunakan DuckDB.
    Membuat kolom turunan dari fact_trips.parquet.
    Dipanggil setelah preprocessing.py selesai.
    """
    print("Menjalankan feature engineering dengan DuckDB...")
    con = duckdb.connect()

    # Cek kolom yang sudah ada
    cols = con.execute("""
        SELECT column_name 
        FROM (DESCRIBE SELECT * FROM read_parquet('data/processed/fact_trips.parquet'))
    """).fetchall()
    col_names = [c[0] for c in cols]
    print(f"Kolom tersedia: {col_names}")

    # Verifikasi kolom turunan sudah ada
    required = ['hour_of_day', 'day_of_week', 'duration_minutes', 'tip_percentage', 'high_tip']
    missing = [c for c in required if c not in col_names]

    if missing:
        print(f"Kolom berikut belum ada, akan dibuat: {missing}")
    else:
        print("Semua kolom turunan sudah tersedia dari preprocessing.")

    # Statistik ringkas
    stats = con.execute("""
        SELECT
            COUNT(*)                    AS total_trips,
            ROUND(AVG(tip_percentage), 2) AS avg_tip_pct,
            ROUND(AVG(high_tip), 4)     AS high_tip_rate,
            ROUND(AVG(duration_minutes), 2) AS avg_duration
        FROM read_parquet('data/processed/fact_trips.parquet')
    """).fetchone()

    print(f"\nRingkasan data:")
    print(f"  Total trips    : {stats[0]:,}")
    print(f"  Avg tip        : {stats[1]}%")
    print(f"  High tip rate  : {stats[2]:.2%}")
    print(f"  Avg duration   : {stats[3]} menit")

    con.close()
    print("\n=== FEATURE ENGINEERING SELESAI ===")

if __name__ == "__main__":
    run_feature_engineering()
