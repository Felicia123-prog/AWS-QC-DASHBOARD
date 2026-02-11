import streamlit as st
import os
import pandas as pd
import plotly.graph_objects as go
import numpy as np

st.title("AWS QC Dashboard – Windrichting (Raw Value)")

# 📁 Detecteer stations
data_path = "data"
stations = [d for d in os.listdir(data_path) if os.path.isdir(os.path.join(data_path, d))]

station = st.selectbox("Kies een station", stations)

# 📄 Automatisch windrichting-bestand kiezen
station_path = os.path.join(data_path, station)
wind_file = "Wind_Dir_Averagedeg_QC.xlsx"   # <-- JUISTE BESTANDSNAAM
file_path = os.path.join(station_path, wind_file)

df = pd.read_excel(file_path)

# Combineer Dag + Tijd
df['Timestamp'] = pd.to_datetime(df['Dag'].astype(str) + ' ' + df['Tijd'].astype(str))
df = df.sort_values('Timestamp')

# 📅 Dagselectie
alle_dagen = sorted(df['Timestamp'].dt.date.unique())
gekozen_dag = st.selectbox("Kies een dag", alle_dagen)

df_dag = df[df['Timestamp'].dt.date == gekozen_dag]

st.subheader(f"QC Rapport – {gekozen_dag}")

# -----------------------------
# 1. CUSTOM BLOCKS TIMELINE (precies zoals temperatuur)
# -----------------------------
st.subheader("Ontbrekende metingen voor de dag!")

# Raw Value numeriek maken
df["Raw Value"] = pd.to_numeric(df["Raw Value"], errors="coerce")

# Filter op gekozen dag
df_dag = df[df['Timestamp'].dt.date == gekozen_dag].copy()

# Verwachte timestamps
start = pd.to_datetime(str(gekozen_dag) + " 00:00:00")
expected_times = pd.date_range(start=start, periods=144, freq="10min")

df_expected = pd.DataFrame({"Timestamp": expected_times})

# Status = True ALS er een echte Raw Value is
df_expected = df_expected.merge(
    df_dag[["Timestamp", "Raw Value"]],
    on="Timestamp",
    how="left"
)

df_expected["Status"] = df_expected["Raw Value"].notna()

# Uur + blok berekenen
df_expected["Hour"] = df_expected["Timestamp"].dt.hour
df_expected["Block"] = df_expected["Timestamp"].dt.minute // 10

# Raster parameters
cell_size = 30
gap = 5
rows = 6
cols = 24

fig = go.Figure()

# Blokjes tekenen
for _, row in df_expected.iterrows():
    hour = row["Hour"]
    block = row["Block"]
    status = row["Status"]

    color = "green" if status else "red"

    x = hour * (cell_size + gap)
    y = (5 - block) * (cell_size + gap)

    fig.add_shape(
        type="rect",
        x0=x, x1=x + cell_size,
        y0=y, y1=y + cell_size,
        line=dict(width=0),
        fillcolor=color
    )

# As-instellingen
fig.update_xaxes(
    title_text="<b>Uur van de dag</b>",
    title_font=dict(size=16),
    tickfont=dict(size=14, color="black"),
    range=[0, cols * (cell_size + gap)],
    tickmode="array",
    tickvals=[h * (cell_size + gap) + cell_size/2 for h in range(cols)],
    ticktext=[f"<b>{h:02d}:00</b>" for h in range(cols)],
    showgrid=False,
    zeroline=False
)

fig.update_yaxes(
    title_text="<b>10-minuten blok</b>",
    title_font=dict(size=16),
    tickfont=dict(size=14, color="black"),
    range=[0, rows * (cell_size + gap)],
    tickmode="array",
    tickvals=[i * (cell_size + gap) + cell_size/2 for i in range(rows)],
    ticktext=[f"<b>{t}</b>" for t in ["00", "10", "20", "30", "40", "50"]],
    showgrid=False,
    zeroline=False
)

fig.update_layout(
    width=cols * (cell_size + gap) + 200,
    height=rows * (cell_size + gap) + 200,
    margin=dict(l=80, r=40, t=60, b=80),
    plot_bgcolor="white"
)

st.plotly_chart(fig, use_container_width=True)

# -----------------------------
# LEGENDA
# -----------------------------
st.markdown("**Legenda:** 🟩 Ontvangen meting   |   🟥 Ontbrekende meting")

# -----------------------------
# 2. QC-REGELS (precies zoals temperatuur)
# -----------------------------
st.subheader("QC Analyse – Windrichting")

df_dag["QC_Flag"] = np.where(
    df_dag["Raw Value"].between(0, 360, inclusive="both"),
    "OK",
    "FOUT"
)

df_dag["Cleaned Value"] = np.where(
    df_dag["QC_Flag"] == "OK",
    df_dag["Raw Value"],
    np.nan
)

st.dataframe(df_dag)
