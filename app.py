import streamlit as st
from datetime import date
import io
from PIL import Image
import os

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader


FLOORS = ["E1", "E2", "O1"]
WEATHER_OPTIONS = ["Sonnig", "Bewölkt", "Regen", "Schnee", "Frost", "Wind"]


def create_pdf(data, photos):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    # LOGO oben rechts
    if os.path.exists("logo.png"):
   # LOGO oben rechts (robuster)
try:
    logo = Image.open("logo.png")
    logo = logo.convert("RGBA")

    logo_buffer = io.BytesIO()
    logo.save(logo_buffer, format="PNG")
    logo_buffer.seek(0)

    c.drawImage(
        ImageReader(logo_buffer),
        width - 55 * mm,
        height - 30 * mm,
        width=40 * mm,
        height=20 * mm,
        preserveAspectRatio=True,
        mask='auto'
    )
except Exception:
    pass


    def header(page_no):
        c.setFont("Helvetica", 9)
        c.drawString(20 * mm, height - 12 * mm, f"Projekt: {data['projekt']}")
        c.drawRightString(width - 20 * mm, 12 * mm, f"Seite {page_no}")

    page_no = 1
    header(page_no)

    y = height - 35 * mm
    c.setFont("Helvetica-Bold", 14)
    c.drawString(20 * mm, y, "BAUTAGEBUCH – TAGESBERICHT")
    y -= 12 * mm

    c.setFont("Helvetica", 11)

    lines = [
        f"Datum: {data['datum']}",
        f"Geschoss: {data['geschoss']}",
        f"Bauleitung: {data['bauleitung'] or '-'}",
        f"Wetter: {', '.join(data['wetter']) if data['wetter'] else '-'}",
        f"Temperatur: {data['temperatur'] or '-'} °C",
        "",
        "Personal:",
        f"  Polier: {data['polier']}",
        f"  Vorarbeiter: {data['vorarbeiter']}",
        f"  Facharbeiter: {data['facharbeiter']}",
        f"  Bauwerker: {data['bauwerker']}",
        "",
        "Ausgeführte Arbeiten:",
        data['arbeiten'] or "-",
        "",
        "Materiallieferungen:",
        data['material'] or "-",
        "",
        "Behinderungen / Mängel:",
        data['maengel'] or "-",
    ]

    for txt in lines:
        if y < 25 * mm:
            c.showPage()
            page_no += 1
            header(page_no)
            y = height - 25 * mm
            c.setFont("Helvetica", 11)

        if len(txt) > 120:
            txt = txt[:120] + "..."

        c.drawString(20 * mm, y, txt)
        y -= 6 * mm

    # Fotos auf extra Seiten
    for i, (name, img_bytes) in enumerate(photos, start=1):
        c.showPage()
        page_no += 1
        header(page_no)

        c.setFont("Helvetica-Bold", 12)
        c.drawString(20 * mm, height - 25 * mm, f"Foto {i}: {name}")

        try:
            img = Image.open(io.BytesIO(img_bytes))
            img = img.convert("RGB")

            max_w = width - 40 * mm
            max_h = height - 60 * mm

            iw, ih = img.size
            scale = min(max_w / iw, max_h / ih)

            new_w = iw * scale
            new_h = ih * scale

            img_buffer = io.BytesIO()
            img.save(img_buffer, format="JPEG", quality=85)
            img_buffer.seek(0)

            c.drawImage(
                ImageReader(img_buffer),
                20 * mm,
                (height - 35 * mm) - new_h,
                width=new_w,
                height=new_h,
                preserveAspectRatio=True,
                mask='auto'
            )
        except:
            c.setFont("Helvetica", 11)
            c.drawString(20 * mm, height - 40 * mm, "Bild konnte nicht eingebettet werden.")

    c.save()
    buffer.seek(0)
    return buffer.getvalue()


st.set_page_config(page_title="Bautagebuch", layout="wide")

st.title("Digitales Bautagebuch")

with st.form("bautagebuch_form"):
    projekt = st.text_input("Projektname", value="Estrobau Auerbach e.K.")
    datum = st.date_input("Datum", value=date.today())
    geschoss = st.selectbox("Geschoss", FLOORS)
    bauleitung = st.text_input("Bauleitung / Verantwortlicher")

    wetter = st.multiselect("Wetter (Mehrfachauswahl)", WEATHER_OPTIONS)
    temperatur = st.text_input("Temperatur (°C)")

    st.subheader("Personal (Anzahl)")
    polier = st.number_input("Polier", min_value=0, value=0)
    vorarbeiter = st.number_input("Vorarbeiter", min_value=0, value=0)
    facharbeiter = st.number_input("Facharbeiter", min_value=0, value=0)
    bauwerker = st.number_input("Bauwerker", min_value=0, value=0)

    st.subheader("Ausgeführte Arbeiten")
    arbeiten = st.text_area("Leistungsbeschreibung / Besonderheiten", height=120)

    st.subheader("Materiallieferungen")
    material = st.text_area("Material / Menge / Lieferant / Uhrzeit", height=80)

    st.subheader("Behinderungen / Mängel")
    maengel = st.text_area("Beschreibung / Ursache / Verantwortlicher / Dauer", height=80)

    st.subheader("Fotos")
    fotos = st.file_uploader("Fotos hochladen", type=["jpg", "jpeg", "png"], accept_multiple_files=True)

    submit = st.form_submit_button("PDF erzeugen")

if submit:
    photo_list = []
    if fotos:
        for f in fotos:
            photo_list.append((f.name, f.read()))

    data = {
        "projekt": projekt,
        "datum": datum.strftime("%d.%m.%Y"),
        "geschoss": geschoss,
        "bauleitung": bauleitung,
        "wetter": wetter,
        "temperatur": temperatur,
        "polier": polier,
        "vorarbeiter": vorarbeiter,
        "facharbeiter": facharbeiter,
        "bauwerker": bauwerker,
        "arbeiten": arbeiten,
        "material": material,
        "maengel": maengel,
    }

    pdf_bytes = create_pdf(data, photo_list)

    filename = f"Bautagebuch_{projekt.replace(' ', '_')}_{datum.strftime('%Y-%m-%d')}_{geschoss}.pdf"

    st.success("PDF wurde erstellt.")
    st.download_button(
        "⬇️ PDF herunterladen",
        data=pdf_bytes,
        file_name=filename,
        mime="application/pdf"
    )

