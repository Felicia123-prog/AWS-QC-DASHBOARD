import streamlit as st
import os
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

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
# 1. CUSTOM BLOCKS TIMELINE (GEDRAAIDE ASSEN + SPATIES)
# -----------------------------
st.subheader("Ontbrekende metingen (10-minuten blokjes – gedraaide assen)")

# Verwachte timestamps
start = pd.to_datetime(str(gekozen_dag) + " 00:00:00")
expected_times = pd.date_range(start=start, periods=144, freq="10min")

df_expected = pd.DataFrame({"Timestamp": expected_times})
df_expected["Status"] = df_expected["Timestamp"].isin(df_dag["Timestamp"])
df_expected["Hour"] = df_expected["Timestamp"].dt.hour
df_expected["Block"] = df_expected["Timestamp"].dt.minute // 10  # 0 t/m 5

# Raster parameters
cell_size = 30
gap = 5  # spatie tussen blokjes
rows = 6   # 10-minuten blokken
cols = 24  # uren

fig = go.Figure()

# Voeg blokjes toe
for _, row in df_expected.iterrows():
    hour = row["Hour"]          # X-as
    block = row["Block"]        # Y-as
    status = row["Status"]

    color = "green" if status else "red"

    # Posities met spaties
    x = hour * (cell_size + gap)
    y = (5 - block) * (cell_size + gap)  # 00 bovenaan, 50 onderaan

    fig.add_shape(
        type="rect",
        x0=x, x1=x + cell_size,
        y0=y, y1=y + cell_size,
        line=dict(width=0),
        fillcolor=color
    )

# As-instellingen
fig.update_xaxes(
    range=[0, cols * (cell_size + gap)],
    tickmode="array",
    tickvals=[h * (cell_size + gap) + cell_size/2 for h in range(cols)],
    ticktext=[f"{h:02d}:00" for h in range(cols)],
    showgrid=False,
    zeroline=False
)

fig.update_yaxes(
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
    margin=dict(l=40, r=40, t=40, b=40),
    title="Missing Blocks Timeline – Gedraaide Assen (🟥 ontbreekt, 🟩 aanwezig)",
    plot_bgcolor="white"
)

st.plotly_chart(fig, use_container_width=False)

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
