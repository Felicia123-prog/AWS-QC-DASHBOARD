import streamlit as st
import os

st.title("AWS QC Dashboard")

# 📁 Detecteer stations (mappen in data/)
data_path = "data"
stations = [d for d in os.listdir(data_path) if os.path.isdir(os.path.join(data_path, d))]

if not stations:
    st.warning("Er zijn nog geen stations in de map 'data/'. Voeg eerst data toe.")
else:
    station = st.selectbox("Kies een station", stations)

    # 📁 Detecteer elementen (Excel-bestanden in station-map)
    station_path = os.path.join(data_path, station)
    elementen = [f for f in os.listdir(station_path) if f.endswith(".xlsx")]

    if not elementen:
        st.warning(f"Geen QC-bestanden gevonden voor station: {station}")
    else:
        element = st.selectbox("Kies een element", elementen)
        st.success(f"Je hebt gekozen: {station} – {element}")
