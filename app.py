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
# 1. INTERVAL CHECK (10 MIN)
# -----------------------------
df_dag['Interval'] = df_dag['Timestamp'].diff().dt.total_seconds() / 60

fig_interval = px.scatter(
    df_dag,
    x='Timestamp',
    y='Interval',
    color=df_dag['Interval'].apply(lambda x: 'OK' if x == 10 else 'FOUT'),
    title="Intervalcontrole (10-minuten check)",
    labels={'Interval': 'Verschil in minuten'}
)
fig_interval.add_hline(y=10, line_dash="dot", line_color="green")

# -----------------------------
# 2. AANTAL METINGEN PER DAG
# -----------------------------
aantal = len(df_dag)

fig_counts = go.Figure()
fig_counts.add_trace(go.Bar(x=[str(gekozen_dag)], y=[aantal], name="Aantal metingen"))
fig_counts.add_hline(y=144, line_dash="dot", line_color="red")
fig_counts.update_layout(title="Aantal metingen op gekozen dag")

# -----------------------------
# 3. TEMPERATUURINTERVALLEN
# -----------------------------
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

# -----------------------------
# 4. HISTOGRAM RAW VALUE
# -----------------------------
fig_hist = px.histogram(
    df_dag,
    x='Raw Value',
    nbins=30,
    title="Histogram van Raw Value"
)

# -----------------------------
# 2×2 GRID LAYOUT
# -----------------------------
col1, col2 = st.columns(2)
with col1:
    st.plotly_chart(fig_interval, use_container_width=True)
with col2:
    st.plotly_chart(fig_counts, use_container_width=True)

col3, col4 = st.columns(2)
with col3:
    st.plotly_chart(fig_intervals, use_container_width=True)
with col4:
    st.plotly_chart(fig_hist, use_container_width=True)
