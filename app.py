import streamlit as st
import os
import pandas as pd
import plotly.graph_objects as go

st.title("AWS QC Dashboard – Temperatuur (Raw Value)")

# 📁 Detecteer stations
data_path = "data"
stations = [d for d in os.listdir(data_path) if os.path.isdir(os.path.join(data_path, d))]

station = st.selectbox("Kies een station", stations)

# 📄 Automatisch temperatuur-bestand kiezen
station_path = os.path.join(data_path, station)
temp_file = "Air_Temperaturedeg_C_QC.xlsx"
file_path = os.path.join(station_path, temp_file)

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
# 1. CUSTOM BLOCKS TIMELINE
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

# -----------------------------
# ⭐ BELANGRIJKSTE FIX:
# Status = True ALS er een echte Raw Value is
# -----------------------------
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
# 2. QC SAMENVATTING
# -----------------------------
st.subheader("QC")

totaal_blokken = 144
aanwezig = df_expected["Status"].sum()
ontbrekend = totaal_blokken - aanwezig
percentage = round((aanwezig / totaal_blokken) * 100, 1)

kwaliteit = (
    "Voldoende — dag voldoet aan de minimale eis."
    if percentage >= 75
    else "Onvoldoende — minder dan 75% datacompleetheid."
)

qc_html = f"""
<div style="
    background-color:#f0f2f6;
    padding:18px;
    border-radius:10px;
    border-left:6px solid #4a90e2;
    font-size:16px;
">
<p>De temperatuur wordt elke 10 minuten gemeten en geregistreerd.</p>
<p>In totaal moeten er <b>144 metingen</b> zijn per dag.</p>
<p><b>Ontbrekende metingen:</b> {ontbrekend} van de 144.</p>
<p><b>Datacompleetheid:</b> {percentage}%.</p>
<p><b>Kwaliteit:</b> {kwaliteit}</p>
<p>Minimaal <b>75%</b> van de datametingen moet aanwezig zijn om te voldoen aan de kwaliteitsnorm.</p>
</div>
"""

st.markdown(qc_html, unsafe_allow_html=True)

# ---------------------------------------------------------
# 3. MAANDOVERZICHT QC – TEMPERATUUR
# ---------------------------------------------------------

st.subheader("Maandelijkse QC – Temperatuur")

# Alle unieke dagen in de dataset
alle_dagen = sorted(df['Timestamp'].dt.date.unique())

qc_resultaten = []

for dag in alle_dagen:
    df_dag = df[df['Timestamp'].dt.date == dag].copy()

    # Raw Value numeriek maken
    df_dag["Raw Value"] = pd.to_numeric(df_dag["Raw Value"], errors="coerce")

    # ⭐ Alleen echte metingen tellen
    aanwezig = df_dag["Raw Value"].notna().sum()

    # Verwachte 144 metingen
    totaal = 144
    percentage = round((aanwezig / totaal) * 100, 1)

    status = "goed" if percentage >= 75 else "slecht"

    qc_resultaten.append({
        "Dag": dag,
        "Aanwezig": aanwezig,
        "Percentage": percentage,
        "Status": status
    })

qc_df = pd.DataFrame(qc_resultaten)

# -----------------------------
# GRAFIEK MAANDOVERZICHT
# -----------------------------

fig2 = go.Figure()

cell_size = 40
gap = 10

for i, row in qc_df.iterrows():
    kleur = "green" if row["Status"] == "goed" else "red"

    x0 = i * (cell_size + gap)
    x1 = x0 + cell_size

    fig2.add_shape(
        type="rect",
        x0=x0, x1=x1,
        y0=0, y1=cell_size,
        line=dict(width=0),
        fillcolor=kleur
    )

    # Dagnummer tonen
    fig2.add_annotation(
        x=x0 + cell_size/2,
        y=cell_size/2,
        text=str(row["Dag"].day),
        showarrow=False,
        font=dict(color="white", size=14)
    )

fig2.update_xaxes(
    visible=False,
    range=[0, len(qc_df) * (cell_size + gap)]
)

