import streamlit as st
import os
import pandas as pd
import plotly.graph_objects as go

st.title("AWS QC Dashboard – Temperatuur & Andere Elementen")

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

# ---------------------------------------------------------
# ⭐ INTERVAL-DETECTIE (alleen voor NIET-temperatuur)
# ---------------------------------------------------------

if element == "Air_Temperaturedeg_C_QC.xlsx":
    # Temperatuur blijft exact zoals jij hem hebt
    interval_sec = 600   # 10 minuten
else:
    # Automatische intervaldetectie voor andere elementen
    df_sorted = df_dag.sort_values("Timestamp")
    df_sorted["diff"] = df_sorted["Timestamp"].diff().dt.total_seconds()
    interval_sec = int(df_sorted["diff"].mode()[0])

# Aantal blokken per uur
blocks_per_hour = int(3600 / interval_sec)

# ---------------------------------------------------------
# ⭐ EXPECTED TIMESTAMPS
# ---------------------------------------------------------
start = pd.to_datetime(str(gekozen_dag) + " 00:00:00")
end = start + pd.Timedelta(days=1)

expected_times = pd.date_range(
    start=start,
    end=end,
    freq=f"{interval_sec}S",
    inclusive="left"
)

df_expected = pd.DataFrame({"Timestamp": expected_times})
df_expected["Status"] = df_expected["Timestamp"].isin(df_dag["Timestamp"])
df_expected["Hour"] = df_expected["Timestamp"].dt.hour
df_expected["Block"] = (df_expected["Timestamp"].dt.minute * 60 + df_expected["Timestamp"].dt.second) // interval_sec

# ---------------------------------------------------------
# ⭐ BLOKJESGRAFIEK
# ---------------------------------------------------------
st.subheader("Ontbrekende metingen voor de dag!")

cell_size = 30
gap = 5
rows = blocks_per_hour
cols = 24

fig = go.Figure()

for _, row in df_expected.iterrows():
    hour = row["Hour"]
    block = row["Block"]
    status = row["Status"]

    color = "green" if status else "red"

    x = hour * (cell_size + gap)
    y = (rows - 1 - block) * (cell_size + gap)

    fig.add_shape(
        type="rect",
        x0=x, x1=x + cell_size,
        y0=y, y1=y + cell_size,
        line=dict(width=0),
        fillcolor=color
    )

fig.update_xaxes(
    title_text="<b>Uur van de dag</b>",
    tickmode="array",
    tickvals=[h * (cell_size + gap) + cell_size/2 for h in range(cols)],
    ticktext=[f"<b>{h:02d}:00</b>" for h in range(cols)],
    showgrid=False,
    zeroline=False
)

fig.update_yaxes(
    title_text="<b>Tijdsblok</b>",
    tickmode="array",
    tickvals=[i * (cell_size + gap) + cell_size/2 for i in range(rows)],
    ticktext=[f"<b>{i}</b>" for i in range(rows)],
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

# ⭐ LEGENDA
st.markdown("**Legenda:** 🟩 Ontvangen meting   |   🟥 Ontbrekende meting")

# ---------------------------------------------------------
# ⭐ QC SAMENVATTING
# ---------------------------------------------------------
st.subheader("QC")

totaal_blokken = len(df_expected)
aanwezig = df_expected["Status"].sum()
ontbrekend = totaal_blokken - aanwezig
percentage = round((aanwezig / totaal_blokken) * 100, 1)

# QC-tekst dynamisch
if element == "Air_Temperaturedeg_C_QC.xlsx":
    meettekst = "De temperatuur wordt elke 10 minuten gemeten en geregistreerd."
else:
    minuten = interval_sec // 60
    if minuten >= 60:
        meettekst = f"Dit element wordt elk uur gemeten en geregistreerd."
    else:
        meettekst = f"Dit element wordt elke {minuten} minuten gemeten en geregistreerd."

qc_html = f"""
<div style="
    background-color:#f0f2f6;
    padding:18px;
    border-radius:10px;
    border-left:6px solid #4a90e2;
    font-size:16px;
">
<p>{meettekst}</p>
<p>In totaal moeten er <b>{totaal_blokken} metingen</b> zijn per dag.</p>
<p><b>Ontbrekende metingen:</b> {ontbrekend}.</p>
<p><b>Datacompleetheid:</b> {percentage}%.</p>
</div>
"""

st.markdown(qc_html, unsafe_allow_html=True)
