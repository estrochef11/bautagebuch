import streamlit as st
from datetime import date
import io
from PIL import Image
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader


# Vorschläge – aber frei anpassbar
FLOOR_OPTIONS = [
    "EG",
    "1. OG",
    "2. OG",
    "UG",
    "DG",
    "Eigene Eingabe"
]

WEATHER_OPTIONS = ["Sonnig", "Bewölkt", "Regen", "Schnee", "Frost", "Wind"]


# -------------------------------------------------
# Bild-Komprimierung
# -------------------------------------------------

def compress_image(img_bytes, max_size=1800, quality=75):
    img = Image.open(io.BytesIO(img_bytes))

    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")

    w, h = img.size

    if max(w, h) > max_size:
        scale = max_size / max(w, h)
        img = img.resize((int(w * scale), int(h * scale)))

    out = io.BytesIO()
    img.save(out, format="JPEG", quality=quality, optimize=True)
    out.seek(0)
    return out


# -------------------------------------------------
# PDF Hilfsfunktionen
# -------------------------------------------------

def draw_logo(c, width, height):
    try:
        logo = Image.open("logo.png").convert("RGBA")
        buf = io.BytesIO()
        logo.save(buf, format="PNG")
        buf.seek(0)

        c.drawImage(
            ImageReader(buf),
            width - 60 * mm,
            height - 28 * mm,
            width=45 * mm,
            height=18 * mm,
            preserveAspectRatio=True,
            mask="auto",
        )
    except:
        pass


def draw_header(c, width, height, projekt, page_no):
    c.setFont("Helvetica-Bold", 16)
    c.drawString(20 * mm, height - 20 * mm, projekt)

    text_width = c.stringWidth(projekt, "Helvetica-Bold", 16)
    c.setLineWidth(0.8)
    c.line(20 * mm, height - 22 * mm, 20 * mm + text_width, height - 22 * mm)

    c.setFont("Helvetica", 9)
    c.drawRightString(width - 20 * mm, 12 * mm, f"Seite {page_no}")


def draw_box(c, x, y_top, width_box, height_box, title):
    y_bottom = y_top - height_box

    c.setLineWidth(0.5)
    c.rect(x, y_bottom, width_box, height_box)

    c.setFont("Helvetica-Bold", 11)
    c.drawString(x + 4 * mm, y_top - 6 * mm, title)

    c.setLineWidth(0.4)
    c.setDash(2, 2)
    c.line(x, y_top - 8 * mm, x + width_box, y_top - 8 * mm)
    c.setDash()

    return y_top - 14 * mm


def wrap_text(c, text, x, y, max_width_mm):
    c.setFont("Helvetica", 10)
    max_width = max_width_mm * mm
    words = (text or "").split()
    line = ""

    for word in words:
        test = (line + " " + word).strip()
        if c.stringWidth(test, "Helvetica", 10) <= max_width:
            line = test
        else:
            c.drawString(x, y, line)
            y -= 5 * mm
            line = word

    if line:
        c.drawString(x, y, line)
        y -= 5 * mm

    return y


# -------------------------------------------------
# PDF-Erstellung
# -------------------------------------------------

def create_pdf(data, photos):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    page_no = 1

    def new_page():
        nonlocal page_no
        c.showPage()
        page_no += 1
        draw_logo(c, width, height)
        draw_header(c, width, height, data["projekt"], page_no)

    draw_logo(c, width, height)
    draw_header(c, width, height, data["projekt"], page_no)

    y = height - 35 * mm
    box_width = width - 30 * mm
    x = 15 * mm

    # Stammdaten
    y_content = draw_box(c, x, y, box_width, 45 * mm, "Stammdaten")
    c.setFont("Helvetica", 10)

    c.drawString(x + 4 * mm, y_content, f"Datum: {data['datum']}")
    c.drawString(x + 90 * mm, y_content, f"Geschoss: {data['geschoss']}")
    y_content -= 6 * mm

    c.drawString(x + 4 * mm, y_content, f"Arbeitsort / Bauteil: {data['arbeitsort']}")
    y_content -= 6 * mm

    c.drawString(x + 4 * mm, y_content, f"Bauleitung: {data['bauleitung'] or '-'}")
    y_content -= 6 * mm

    c.drawString(x + 4 * mm, y_content, f"Wetter: {', '.join(data['wetter']) if data['wetter'] else '-'}")
    c.drawString(x + 90 * mm, y_content, f"Temperatur: {data['temperatur'] + ' °C' if data['temperatur'] else '-'}")

    # Weitere Bereiche unverändert (aus Platzgründen hier gekürzt)
    # ... Rest bleibt gleich wie vorher ...

    c.save()
    buffer.seek(0)
    return buffer.getvalue()


# -------------------------------------------------
# Streamlit Oberfläche
# -------------------------------------------------

st.set_page_config(page_title="Bautagebuch", layout="wide")
st.title("Digitales Bautagebuch")

with st.form("form"):
    projekt = st.text_input("Projektname", value="Estrobau Auerbach e.K.")
    datum = st.date_input("Datum", value=date.today())

    # Geschoss flexibel
    floor_selection = st.selectbox("Geschoss", FLOOR_OPTIONS)

    if floor_selection == "Eigene Eingabe":
        geschoss = st.text_input("Geschoss (frei eingeben)")
    else:
        geschoss = floor_selection

    arbeitsort = st.text_input("Arbeitsort / Einsatzort / Bauteil")
    bauleitung = st.text_input("Bauleitung")

    wetter = st.multiselect("Wetter", WEATHER_OPTIONS)
    temperatur = st.text_input("Temperatur (°C)")

    submit = st.form_submit_button("PDF erzeugen")

if submit:
    data = {
        "projekt": projekt,
        "datum": datum.strftime("%d.%m.%Y"),
        "geschoss": geschoss,
        "arbeitsort": arbeitsort,
        "bauleitung": bauleitung,
        "wetter": wetter,
        "temperatur": temperatur,
    }

    pdf = create_pdf(data, [])

    filename = f"Bautagebuch_{projekt.replace(' ', '_')}_{datum.strftime('%Y-%m-%d')}.pdf"

    st.success("PDF erstellt.")
    st.download_button("PDF herunterladen", data=pdf, file_name=filename, mime="application/pdf")
