import json
import joblib
import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

df_stats = pd.read_csv("app/data/bezirk_kategorie_hilfsfrist.csv")
df_krit = pd.read_csv("app/data/bezirk_kategorie_kritikalitaet.csv")
geojson = json.load(open("app/berlin_bezirke.geojson"))
modell = joblib.load("app/data/rf_reg_kategorie.pkl")
feature_spalten = joblib.load("app/data/feature_spalten_kategorie.pkl")

#Auswahlfelder festlegen
bezirk_liste = sorted(df_stats["bezirk"].unique())

if "bezirk" not in st.session_state:
    st.session_state["bezirk"] = bezirk_liste[0]

bezirk = st.session_state["bezirk"]
st.write(f"Ausgewählter Bezirk: **{bezirk}** (auf die Karte klicken, um zu ändern)")
notfalltyp = st.selectbox("Notfalltyp", sorted(df_stats["Hauptbeschwerde_Text_Original"].unique()))
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

zeile = df_stats[
    (df_stats["bezirk"] == bezirk) &
    (df_stats["Hauptbeschwerde_Text_Original"] == notfalltyp)
]

if zeile.empty:
    st.warning("Für diese Kombination liegen keine ausreichend verlässlichen Daten vor.")
else:
    median_zeit = zeile["median_response_time"].iloc[0]
    quote = zeile["hilfsfrist_quote"].iloc[0]
    n = zeile["n"].iloc[0]
    kategorie_raw = zeile["kategorie_raw"].iloc[0]

    input_vektor = pd.DataFrame([[0] * len(feature_spalten)], columns=feature_spalten)
    input_vektor[f"district_{bezirk}"] = 1
    input_vektor[f"kategorie_{kategorie_raw}"] = 1
    input_vektor[f"typ_{einsatztyp}"] = 1

    vorhersage = modell.predict(input_vektor)[0]

    col1, col2 = st.columns(2)
    col1.metric("Historischer Median", f"{median_zeit/60:.1f} min")
    col1.metric("Hilfsfrist-Quote", f"{quote*100:.1f}%")
    col1.caption("Anteil der Einsätze mit Eintreffzeit ≤ 8 Minuten — medizinisch begründete Grenze, kein gesetzliches Limit (Berlins eigenes Schutzziel liegt bei 10–11 Minuten für 90% der Fälle).")
    col1.caption(f"Basiert auf {n} Einsätzen")
    col2.metric("Modell-Vorhersage", f"{vorhersage/60:.1f} min")

    st.subheader("Verteilung nach Dringlichkeitsstufe (AMPDS)")
    krit_zeile = df_krit[
        (df_krit["bezirk"] == bezirk) &
        (df_krit["kategorie_raw"] == kategorie_raw)
    ]
    if krit_zeile.empty:
        st.caption("Keine ausreichend verlässliche Aufschlüsselung für diese Kombination verfügbar.")
    else:
        reihenfolge = ["O", "A", "B", "C", "D", "E", "unbekannt"]
        krit_zeile = krit_zeile.set_index("criticality")
        krit_zeile = krit_zeile.reindex([k for k in reihenfolge if k in krit_zeile.index])
        st.bar_chart(krit_zeile["hilfsfrist_quote"])
        st.caption("AMPDS-Dringlichkeitsstufen (steigend): O=Omega (niedrig) < A=Alpha < B=Bravo < C=Charlie < D=Delta < E=Echo (lebensbedrohlich)")
        st.caption("Fallzahlen je Stufe: " + ", ".join(f"{k}: {int(v)}" for k, v in krit_zeile["n"].items()))