import streamlit as st
from datetime import date

st.set_page_config(page_title="Bautagebuch", layout="wide")

st.title("Bautagebuch")
st.subheader("Projekt: Helen Keller Realschule")

with st.form("form"):
    datum = st.date_input("Datum", value=date.today())
    geschoss = st.selectbox("Geschoss", ["E1", "E2", "O1"])
    bauleitung = st.text_input("Bauleitung")

    st.subheader("Wetter")
    wetter = st.multiselect(
        "Wetter auswählen",
        ["Sonnig", "Bewölkt", "Regen", "Schnee", "Frost", "Wind"]
    )
    temperatur = st.text_input("Temperatur (°C)")

    st.subheader("Personal")
    polier = st.number_input("Polier", min_value=0)
    vorarbeiter = st.number_input("Vorarbeiter", min_value=0)
    facharbeiter = st.number_input("Facharbeiter", min_value=0)
    bauwerker = st.number_input("Bauwerker", min_value=0)

    st.subheader("Arbeiten")
    arbeiten = st.text_area("Ausgeführte Arbeiten")

    st.subheader("Fotos")
    fotos = st.file_uploader("Fotos hochladen", type=["jpg","jpeg","png"], accept_multiple_files=True)

    speichern = st.form_submit_button("Speichern")

if speichern:
    st.success("Eintrag gespeichert (nur Vorschau).")
    st.write("Datum:", datum)
    st.write("Geschoss:", geschoss)
    st.write("Bauleitung:", bauleitung)
    st.write("Wetter:", wetter)
    st.write("Temperatur:", temperatur)
    st.write("Personal:",
             "Polier:", polier,
             "Vorarbeiter:", vorarbeiter,
             "Facharbeiter:", facharbeiter,
             "Bauwerker:", bauwerker)
    st.write("Arbeiten:", arbeiten)
