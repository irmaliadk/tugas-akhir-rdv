import streamlit as st

st.set_page_config(
    page_title="Analisis Tip Taksi NYC",
    page_icon="🚕",
    layout="wide"
)

st.title("🚕 Analisis Tip Taksi NYC 2025")
st.markdown("**Prediksi Tip Tinggi & Analisis Spasial-Temporal Berbasis Data Cuaca**")
st.markdown(
    """
    <style>
        [data-testid="stSidebarNav"] {
            display: none;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

st.sidebar.title("Navigasi")
page = st.sidebar.radio("Pilih Halaman", ["🗺️ Peta", "📊 Analisis", "🤖 Prediksi"])

if page == "🗺️ Peta":
    from pages.peta import show
    show()
elif page == "📊 Analisis":
    from pages.analisis import show
    show()
elif page == "🤖 Prediksi":
    from pages.prediksi import show
    show()
