import streamlit as st
import os
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.title("AWS QC Dashboard – Temperatuur (Raw Value)")

# 📁 Detecteer stations
data_path = "data"
stations = [d for d in os.listdir(data_path) if os.path.isdir(os.path.join(data_path, d))]

if not stations:
    st.warning("Geen stations gevonden in de map 'data/'.")
    st.stop()

station = st.selectbox("Kies een station", stations)

# 📁 Detecteer elementen
station_path = os.path.join(data_path, station)
elementen = [f for f in os.listdir(station_path) if f.endswith(".xlsx")]

if not elementen:
    st.warning(f"Geen bestanden gevonden voor station: {station}")
    st.stop()

element = st.selectbox("Kies een element", elementen)

# 📄 Laad bestand
file_path = os.path.join(station_path, element)
df = pd.read_excel(file_path)

# Controleer kolommen
if not {'Dag', 'Tijd', 'Raw Value'}.issubset(df.columns):
    st.error("Bestand mist één van de vereiste kolommen: Dag, Tijd, Raw Value")
    st.stop()

# Combineer Dag + Tijd
df['Timestamp'] = pd.to_datetime(df['Dag'].astype(str) + ' ' + df['Tijd'].astype(str))
df = df.sort_values('Timestamp')

# 📅 Dagselectie
alle_dagen = sorted(df['Timestamp'].dt.date.unique())
gekozen_dag = st.selectbox("Kies een dag", alle_dagen)

df_dag = df[df['Timestamp'].dt.date == gekozen_dag]

st.subheader(f"QC Rapport – {gekozen_dag}")

# -----------------------------
# 1. MISSING BLOCKS TIMELINE (DUIDELIJKE BLOKJES)
# -----------------------------
st.subheader("Ontbrekende metingen (10-minuten blokjes)")

# Maak alle verwachte tijdstippen voor de gekozen dag
start = pd.to_datetime(str(gekozen_dag) + " 00:00:00")
expected_times = pd.date_range(start=start, periods=144, freq="10min")

# Dataframe met expected timestamps
df_expected = pd.DataFrame({"Timestamp": expected_times})

# Markeer of de meting bestaat
df_expected["Status"] = df_expected["Timestamp"].isin(df_dag["Timestamp"])

# Zet True/False om naar 1/0
df_expected["StatusCode"] = df_expected["Status"].apply(lambda x: 1 if x else 0)

# Uur en 10-minuten index
df_expected["Hour"] = df_expected["Timestamp"].dt.hour
df_expected["Block"] = df_expected["Timestamp"].dt.minute // 10  # 0 t/m 5

# Pivot: 24 rijen (uren) × 6 kolommen (10-min blokjes)
matrix = df_expected.pivot_table(
    index="Hour",
    columns="Block",
    values="StatusCode",
    aggfunc="max"
)

# Plot heatmap met alleen rood/groen
fig_blocks = px.imshow(
    matrix,
    color_continuous_scale=["red", "green"],
    aspect="auto",
    labels=dict(x="10-minuten blok", y="Uur", color="Status"),
    title="Missing Blocks Timeline (🟥 ontbreekt, 🟩 aanwezig)"
)

# Geen 0–1 schaal tonen
fig_blocks.update_coloraxes(showscale=False)

# Duidelijke ticks
fig_blocks.update_xaxes(
    tickmode="array",
    tickvals=[0,1,2,3,4,5],
    ticktext=["00","10","20","30","40","50"]
)

fig_blocks.update_yaxes(
    tickmode="array",
    tickvals=list(range(24)),
    ticktext=[f"{h:02d}:00" for h in range(24)]
)

st.plotly_chart(fig_blocks, use_container_width=True)

# -----------------------------
# 2. AANTAL METINGEN PER DAG
# -----------------------------
st.subheader("Aantal metingen op gekozen dag")

aantal = len(df_dag)

fig_counts = go.Figure()
fig_counts.add_trace(go.Bar(x=[str(gekozen_dag)], y=[aantal], name="Aantal metingen"))
fig_counts.add_hline(y=144, line_dash="dot", line_color="red")
fig_counts.update_layout(title="Aantal metingen (verwacht: 144)")

st.plotly_chart(fig_counts, use_container_width=True)

# -----------------------------
# 3. TEMPERATUURINTERVALLEN
# -----------------------------
st.subheader("Verdeling van temperatuurintervallen")

bins = [-999, 0, 5, 10, 15, 20, 25, 30, 999]
labels = ["<0", "0–5", "5–10", "10–15", "15–20", "20–25", "25–30", ">30"]

df_dag['TempInterval'] = pd.cut(df_dag['Raw Value'], bins=bins, labels=labels)
interval_counts = df_dag['TempInterval'].value_counts().sort_index()

fig_intervals = px.bar(
    x=interval_counts.index,
    y=interval_counts.values,
    title="Verdeling van temperatuurintervallen",
    labels={'x': 'Interval (°C)', 'y': 'Aantal metingen'}
)

st.plotly_chart(fig_intervals, use_container_width=True)

# -----------------------------
# 4. HISTOGRAM RAW VALUE
# -----------------------------
st.subheader("Histogram van Raw Value")

fig_hist = px.histogram(
    df_dag,
    x='Raw Value',
    nbins=30,
    title="Histogram van Raw Value"
)

st.plotly_chart(fig_hist, use_container_width=True)
