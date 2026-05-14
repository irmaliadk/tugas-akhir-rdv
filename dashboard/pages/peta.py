import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import json

@st.cache_data
def load_data():
    df = pd.read_parquet("data/processed/fact_trips.parquet")
    if len(df) > 500000:
        df = df.sample(500000, random_state=42)
    return df

@st.cache_data
def load_geojson():
    with open("data/processed/nyc_boroughs.geojson", "r") as f:
        return json.load(f)

def show():
    st.header("🗺️ Peta Tip Taksi NYC per Borough & Zona")

    df = load_data()
    geojson = load_geojson()

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

    st.markdown(f"**Total perjalanan (sample):** {len(df_filtered):,}")

    # =====================
    # AGREGASI PER BOROUGH
    # =====================
    agg_borough = df_filtered.groupby("PU_Borough").agg(
        avg_tip=("tip_percentage", "mean"),
        total_trips=("tip_percentage", "count"),
        high_tip_rate=("high_tip", "mean")
    ).reset_index()
    agg_borough.columns = ["name", "avg_tip", "total_trips", "high_tip_rate"]

    # =====================
    # AGREGASI PER ZONA
    # =====================
    agg_zona = df_filtered.groupby(["PULocationID", "PU_Zone", "PU_Borough"]).agg(
        avg_tip=("tip_percentage", "mean"),
        total_trips=("tip_percentage", "count"),
        high_tip_rate=("high_tip", "mean")
    ).reset_index()

    # =====================
    # BUAT PETA CHOROPLETH
    # =====================
    m = folium.Map(location=[40.7128, -74.0060], zoom_start=10)

    folium.Choropleth(
        geo_data=geojson,
        name="Avg Tip per Borough",
        data=agg_borough,
        columns=["name", "avg_tip"],
        key_on="feature.properties.name",
        fill_color="YlOrRd",
        fill_opacity=0.7,
        line_opacity=0.5,
        legend_name="Rata-rata Tip (%)",
        nan_fill_color="lightgray"
    ).add_to(m)

    # Tooltip per borough
    for feature in geojson["features"]:
        name = feature["properties"]["name"]
        row = agg_borough[agg_borough["name"] == name]
        if len(row) > 0:
            feature["properties"]["avg_tip"] = f"{row['avg_tip'].values[0]:.1f}%"
            feature["properties"]["total_trips"] = f"{row['total_trips'].values[0]:,}"
            feature["properties"]["high_tip_rate"] = f"{row['high_tip_rate'].values[0]:.1%}"
        else:
            feature["properties"]["avg_tip"] = "N/A"
            feature["properties"]["total_trips"] = "0"
            feature["properties"]["high_tip_rate"] = "N/A"

    folium.GeoJson(
        geojson,
        style_function=lambda x: {"fillOpacity": 0, "weight": 0},
        tooltip=folium.GeoJsonTooltip(
            fields=["name", "avg_tip", "total_trips", "high_tip_rate"],
            aliases=["Borough:", "Avg Tip:", "Total Trips:", "High Tip Rate:"],
        )
    ).add_to(m)

    # Tambah marker per zona (top 50 zona berdasarkan total trips)
    top_zones = agg_zona.nlargest(50, "total_trips")
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
        "Astoria": (40.7721, -73.9302),
        "Harlem": (40.8116, -73.9465),
        "East Harlem North": (40.7957, -73.9389),
        "East Harlem South": (40.7905, -73.9389),
        "Yorkville East": (40.7736, -73.9447),
        "Yorkville West": (40.7736, -73.9527),
        "Lincoln Square East": (40.7731, -73.9845),
        "Lincoln Square West": (40.7731, -73.9895),
        "Clinton East": (40.7631, -73.9895),
        "Clinton West": (40.7631, -73.9945),
        "Garment District": (40.7506, -73.9971),
        "Flatiron": (40.7401, -73.9901),
        "Gramercy": (40.7368, -73.9845),
        "Murray Hill": (40.7484, -73.9767),
    }

    for _, row in top_zones.iterrows():
        coords = zone_coords.get(row["PU_Zone"])
        if coords is None:
            continue
        avg_tip = row["avg_tip"]
        if avg_tip > 25:
            color = "red"
        elif avg_tip > 20:
            color = "orange"
        elif avg_tip > 15:
            color = "blue"
        else:
            color = "green"
        radius = max(5, min(20, row["total_trips"] / 500))
        folium.CircleMarker(
            location=coords,
            radius=radius,
            color=color,
            fill=True,
            fill_opacity=0.8,
            tooltip=f"{row['PU_Zone']}<br>Avg Tip: {avg_tip:.1f}%<br>Total Trips: {row['total_trips']:,}<br>High Tip Rate: {row['high_tip_rate']:.1%}"
        ).add_to(m)

    folium.LayerControl().add_to(m)
    st_folium(m, width=900, height=500)

    # =====================
    # TABEL TOP ZONA
    # =====================
    st.subheader("Top 10 Zona dengan Tip Tertinggi")
    top10 = agg_zona.sort_values("avg_tip", ascending=False).head(10)
    top10["high_tip_pct"] = (top10["high_tip_rate"] * 100).round(1).astype(str) + "%"
    top10 = top10[["PU_Zone", "PU_Borough", "avg_tip", "total_trips", "high_tip_pct"]]
    top10.columns = ["Zona", "Borough", "Avg Tip (%)", "Total Trips", "High Tip Rate"]
    top10["Avg Tip (%)"] = top10["Avg Tip (%)"].round(1)
    st.dataframe(top10, use_container_width=True)
