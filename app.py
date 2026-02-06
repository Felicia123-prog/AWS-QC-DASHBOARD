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
import pandas as pd
import plotly.express as px

# 📊 Als er een element gekozen is, laad het bestand
if 'element' in locals():
    file_path = os.path.join(station_path, element)
    df = pd.read_excel(file_path)

    st.subheader("Voorbeeld van de ingelezen data")
    st.write(df.head())

    # Controleer of er een kolom 'Timestamp' bestaat
    tijdkolommen = [col for col in df.columns if 'time' in col.lower() or 'datum' in col.lower()]
    
    if tijdkolommen:
        tijdkolom = tijdkolommen[0]
        df[tijdkolom] = pd.to_datetime(df[tijdkolom])

        # Zoek een kolom met temperatuur
        waardekolommen = [col for col in df.columns if 'temp' in col.lower()]
        
        if waardekolommen:
            waardekolom = waardekolommen[0]

            fig = px.line(df, x=tijdkolom, y=waardekolom, title="Eerste testgrafiek")
            st.plotly_chart(fig)
        else:
            st.warning("Geen temperatuurkolom gevonden in dit bestand.")
    else:
        st.warning("Geen tijdkolom gevonden in dit bestand.")
