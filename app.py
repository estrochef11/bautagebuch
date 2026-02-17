import streamlit as st
from datetime import date
import io
from PIL import Image
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader


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
    # Projekt mit Vorspann
    projekt_text = f"Projekt: {projekt}"

    c.setFont("Helvetica-Bold", 16)
    c.drawString(20 * mm, height - 20 * mm, projekt_text)

    text_width = c.stringWidth(projekt_text, "Helvetica-Bold", 16)
    c.setLineWidth(0.8)
    c.line(20 * mm, height - 22 * mm, 20 * mm + text_width, height - 22 * mm)

    # Seitennummer
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

    if not words:
        c.drawString(x, y, "-")
        return y - 5 * mm

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

    def render_header():
        draw_logo(c, width, height)
        draw_header(c, width, height, data["projekt"], page_no)

    def new_page():
        nonlocal page_no
        c.showPage()
        page_no += 1
        render_header()

    render_header()

    # zusätzlicher Abstand unter Projektzeile
    y = height - 35 * mm

    box_width = width - 30 * mm
    x = 15 * mm

    # Stammdaten
    y_content = draw_box(c, x, y, box_width, 50 * mm, "Stammdaten")
    c.setFont("Helvetica", 10)

    c.drawString(x + 4 * mm, y_content, f"Datum: {data['datum']}")
    c.drawString(x + 90 * mm, y_content, f"Geschoss/Bereich: {data['geschoss']}")
    y_content -= 6 * mm

    c.drawString(x + 4 * mm, y_content, f"Arbeitsort / Einsatzort / Bauteil: {data['arbeitsort'] or '-'}")
    y_content -= 6 * mm

    c.drawString(x + 4 * mm, y_content, f"Bauleitung: {data['bauleitung'] or '-'}")
    y_content -= 6 * mm

    c.drawString(x + 4 * mm, y_content, f"Wetter: {', '.join(data['wetter']) if data['wetter'] else '-'}")
    c.drawString(x + 90 * mm, y_content, f"Temperatur: {data['temperatur'] + ' °C' if data['temperatur'] else '-'}")

    y -= 55 * mm

    # Personal
    y_content = draw_box(c, x, y, box_width, 30 * mm, "Personal")
    c.setFont("Helvetica", 10)
    c.drawString(x + 4 * mm, y_content, f"Polier: {data['polier']}")
    c.drawString(x + 70 * mm, y_content, f"Vorarbeiter: {data['vorarbeiter']}")
    y_content -= 6 * mm
    c.drawString(x + 4 * mm, y_content, f"Facharbeiter: {data['facharbeiter']}")
    c.drawString(x + 70 * mm, y_content, f"Bauwerker: {data['bauwerker']}")

    y -= 35 * mm

    # Arbeiten
    y_content = draw_box(c, x, y, box_width, 45 * mm, "Ausgeführte Arbeiten")
    wrap_text(c, data["arbeiten"], x + 4 * mm, y_content, 170)

    y -= 50 * mm

    # Material
    y_content = draw_box(c, x, y, box_width, 40 * mm, "Materiallieferungen")
    wrap_text(c, data["material"], x + 4 * mm, y_content, 170)

    y -= 45 * mm

    # Mängel
    y_content = draw_box(c, x, y, box_width, 40 * mm, "Behinderungen / Mängel")
    wrap_text(c, data["maengel"], x + 4 * mm, y_content, 170)

    # Fotos
    if photos:
        new_page()

        c.setFont("Helvetica-Bold", 13)
        c.drawString(20 * mm, height - 28 * mm, "Fotodokumentation")

        # zusätzlicher Abstand unter Fotodokumentation
        foto_start_y = height - 40 * mm

        positions = [
            (20 * mm, foto_start_y),
            (110 * mm, foto_start_y),
            (20 * mm, foto_start_y - 95 * mm),
            (110 * mm, foto_start_y - 95 * mm),
        ]

        cell_w = 80 * mm
        cell_h = 60 * mm

        for idx, (name, img_bytes) in enumerate(photos, start=1):
            if (idx - 1) % 4 == 0 and idx != 1:
                new_page()
                c.setFont("Helvetica-Bold", 13)
                c.drawString(20 * mm, height - 28 * mm, "Fotodokumentation")

            pos = (idx - 1) % 4
            x_img, top_y = positions[pos]

            c.setLineWidth(0.4)
            c.rect(x_img, top_y - 70 * mm, cell_w, 70 * mm)

            c.setFont("Helvetica-Bold", 9)
            c.drawString(x_img + 3 * mm, top_y - 6 * mm, f"Foto {idx}: {name}")

            try:
                compressed = compress_image(img_bytes)

                img = Image.open(compressed).convert("RGB")
                iw, ih = img.size
                scale = min(cell_w / iw, cell_h / ih)
                new_w = iw * scale
                new_h = ih * scale
                compressed.seek(0)

                c.drawImage(
                    ImageReader(compressed),
                    x_img + (cell_w - new_w) / 2,
                    (top_y - 12 * mm) - new_h,
                    width=new_w,
                    height=new_h,
                    preserveAspectRatio=True,
                    mask="auto",
                )
            except:
                pass

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

    geschoss = st.text_input("Geschoss / Bereich (frei)")
    arbeitsort = st.text_input("Arbeitsort / Einsatzort / Bauteil")
    bauleitung = st.text_input("Bauleitung")

    wetter = st.multiselect("Wetter", WEATHER_OPTIONS)
    temperatur = st.text_input("Temperatur (°C)")

    st.subheader("Personal (Anzahl)")
    polier = st.number_input("Polier", min_value=0)
    vorarbeiter = st.number_input("Vorarbeiter", min_value=0)
    facharbeiter = st.number_input("Facharbeiter", min_value=0)
    bauwerker = st.number_input("Bauwerker", min_value=0)

    st.subheader("Ausgeführte Arbeiten")
    arbeiten = st.text_area("Leistungen")

    st.subheader("Materiallieferungen")
    material = st.text_area("Material")

    st.subheader("Behinderungen / Mängel")
    maengel = st.text_area("Mängel")

    fotos = st.file_uploader("Fotos", type=["jpg", "jpeg", "png"], accept_multiple_files=True)

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
        "arbeitsort": arbeitsort,
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

    pdf = create_pdf(data, photo_list)

    filename = f"Bautagebuch_{projekt.replace(' ', '_')}_{datum.strftime('%Y-%m-%d')}.pdf"

    st.success("PDF erstellt.")
    st.download_button("PDF herunterladen", data=pdf, file_name=filename, mime="application/pdf")