fig2.update_yaxes(
    visible=False,
    range=[0, cell_size]
)

fig2.update_layout(
    height=150,
    margin=dict(l=20, r=20, t=20, b=20),
    plot_bgcolor="white"
)

st.plotly_chart(fig2, use_container_width=True)

# -----------------------------
# LEGENDA VOOR MAAND-QC
# -----------------------------
st.markdown("**Legenda:** 🟩 Geschikte dag (≥75% compleet)   |   🟥 Ongeschikte dag (<75% compleet)")

# -----------------------------
# BEREKENING VAN DAGEN IN MAAND
# -----------------------------

eerste_dag = alle_dagen[0]
maand = eerste_dag.month
jaar = eerste_dag.year

dagen_per_maand = {
    1: 31,
    2: 29 if (jaar % 4 == 0 and (jaar % 100 != 0 or jaar % 400 == 0)) else 28,
    3: 31,
    4: 30,
    5: 31,
    6: 30,
    7: 31,
    8: 31,
    9: 30,
    10: 31,
    11: 30,
    12: 31
}

totaal_dagen_in_maand = dagen_per_maand[maand]
dagen_met_data = len(alle_dagen)
ontbrekende_dagen = totaal_dagen_in_maand - dagen_met_data

# -----------------------------
# SAMENVATTING
# -----------------------------

goede_dagen = (qc_df["Status"] == "goed").sum()
slechte_dagen = (qc_df["Status"] == "slecht").sum()

st.markdown(f"""
### Samenvatting maand
- **Geschikte dagen (≥75% compleet):** {goede_dagen}  
- **Ongeschikte dagen (<75% compleet):** {slechte_dagen}  
- **Aantal dagen met data:** {dagen_met_data} van de {totaal_dagen_in_maand}  
- **Ontbrekende dagen:** {ontbrekende_dagen}  
""")

# ---------------------------------------------------------
# 4. GEREGISTREERDE TEMPERATUURMETINGEN & DATAKWALITEIT
# ---------------------------------------------------------

st.subheader("Geregistreerde Temperatuurmetingen & Datakwaliteit")
st.caption("We kijken naar de werkelijke gemeten data én de kwaliteit ervan.")

# 1. Timestamp bouwen
df["Tijd"] = df["Tijd"].astype(str).str.strip()
df["Timestamp"] = pd.to_datetime(
    df["Dag"].astype(str) + " " + df["Tijd"].astype(str),
    errors="coerce"
)

# 2. Raw Value numeriek maken
df["Raw Value"] = pd.to_numeric(df["Raw Value"], errors="coerce")

# 3. Gebruik de dag die bovenaan al gekozen is
df_dag = df[df["Timestamp"].dt.date == gekozen_dag].copy()

# 4. VERWIJDER ALLE rijen zonder Raw Value
df_dag = df_dag[df_dag["Raw Value"].notna()]

# 5. ALS ER GEEN ENKELE METING IS → MELDING TONEN
if df_dag.empty:
    st.warning(f"Er zijn geen temperatuurmetingen beschikbaar voor {gekozen_dag}.")
    st.stop()

# 6. Sorteren
df_dag = df_dag.sort_values("Timestamp")

# 6b. Raw Value afronden voor weergave
df_dag["Raw Value"] = df_dag["Raw Value"].round(1)

# ---------------------------------------------------------
# ⭐ 7. QC INTERVALLEN – SURINAME SPECIFIEK
# ---------------------------------------------------------

df_dag["QC_Flag"] = "OK"

# Onmogelijke waarden (<0°C)
df_dag.loc[df_dag["Raw Value"] < 0, "QC_Flag"] = "LOW_IMPOSSIBLE"

# Onrealistisch laag (0–5°C)
df_dag.loc[(df_dag["Raw Value"] >= 0) & (df_dag["Raw Value"] < 5), "QC_Flag"] = "LOW_SUSPICIOUS"

