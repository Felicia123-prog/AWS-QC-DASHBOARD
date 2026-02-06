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

    # 👉 Controleer of kolommen 'Dag' en 'Tijd' bestaan
    if 'Dag' in df.columns and 'Tijd' in df.columns:
        # Combineer Dag + Tijd tot één datetime kolom
        df['Timestamp'] = pd.to_datetime(df['Dag'].astype(str) + ' ' + df['Tijd'].astype(str))

      # 👉 Controleer of kolommen 'Dag' en 'Tijd' bestaan
if 'Dag' in df.columns and 'Tijd' in df.columns:
    # Combineer Dag + Tijd tot één datetime kolom
    df['Timestamp'] = pd.to_datetime(df['Dag'].astype(str) + ' ' + df['Tijd'].astype(str))

    # 👉 Controleer of Raw Value en Cleaned Value bestaan
    if 'Raw Value' in df.columns and 'Cleaned Value' in df.columns:

        fig = px.line(
            df,
            x='Timestamp',
            y=['Raw Value', 'Cleaned Value'],
            labels={'value': 'Temperatuur (°C)', 'Timestamp': 'Tijd'},
            title="Raw vs Cleaned – Temperatuur"
        )

        st.plotly_chart(fig)

    else:
        st.warning("Kolommen 'Raw Value' en/of 'Cleaned Value' ontbreken in dit bestand.")
else:
    st.warning("Kolommen 'Dag' en 'Tijd' zijn niet gevonden in dit bestand.")
