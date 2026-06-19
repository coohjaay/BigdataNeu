import json
import joblib
import streamlit as st
import pandas as pd
import altair as alt
import folium
from streamlit_folium import st_folium

df_bezirk_krit = pd.read_csv("app/data/bezirk_kritikalitaet.csv")
geojson = json.load(open("app/berlin_bezirke.geojson"))
modell = joblib.load("app/data/rf_reg.pkl")
feature_spalten = joblib.load("app/data/feature_spalten.pkl")

#Auswahlfelder festlegen
bezirk_liste = sorted(df_bezirk_krit["bezirk"].unique())

if "bezirk" not in st.session_state:
    st.session_state["bezirk"] = bezirk_liste[0]

bezirk = st.session_state["bezirk"]
st.write(f"Ausgewählter Bezirk: **{bezirk}** (auf die Karte klicken, um zu ändern)")

reihenfolge = ["O", "A", "B", "C", "D", "E"]
krit_label = {
    "O": "O — niedrig",
    "A": "A",
    "B": "B",
    "C": "C",
    "D": "D",
    "E": "E — lebensbedrohlich",
}
krit_beispiele = {
    "O": "geringste Dringlichkeit",
    "A": "z.B. Krampfanfall, Verbrennungen",
    "B": "z.B. Sturz/Absturz, Verletzungen",
    "C": "z.B. Atembeschwerden, Herzbeschwerden",
    "D": "z.B. Bewusstlosigkeit, Verkehrsunfall",
    "E": "z.B. Kreislaufstillstand",
}
dringlichkeit_optionen = [k for k in reihenfolge if k in df_bezirk_krit["criticality"].unique()]
dringlichkeit = st.selectbox(
    "Dringlichkeitsstufe (AMPDS)",
    dringlichkeit_optionen,
    format_func=lambda k: krit_label.get(k, k),
)
st.caption(krit_beispiele.get(dringlichkeit, ""))

einsatztyp = st.radio("Einsatztyp", ["Rettungsdienst", "Rettungsdienst mit Technischer Hilfeleistung"])

if einsatztyp == "Rettungsdienst":
    st.caption("Medizinischer Notfall z.B Erkrankung, Verletzung")
else:
    st.caption("Notfall mit zusätzlicher technischer Rettung z.B. Befreiung aus einem Fahrzeug")

m = folium.Map(location=[52.52, 13.405], zoom_start=10)

def style_function(feature):
    if feature["properties"]["name"] == bezirk:
        return {"fillColor": "#ff7800", "color": "black", "weight": 2, "fillOpacity": 0.7}
    return {"fillColor": "#3186cc", "color": "black", "weight": 1, "fillOpacity": 0.3}

folium.GeoJson(
    geojson,
    style_function=style_function,
    tooltip=folium.GeoJsonTooltip(fields=["name"])
).add_to(m)

karte_output = st_folium(m, width=700, height=500)

geklickt = karte_output.get("last_active_drawing")
if geklickt:
    geklickter_bezirk = geklickt["properties"]["name"]
    if geklickter_bezirk != st.session_state["bezirk"]:
        st.session_state["bezirk"] = geklickter_bezirk
        st.rerun()

zeile = df_bezirk_krit[
    (df_bezirk_krit["bezirk"] == bezirk) &
    (df_bezirk_krit["criticality"] == dringlichkeit)
]

if zeile.empty:
    st.warning("Für diese Kombination liegen keine ausreichend verlässlichen Daten vor.")
else:
    median_zeit = zeile["median_response_time"].iloc[0]
    quote = zeile["hilfsfrist_quote"].iloc[0]
    n = zeile["n"].iloc[0]

    input_vektor = pd.DataFrame([[0] * len(feature_spalten)], columns=feature_spalten)
    input_vektor[f"district_{bezirk}"] = 1
    input_vektor[f"criticality_{dringlichkeit}"] = 1
    input_vektor[f"typ_{einsatztyp}"] = 1

    vorhersage = modell.predict(input_vektor)[0]

    col1, col2 = st.columns(2)
    col1.metric("Historischer Median", f"{median_zeit/60:.1f} min")
    col1.metric("Hilfsfrist-Quote", f"{quote*100:.1f}%")
    col1.caption("Anteil der Einsätze mit Eintreffzeit ≤ 8 Minuten — medizinisch begründete Grenze, kein gesetzliches Limit (Berlins eigenes Schutzziel liegt bei 10–11 Minuten für 90% der Fälle).")
    col1.caption(f"Basiert auf {n} Einsätzen")
    col2.metric("Modell-Vorhersage", f"{vorhersage/60:.1f} min")

    st.subheader("Bezirk im Vergleich zum Berlin-Durchschnitt")
    berlin_zeile = df_bezirk_krit[df_bezirk_krit["criticality"] == dringlichkeit]
    berlin_quote = (berlin_zeile["hilfsfrist_quote"] * berlin_zeile["n"]).sum() / berlin_zeile["n"].sum()

    vergleich_daten = pd.DataFrame({
        "Vergleich": [bezirk, "Berlin-Durchschnitt"],
        "hilfsfrist_quote_prozent": [quote * 100, berlin_quote * 100],
    })

    chart = alt.Chart(vergleich_daten).mark_bar().encode(
        x=alt.X("Vergleich", sort=None, axis=alt.Axis(labelAngle=0), title=None),
        y=alt.Y("hilfsfrist_quote_prozent", title="Hilfsfrist-Quote (%)"),
        color=alt.Color("Vergleich", legend=None),
    )
    st.altair_chart(chart, use_container_width=True)
    differenz = quote * 100 - berlin_quote * 100
    richtung = "über" if differenz >= 0 else "unter"
    st.caption(
        f"{bezirk} liegt bei Dringlichkeitsstufe {dringlichkeit} {abs(differenz):.1f} Punkte {richtung} "
        f"dem Berlin-Durchschnitt. Dieser Bezirksunterschied fällt bei dringenden Einsätzen (Stufe E) am größten "
        f"aus (~40 Punkte) und bei weniger dringenden (Stufe O) am kleinsten (~11 Punkte)."
    )