# Verdacht laag (5–20°C)
df_dag.loc[(df_dag["Raw Value"] >= 5) & (df_dag["Raw Value"] < 20), "QC_Flag"] = "LOW_RANGE"

# Normaal (20–37°C) → OK

# Extreem hoog (37–40°C)
df_dag.loc[(df_dag["Raw Value"] >= 37) & (df_dag["Raw Value"] <= 40), "QC_Flag"] = "HIGH"

# Zeer extreem hoog (>40°C)
df_dag.loc[df_dag["Raw Value"] > 40, "QC_Flag"] = "VERY_HIGH"

# ---------------------------------------------------------
# 8. Tabel tonen – MET HIGHLIGHTING
# ---------------------------------------------------------

def highlight_qc(val):
    colors = {
        "OK": "background-color: #b6f2b6",
        "LOW_RANGE": "background-color: #ffd27f",
        "LOW_SUSPICIOUS": "background-color: #fff59d",
        "LOW_IMPOSSIBLE": "background-color: #90caf9",
        "HIGH": "background-color: #ff8a80",
        "VERY_HIGH": "background-color: #d32f2f; color: white"
    }
    return colors.get(val, "")

st.write(f"Temperatuurmetingen op {gekozen_dag}:")
st.dataframe(
    df_dag[["Timestamp", "Raw Value", "QC_Flag"]]
    .style
    .applymap(highlight_qc, subset=["QC_Flag"])
    .format({"Raw Value": "{:.1f}"})
)

# ---------------------------------------------------------
# ⭐ LEGENDA – ONDER DE TABEL
# ---------------------------------------------------------

st.markdown("""
### Legenda datakwaliteit
- 🟩 **OK** — Normale waarden (20–37°C)  
- 🟧 **LOW_RANGE** — Verdacht laag (5–20°C)  
- 🟨 **LOW_SUSPICIOUS** — Onrealistisch laag (0–5°C)  
- 🟦 **LOW_IMPOSSIBLE** — Onmogelijk (<0°C)  
- 🟥 **HIGH** — Extreem hoog (37–40°C)  
- 🟥 **VERY_HIGH** — Zeer extreem hoog (>40°C)  
""")

# ---------------------------------------------------------
# 9. Grafiek tonen – MET QC-KLEUREN
# ---------------------------------------------------------

import plotly.express as px

fig = px.line(
    df_dag,
    x="Timestamp",
    y="Raw Value",
    title=f"Temperatuurverloop op {gekozen_dag}",
    markers=True,
    color="QC_Flag",
    color_discrete_map={
        "OK": "green",
        "LOW_RANGE": "orange",
        "LOW_SUSPICIOUS": "yellow",
        "LOW_IMPOSSIBLE": "blue",
        "HIGH": "red",
        "VERY_HIGH": "darkred"
    }
)

fig.update_yaxes(title_text="Temperatuur (°C)")
fig.update_xaxes(title_text="Tijd")

st.plotly_chart(fig, use_container_width=True)

# ---------------------------------------------------------
# ⭐ 10. QC SAMENVATTING – ONDER DE GRAFIEK
# ---------------------------------------------------------

laagste = df_dag["Raw Value"].min()
hoogste = df_dag["Raw Value"].max()
qc_counts = df_dag["QC_Flag"].value_counts()

st.markdown(f"""
### Samenvatting datakwaliteit
- **Laagste waarde:** {laagste}°C  
- **Hoogste waarde:** {hoogste}°C  
- **Aantal LOW_RANGE:** {qc_counts.get('LOW_RANGE', 0)}  
- **Aantal LOW_SUSPICIOUS:** {qc_counts.get('LOW_SUSPICIOUS', 0)}  
- **Aantal HIGH:** {qc_counts.get('HIGH', 0)}  
- **Aantal VERY_HIGH:** {qc_counts.get('VERY_HIGH', 0)}  
""")

# ⭐ Dagconclusie
if hoogste > 40:
    conclusie = "❌ De dag bevat zeer extreme hoge waarden (boven 40°C). Controle aanbevolen."
