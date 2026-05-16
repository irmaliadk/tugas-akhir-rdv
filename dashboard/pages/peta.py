import streamlit as st
from utils import load_data
import pandas as pd
import folium
from streamlit_folium import st_folium
import json


@st.cache_data
def load_data_full():
    """Load semua data tanpa sampling, hanya kolom yang dibutuhkan untuk tabel zona"""
    df = pd.read_parquet(
        "data/processed/fact_trips.parquet",
        columns=["PULocationID", "PU_Zone", "PU_Borough", "tip_percentage", "high_tip_v2"]
    )
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
        high_tip_rate=("high_tip_v2", "mean")
    ).reset_index()
    agg_borough.columns = ["name", "avg_tip", "total_trips", "high_tip_rate"]

    # =====================
    # AGREGASI PER ZONA (pakai data penuh)
    # =====================
    df_full = load_data_full()
    agg_zona = df_full.groupby(["PULocationID", "PU_Zone", "PU_Borough"]).agg(
        avg_tip=("tip_percentage", "mean"),
        total_trips=("tip_percentage", "count"),
        high_tip_rate=("high_tip_v2", "mean")
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

    folium.LayerControl().add_to(m)
    st_folium(m, width=900, height=500)

    # =====================
    # TABEL SEMUA ZONA
    # =====================
    st.subheader("📋 Semua Zona Berdasarkan Rata-rata Tip")

    tabel = agg_zona.copy()
    tabel["High Tip Rate"] = (tabel["high_tip_rate"] * 100).round(1).astype(str) + "%"
    tabel["avg_tip"] = tabel["avg_tip"].round(1)
    tabel = tabel[["PU_Zone", "PU_Borough", "avg_tip", "total_trips", "High Tip Rate"]]
    tabel.columns = ["Zona", "Borough", "Avg Tip (%)", "Total Trips", "High Tip Rate"]

    # Search
    search = st.text_input("🔍 Cari zona...", "")
    if search:
        tabel = tabel[tabel["Zona"].str.contains(search, case=False, na=False)]

    # Sort
    col_sort, col_order = st.columns([2, 1])
    with col_sort:
        sort_col = st.selectbox("Urutkan berdasarkan", ["Avg Tip (%)", "Total Trips", "High Tip Rate", "Zona", "Borough"])
    with col_order:
        sort_asc = st.radio("Urutan", ["Descending ↓", "Ascending ↑"], horizontal=True)

    # Sort pada seluruh data sebelum pagination
    # Reset ke halaman 1 setiap kali sort berubah
    sort_key = f"{sort_col}_{sort_asc}"
    if st.session_state.get("last_sort") != sort_key:
        st.session_state["page_zona"] = 1
        st.session_state["last_sort"] = sort_key

    if sort_col == "High Tip Rate":
        tabel["_sort_key"] = tabel["High Tip Rate"].str.replace("%","").astype(float)
        tabel = tabel.sort_values("_sort_key", ascending=(sort_asc == "Ascending ↑")).drop(columns=["_sort_key"])
    else:
        tabel = tabel.sort_values(sort_col, ascending=(sort_asc == "Ascending ↑"))

    # Reset index SETELAH sort agar slice pagination konsisten
    tabel = tabel.reset_index(drop=True)
    tabel.index += 1

    # Pagination
    page_size = 20
    total_pages = max(1, (len(tabel) - 1) // page_size + 1)

    st.caption(f"Menampilkan {len(tabel)} zona total")
    st.dataframe(tabel.iloc[((st.session_state.get('page_zona', 1))-1)*page_size : st.session_state.get('page_zona', 1)*page_size], use_container_width=True)

    # Pagination di bawah tabel
    col_prev, col_num, col_next = st.columns([1, 2, 1])
    with col_prev:
        if st.button("◀ Prev", use_container_width=True):
            st.session_state['page_zona'] = max(1, st.session_state.get('page_zona', 1) - 1)
            st.rerun()
    with col_num:
        st.markdown(f"<p style='text-align:center; padding-top:8px'>Halaman {st.session_state.get('page_zona', 1)} dari {total_pages}</p>", unsafe_allow_html=True)
    with col_next:
        if st.button("Next ▶", use_container_width=True):
            st.session_state['page_zona'] = min(total_pages, st.session_state.get('page_zona', 1) + 1)
            st.rerun()
