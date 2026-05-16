import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
from sklearn.preprocessing import LabelEncoder
import joblib
import os

if __name__ == "__main__":
    print("Loading data...")
    df = pd.read_parquet("data/processed/fact_trips.parquet")

    features = ['hour_of_day', 'day_of_week', 'trip_distance',
                'passenger_count', 'PULocationID', 'weather_condition', 'duration_minutes']
    target = 'high_tip'

    df = df[features + [target]].dropna()

    # Encode kolom kategorikal
    le_day = LabelEncoder()
    le_weather = LabelEncoder()
    df['day_of_week'] = le_day.fit_transform(df['day_of_week'])
    df['weather_condition'] = le_weather.fit_transform(df['weather_condition'])

    # Sample 500k
    print(f"Menggunakan sample 500.000 baris")
    df_sample = df.sample(500000, random_state=42)
    X = df_sample[features]
    y = df_sample[target]

    print("Split data train-test...")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    print("Training Random Forest (balanced)...")
    model = RandomForestClassifier(
        n_estimators=100,
        max_depth=10,
        random_state=42,
        n_jobs=-1,
        class_weight='balanced'
    )
    model.fit(X_train, y_train)

    print("Evaluasi model:")
    y_pred = model.predict(X_test)
    print(classification_report(y_test, y_pred))

    # Feature importance
    print("Feature Importance:")
    for feat, imp in sorted(zip(features, model.feature_importances_), key=lambda x: -x[1]):
        print(f"  {feat}: {imp:.4f}")

    # Simpan model dan encoder
    os.makedirs("data/models", exist_ok=True)
    joblib.dump(model, "data/models/random_forest_tip_model.pkl")
    joblib.dump(le_day, "data/models/le_day.pkl")
    joblib.dump(le_weather, "data/models/le_weather.pkl")

    print("=== ML TRAINING SELESAI ===")
    print("Model tersimpan di data/models/")
