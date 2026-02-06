import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Combineer Dag + Tijd
df['Timestamp'] = pd.to_datetime(df['Dag'].astype(str) + ' ' + df['Tijd'].astype(str))
df = df.sort_values('Timestamp')

# -----------------------------
# 1. INTERVAL CHECK (10 MIN)
# -----------------------------
df['Interval'] = df['Timestamp'].diff().dt.total_seconds() / 60  # minuten

fig_interval = px.scatter(
    df,
    x='Timestamp',
    y='Interval',
    color=df['Interval'].apply(lambda x: 'OK' if x == 10 else 'FOUT'),
    title="Intervalcontrole (10-minuten check)",
    labels={'Interval': 'Verschil in minuten'}
)
fig_interval.add_hline(y=10, line_dash="dot", line_color="green")

# -----------------------------
# 2. AANTAL METINGEN PER DAG
# -----------------------------
df['Date'] = df['Timestamp'].dt.date
counts = df.groupby('Date').size().reset_index(name='Aantal')

fig_counts = px.bar(
    counts,
    x='Date',
    y='Aantal',
    title="Aantal metingen per dag",
    labels={'Aantal': 'Aantal metingen'}
)
fig_counts.add_hline(y=144, line_dash="dot", line_color="red")

# -----------------------------
# 3. TEMPERATUURINTERVALLEN
# -----------------------------
bins = [-999, 0, 5, 10, 15, 20, 25, 30, 999]
labels = ["<0", "0–5", "5–10", "10–15", "15–20", "20–25", "25–30", ">30"]

df['TempInterval'] = pd.cut(df['Raw Value'], bins=bins, labels=labels)
interval_counts = df['TempInterval'].value_counts().sort_index()

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
    df,
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
