import streamlit as st
from datetime import date
import io
from PIL import Image

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader


FLOORS = ["E1", "E2", "O1"]
WEATHER_OPTIONS = ["Sonnig", "Bewölkt", "Regen", "Schnee", "Frost", "Wind"]


def draw_header(c, width, height, projekt, page_no):
    c.setFont("Helvetica", 9)
    c.drawString(20 * mm, height - 12 * mm, f"Projekt: {projekt}")
    c.drawRightString(width - 20 * mm, 12 * mm, f"Seite {page_no}")


def draw_logo_top_right(c, width, height):
    # Robustes Einfügen aus logo.png (falls vorhanden)
    try:
        logo = Image.open("logo.png").convert("RGBA")
        buf = io.BytesIO()
        logo.save(buf, format="PNG")
        buf.seek(0)

        # Position oben rechts
        # (x, y) ist unten links der Grafik
        c.drawImage(
            ImageReader(buf),
            width - 60 * mm,
            height - 30 * mm,
            width=45 * mm,
            height=18 * mm,
            preserveAspectRatio=True,
            mask="auto",
        )
    except Exception:
        # Kein Logo oder nicht lesbar -> einfach ohne Logo weiter
        pass


def add_wrapped_text(c, text, x, y, max_width_mm, font_name="Helvetica", font_size=11, line_height_mm=6):
    """
    Einfacher Textumbruch für ReportLab.
    """
    c.setFont(font_name, font_size)
    max_width = max_width_mm * mm
    words = (text or "").split()
    if not words:
        c.drawString(x, y, "-")
        return y - (line_height_mm * mm)

    line = ""
    for w in words:
        test = (line + " " + w).strip()
        if c.stringWidth(test, font_name, font_size) <= max_width:
            line = test
        else:
            c.drawString(x, y, line)
            y -= line_height_mm * mm
            line = w
    if line:
        c.drawString(x, y, line)
        y -= line_height_mm * mm
    return y


def create_pdf(data, photos):
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    width, height = A4

    page_no = 1

    # Logo + Header
    draw_logo_top_right(c, width, height)
    draw_header(c, width, height, data["projekt"], page_no)

    # Titel
    y = height - 35 * mm
    c.setFont("Helvetica-Bold", 14)
    c.drawString(20 * mm, y, "BAUTAGEBUCH – TAGESBERICHT")
    y -= 10 * mm

    c.setFont("Helvetica", 11)
    # Stammdaten
    lines = [
        f"Datum: {data['datum']}",
        f"Geschoss: {data['geschoss']}",
        f"Bauleitung: {data['bauleitung'] or '-'}",
        f"Wetter: {', '.join(data['wetter']) if data['wetter'] else '-'}",
        f"Temperatur: {data['temperatur'] + ' °C' if data['temperatur'] else '-'}",
        "",
        "Personal (Anzahl):",
        f"  Polier: {data['polier']}",
        f"  Vorarbeiter: {data['vorarbeiter']}",
        f"  Facharbeiter: {data['facharbeiter']}",
        f"  Bauwerker: {data['bauwerker']}",
        "",
        "Ausgeführte Arbeiten:",
    ]

    for t in lines:
        if y < 25 * mm:
            c.showPage()
            page_no += 1
            draw_logo_top_right(c, width, height)
            draw_header(c, width, height, data["projekt"], page_no)
            y = height - 25 * mm
            c.setFont("Helvetica", 11)

        c.drawString(20 * mm, y, t)
        y -= 6 * mm

    # Arbeiten mit Umbruch
    y = add_wrapped_text(c, data["arbeiten"] or "-", 20 * mm, y, max_width_mm=170)

    # Material
    if y < 35 * mm:
        c.showPage()
        page_no += 1
        draw_logo_top_right(c, width, height)
        draw_header(c, width, height, data["projekt"], page_no)
        y = height - 25 * mm

    c.setFont("Helvetica", 11)
    c.drawString(20 * mm, y, "Materiallieferungen:")
    y -= 6 * mm
    y = add_wrapped_text(c, data["material"] or "-", 20 * mm, y, max_width_mm=170)

    # Mängel
    if y < 35 * mm:
        c.showPage()
        page_no += 1
        draw_logo_top_right(c, width, height)
        draw_header(c, width, height, data["projekt"], page_no)
        y = height - 25 * mm

    c.setFont("Helvetica", 11)
    c.drawString(20 * mm, y, "Behinderungen / Mängel:")
    y -= 6 * mm
    y = add_wrapped_text(c, data["maengel"] or "-", 20 * mm, y, max_width_mm=170)

    # Fotos als Raster (4 pro Seite)
    if photos:
        def new_photo_page():
            nonlocal page_no
            c.showPage()
            page_no += 1
            draw_logo_top_right(c, width, height)
            draw_header(c, width, height, data["projekt"], page_no)
            c.setFont("Helvetica-Bold", 12)
            c.drawString(20 * mm, height - 20 * mm, "Fotodokumentation")

        new_photo_page()

        positions = [
            (20 * mm, height - 40 * mm),
            (110 * mm, height - 40 * mm),
            (20 * mm, height - 135 * mm),
            (110 * mm, height - 135 * mm),
        ]
        cell_w = 80 * mm
        cell_h = 60 * mm

        for idx, (name, img_bytes) in enumerate(photos, start=1):
            if (idx - 1) % 4 == 0 and idx != 1:
                new_photo_page()

            pos = (idx - 1) % 4
            x, top_y = positions[pos]

            # Bildtitel
            c.setFont("Helvetica", 9)
            title = f"Foto {idx}: {name}"
            if len(title) > 55:
                title = title[:55] + "..."
            c.drawString(x, top_y, title)

            try:
                img = Image.open(io.BytesIO(img_bytes)).convert("RGB")

                iw, ih = img.size
                scale = min(cell_w / iw, cell_h / ih)
                new_w = iw * scale
                new_h = ih * scale

                img_buf = io.BytesIO()
                img.save(img_buf, format="JPEG", quality=85)
                img_buf.seek(0)

                # Bild unter Titel platzieren
                c.drawImage(
                    ImageReader(img_buf),
                    x,
                    top_y - 5 * mm - new_h,
                    width=new_w,
                    height=new_h,
                    preserveAspectRatio=True,
                    mask="auto",
                )
            except Exception:
                c.drawString(x, top_y - 12 * mm, "Bild konnte nicht geladen werden.")

    c.save()
    buf.seek(0)
    return buf.getvalue()


