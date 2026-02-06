import streamlit as st
import os
import pandas as pd
import plotly.express as px

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

        # 📊 Laad het bestand
        file_path = os.path.join(station_path, element)
        df = pd.read_excel(file_path)

        st.subheader("Voorbeeld van de ingelezen data")
        st.write(df.head())

        # 👉 Controleer of kolommen 'Dag' en 'Tijd' bestaan
        if 'Dag' in df.columns and 'Tijd' in df.columns:

            # Combineer Dag + Tijd tot één datetime kolom
            df['Timestamp'] = pd.to_datetime(df['Dag'].astype(str) + ' ' + df['Tijd'].astype(str))

            # 👉 RAW VS CLEANED GRAFIEK
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

            # 📊 --- DAGELIJKSE SAMENVATTING ---
            st.subheader("Dagelijkse samenvatting")

            # Maak een dagkolom
            df['Date'] = df['Timestamp'].dt.date

            # Bereken daily stats
            daily_stats = df.groupby('Date').agg({
                'Raw Value': ['mean', 'min', 'max'],
                'QC Flag': lambda x: (x != "None").sum()  # aantal QC-fouten
            })

            # Kolomnamen opschonen
            daily_stats.columns = ['Mean', 'Min', 'Max', 'QC_Fouten']
            daily_stats = daily_stats.reset_index()

            st.write("Dagelijkse statistieken", daily_stats)

            # Plot dagelijkse mean + min/max band
            fig_daily = px.line(
                daily_stats,
                x='Date',
                y='Mean',
                title="Dagelijkse temperatuur (gemiddelde, min-max band)"
            )

            # Voeg min-max band toe
            fig_daily.add_scatter(
                x=daily_stats['Date'],
                y=daily_stats['Min'],
                mode='lines',
                line=dict(width=0),
                showlegend=False
            )
            fig_daily.add_scatter(
                x=daily_stats['Date'],
                y=daily_stats['Max'],
                mode='lines',
                fill='tonexty',
                line=dict(width=0),
                name='Min-Max band'
            )

            st.plotly_chart(fig_daily)

            # QC-fouten grafiek
            fig_qc = px.bar(
                daily_stats,
                x='Date',
                y='QC_Fouten',
                title="Aantal QC-fouten per dag"
            )
            st.plotly_chart(fig_qc)

        else:
            st.warning("Kolommen 'Dag' en 'Tijd' zijn niet gevonden in dit bestand.")
            # 📊 --- QC HEATMAP ---
st.subheader("QC Heatmap (dag vs uur)")

# Maak een uurkolom
df['Hour'] = df['Timestamp'].dt.hour

# Zet QC Flag om naar numerieke codes
qc_map = {
    "None": 0,
    "OK": 0,
    "Missing": 1,
    "Suspect": 2,
    "Fail": 3
}

df['QC_Code'] = df['QC Flag'].map(qc_map).fillna(0)

# Maak een pivot table: dagen vs uren
heatmap_data = df.pivot_table(
    index=df['Timestamp'].dt.date,
    columns='Hour',
    values='QC_Code',
    aggfunc='max'
)

# Plot heatmap
fig_heatmap = px.imshow(
    heatmap_data,
    labels=dict(x="Uur van de dag", y="Datum", color="QC Code"),
    title="QC Heatmap (0 = OK, 1 = Missing, 2 = Suspect, 3 = Fail)",
    aspect="auto",
    color_continuous_scale=[
        (0.0, "green"),
        (0.33, "yellow"),
        (0.66, "orange"),
        (1.0, "red")
    ]
)

st.plotly_chart(fig_heatmap)
