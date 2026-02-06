import streamlit as st
import os
import pandas as pd
import plotly.graph_objects as go

st.title("AWS QC Dashboard – Temperatuur (Raw Value)")

# 📁 Detecteer stations
data_path = "data"
stations = [d for d in os.listdir(data_path) if os.path.isdir(os.path.join(data_path, d))]

station = st.selectbox("Kies een station", stations)

# 📁 Detecteer elementen
station_path = os.path.join(data_path, station)
elementen = [f for f in os.listdir(station_path) if f.endswith(".xlsx")]

element = st.selectbox("Kies een element", elementen)

# 📄 Laad bestand
file_path = os.path.join(station_path, element)
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
# LAYOUT: GRAFIEK LINKS, TEKST RECHTS
# -----------------------------
col1, col2 = st.columns([3, 1])   # grafiek krijgt meer ruimte

with col1:
    st.subheader("Ontbrekende metingen voor de dag!")

    # Verwachte timestamps
    start = pd.to_datetime(str(gekozen_dag) + " 00:00:00")
    expected_times = pd.date_range(start=start, periods=144, freq="10min")

    df_expected = pd.DataFrame({"Timestamp": expected_times})
    df_expected["Status"] = df_expected["Timestamp"].isin(df_dag["Timestamp"])
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
        title_text="Uur van de dag",
        range=[0, cols * (cell_size + gap)],
        tickmode="array",
        tickvals=[h * (cell_size + gap) + cell_size/2 for h in range(cols)],
        ticktext=[f"{h:02d}:00" for h in range(cols)],
        showgrid=False,
        zeroline=False
    )

    fig.update_yaxes(
        title_text="10-minuten blok",
        range=[0, rows * (cell_size + gap)],
        tickmode="array",
        tickvals=[i * (cell_size + gap) + cell_size/2 for i in range(rows)],
        ticktext=["00", "10", "20", "30", "40", "50"],
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

with col2:
    st.subheader("Samenvatting")

    # Berekeningen
    totaal_blokken = 144
    aanwezig = df_expected["Status"].sum()
    ontbrekend = totaal_blokken - aanwezig
    percentage = round((aanwezig / totaal_blokken) * 100, 1)

    # Kwaliteitslabel
    if percentage >= 75:
        kwaliteit = "Voldoende — dag voldoet aan de minimale eis."
    else:
        kwaliteit = "Onvoldoende — minder dan 75% datacompleetheid."

    # Tekst volgens jouw nieuwe formulering
    st.write("De temperatuur wordt elke 10 minuten gemeten en geregistreerd.")
    st.write("In totaal moeten er **144 metingen** zijn per dag.")
    st.write(f"**Ontbrekende metingen:** {ontbrekend} van de 144.")
    st.write(f"**Datacompleetheid:** {percentage}%.")
    st.write(f"**Kwaliteit:** {kwaliteit}")