# -------------------------
# Streamlit UI
# -------------------------
st.set_page_config(page_title="Bautagebuch", layout="wide")

st.title("Digitales Bautagebuch")
st.caption("PDF-Export mit Logo & Fotodokumentation (Raster)")

with st.form("bautagebuch_form"):
    projekt = st.text_input("Projektname", value="Estrobau Auerbach e.K.")
    datum = st.date_input("Datum", value=date.today())
    geschoss = st.selectbox("Geschoss", FLOORS)
    bauleitung = st.text_input("Bauleitung / Verantwortlicher")

    wetter = st.multiselect("Wetter (Mehrfachauswahl)", WEATHER_OPTIONS)
    temperatur = st.text_input("Temperatur (°C)")

    st.subheader("Personal (Anzahl)")
    polier = st.number_input("Polier", min_value=0, value=0, step=1)
    vorarbeiter = st.number_input("Vorarbeiter", min_value=0, value=0, step=1)
    facharbeiter = st.number_input("Facharbeiter", min_value=0, value=0, step=1)
    bauwerker = st.number_input("Bauwerker", min_value=0, value=0, step=1)

    st.subheader("Ausgeführte Arbeiten")
    arbeiten = st.text_area("Leistungsbeschreibung / Besonderheiten", height=120)

    st.subheader("Materiallieferungen")
    material = st.text_area("Material / Menge / Lieferant / Uhrzeit", height=80)

    st.subheader("Behinderungen / Mängel")
    maengel = st.text_area("Beschreibung / Ursache / Verantwortlicher / Dauer", height=80)

    st.subheader("Fotos")
    fotos = st.file_uploader(
        "Fotos hochladen (JPG/PNG) – werden im PDF als Raster (4 pro Seite) gesetzt",
        type=["jpg", "jpeg", "png"],
        accept_multiple_files=True,
    )

    submit = st.form_submit_button("PDF erzeugen")

if submit:
    photo_list = []
    if fotos:
        for f in fotos:
            photo_list.append((f.name, f.read()))

    data = {
        "projekt": projekt.strip() or "Projekt",
        "datum": datum.strftime("%d.%m.%Y"),
        "geschoss": geschoss,
        "bauleitung": bauleitung.strip(),
        "wetter": wetter,
        "temperatur": temperatur.strip(),
        "polier": int(polier),
        "vorarbeiter": int(vorarbeiter),
        "facharbeiter": int(facharbeiter),
        "bauwerker": int(bauwerker),
        "arbeiten": arbeiten.strip(),
        "material": material.strip(),
        "maengel": maengel.strip(),
    }

    pdf_bytes = create_pdf(data, photo_list)

    safe_project = "".join(ch for ch in data["projekt"] if ch.isalnum() or ch in (" ", "_", "-")).strip().replace(" ", "_")
    filename = f"Bautagebuch_{safe_project}_{datum.strftime('%Y-%m-%d')}_{geschoss}.pdf"

    st.success("PDF wurde erstellt.")
    st.download_button(
        "⬇️ PDF herunterladen",
        data=pdf_bytes,
        file_name=filename,
        mime="application/pdf",
    )

    if photo_list:
        st.subheader("Foto-Vorschau")
        for name, img in photo_list:
            st.image(img, caption=name, use_container_width=True)
