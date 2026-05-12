import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

@st.cache_data
def load_data():
    df = pd.read_parquet("data/processed/fact_trips.parquet")
    if len(df) > 500000:
        df = df.sample(500000, random_state=42)
    return df

def show():
    st.header("🗺️ Peta Zona Tip Taksi NYC")

    df = load_data()

    # =====================
    # FILTER SIDEBAR
    # =====================
    st.sidebar.header("Filter Data")

    jam = st.sidebar.slider("Rentang Jam", 0, 23, (0, 23))
    hari = st.sidebar.multiselect(
        "Hari",
        options=["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"],
        default=["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
    )
    cuaca = st.sidebar.multiselect(
        "Kondisi Cuaca",
        options=df["weather_condition"].dropna().unique().tolist(),
        default=df["weather_condition"].dropna().unique().tolist()
    )

    # Apply filter
    df_filtered = df[
        (df["hour_of_day"] >= jam[0]) &
        (df["hour_of_day"] <= jam[1]) &
        (df["day_of_week"].isin(hari)) &
        (df["weather_condition"].isin(cuaca))
    ]

    st.markdown(f"**Total perjalanan:** {len(df_filtered):,}")

    # =====================
    # AGREGASI PER ZONA
    # =====================
    agg = df_filtered.groupby(["PULocationID", "PU_Zone", "PU_Borough"]).agg(
        avg_tip=("tip_percentage", "mean"),
        total_trips=("tip_percentage", "count"),
        high_tip_rate=("high_tip", "mean")
    ).reset_index()

    # Load koordinat zona (centroid manual untuk top zona)
    zone_coords = {
        "JFK Airport": (40.6413, -73.7781),
        "LaGuardia Airport": (40.7769, -73.8740),
        "Times Sq/Theatre District": (40.7580, -73.9855),
        "Midtown Center": (40.7549, -73.9840),
        "Upper East Side North": (40.7736, -73.9566),
        "Upper East Side South": (40.7648, -73.9627),
        "Upper West Side North": (40.7870, -73.9754),
        "Upper West Side South": (40.7784, -73.9817),
        "Midtown East": (40.7549, -73.9706),
        "Penn Station/Madison Sq West": (40.7501, -73.9967),
        "Chelsea": (40.7465, -74.0014),
        "Greenwich Village North": (40.7337, -74.0027),
        "Greenwich Village South": (40.7282, -74.0027),
        "SoHo": (40.7233, -74.0020),
        "Financial District North": (40.7092, -74.0131),
        "Financial District South": (40.7033, -74.0170),
        "Brooklyn": (40.6782, -73.9442),
        "Astoria": (40.7721, -73.9302),
        "Harlem": (40.8116, -73.9465),
        "East Harlem North": (40.7957, -73.9389),
    }

    # =====================
    # BUAT PETA FOLIUM
    # =====================
    m = folium.Map(location=[40.7128, -74.0060], zoom_start=11)

    for _, row in agg.iterrows():
        zone_name = row["PU_Zone"]
        coords = zone_coords.get(zone_name)
        if coords is None:
            continue

        avg_tip = row["avg_tip"]
        # Warna berdasarkan avg tip
        if avg_tip > 25:
            color = "red"
        elif avg_tip > 20:
            color = "orange"
        elif avg_tip > 15:
            color = "blue"
        else:
            color = "green"

        folium.CircleMarker(
            location=coords,
            radius=8,
            color=color,
            fill=True,
            fill_opacity=0.7,
            tooltip=f"{zone_name}<br>Avg Tip: {avg_tip:.1f}%<br>Total Trips: {row['total_trips']:,}<br>High Tip Rate: {row['high_tip_rate']:.1%}"
        ).add_to(m)

    # Legend
    legend_html = """
        <div style="position: fixed; bottom: 30px; left: 30px; z-index: 1000;
                    background-color: white; padding: 10px; border-radius: 8px;
                    border: 2px solid grey; font-size: 13px; color: black;">
            <b style="color: black;">Rata-rata Tip</b><br>
            🔴 > 25%<br>
            🟠 20-25%<br>
            🔵 15-20%<br>
            🟢 < 15%
        </div>
        """
    m.get_root().html.add_child(folium.Element(legend_html))

    st_folium(m, width=900, height=500)

    # =====================
    # TABEL TOP ZONA
    # =====================
    st.subheader("Top 10 Zona dengan Tip Tertinggi")
    top_zones = agg.sort_values("avg_tip", ascending=False).head(10)
    top_zones = top_zones[["PU_Zone", "PU_Borough", "avg_tip", "total_trips", "high_tip_rate"]]
    top_zones.columns = ["Zona", "Borough", "Avg Tip (%)", "Total Trips", "High Tip Rate"]
    top_zones["Avg Tip (%)"] = top_zones["Avg Tip (%)"].round(1)
    top_zones["High Tip Rate"] = (top_zones["High Tip Rate"] * 100).round(1).astype(str) + "%"
    st.dataframe(top_zones, use_container_width=True)