elif hoogste > 37:
    conclusie = "⚠️ De dag bevat extreme hoge waarden (boven 37°C)."
elif laagste < 20:
    conclusie = "ℹ️ De dag bevat lage waarden die niet typisch zijn voor Suriname."
else:
    conclusie = "✔️ De gemeten waarden vallen binnen het normale bereik."

st.markdown(f"### Dagconclusie\n{conclusie}")


# ---------------------------------------------------------
# ⭐ 11. MAANDSTATISTIEKEN – AUTOMATISCH OP BASIS VAN GEKOZEN DAG
# ---------------------------------------------------------

maand = gekozen_dag.month
jaar = gekozen_dag.year

df_maand = df[
    (df["Timestamp"].dt.month == maand) &
    (df["Timestamp"].dt.year == jaar)
].copy()

df_maand = df_maand[df_maand["Raw Value"].notna()]

if not df_maand.empty:

    # 1️⃣ Tel negatieve waarden
    negatieve_count = (df_maand["Raw Value"] < 0).sum()

    # 2️⃣ Filter negatieve waarden eruit voor laagste geldige waarde
    df_maand_pos = df_maand[df_maand["Raw Value"] >= 0]

    if not df_maand_pos.empty:
        laagste_maand = round(df_maand_pos["Raw Value"].min(), 1)
    else:
        laagste_maand = None  # geen geldige waarden

    hoogste_maand = round(df_maand["Raw Value"].max(), 1)

    st.markdown(f"""
    ### Maandstatistieken ({gekozen_dag.strftime('%B %Y')})
    - **Aantal negatieve waarden:** {negatieve_count}  
    - **Laagste geldige waarde in de maand:** {laagste_maand if laagste_maand is not None else "Geen geldige waarden"}°C  
    - **Hoogste waarde in de maand:** {hoogste_maand}°C  
    """)


# ---------------------------------------------------------
# ⭐ 12. MAAND-CONCLUSIE – GESCHIKTHEID VAN HET STATION
# ---------------------------------------------------------

if not df_maand.empty:

    problemen = []

    # ❌ Negatieve waarden
    if negatieve_count > 0:
        problemen.append(
            f"Er zijn {negatieve_count} negatieve waarden gevonden, wat fysiek onmogelijk is."
        )

    # ❌ Onrealistisch hoge minimumtemperatuur
    if laagste_maand is not None and laagste_maand > 30:
        problemen.append(
            "De laagste geldige waarde ligt boven 30°C, wat onrealistisch is voor Suriname."
        )

    # ❌ Onrealistisch lage minimumtemperatuur (na filtering)
    if laagste_maand is not None and laagste_maand < 5:
        problemen.append(
            "De laagste geldige waarde ligt onder 5°C, wat fysiek onmogelijk is."
        )
    elif laagste_maand is not None and laagste_maand < 10:
        problemen.append(
            "De laagste geldige waarde ligt onder 10°C, wat zeer onrealistisch is."
        )
    elif laagste_maand is not None and laagste_maand < 20:
        problemen.append(
            "De laagste geldige waarde ligt onder 20°C, wat niet typisch is voor Suriname."
        )

    # ❌ Onrealistisch hoge maximumtemperatuur
    if hoogste_maand > 45:
        problemen.append(
            "De maand bevat waarden boven 45°C, wat fysiek onmogelijk is."
        )
    elif hoogste_maand > 40:
        problemen.append(
            "De maand bevat extreem hoge waarden (>40°C)."
        )
    elif hoogste_maand > 37:
        problemen.append(
            "De maand bevat zeer hoge waarden (>37°C)."
        )

    # ⭐ Bouw conclusie
    if problemen:
        maand_conclusie = "❌ Het station is NIET geschikt voor deze maand.\n\n" + "\n".join(
            f"- {p}" for p in problemen
        )
    else:
        maand_conclusie = (
            "✔ Het station toont realistische waarden voor deze maand. "
            "Het station is geschikt voor verdere analyse."
        )

    st.markdown(f"### Maandconclusie\n{maand_conclusie}")
