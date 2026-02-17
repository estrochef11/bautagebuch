import streamlit as st
from datetime import date
import io
from PIL import Image
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader


WEATHER_OPTIONS = ["Sonnig", "Bewölkt", "Regen", "Schnee", "Frost", "Wind"]

FONT_BODY = ("Helvetica", 10)
FONT_BODY_BOLD = ("Helvetica-Bold", 10)
FONT_TITLE = ("Helvetica-Bold", 11)
LINE_H = 5 * mm


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
# Text-Layout
# -------------------------------------------------
def split_text_to_lines(c, text, font_name, font_size, max_width_pt):
    c.setFont(font_name, font_size)
    text = (text or "").replace("\r\n", "\n").replace("\r", "\n")
    paragraphs = text.split("\n")

    lines = []
    for p in paragraphs:
        p = p.strip()
        if not p:
            lines.append("")
            continue
        words = p.split()
        cur = ""
        for w in words:
            test = (cur + " " + w).strip()
            if c.stringWidth(test, font_name, font_size) <= max_width_pt:
                cur = test
            else:
                if cur:
                    lines.append(cur)
                cur = w
        if cur:
            lines.append(cur)

    if not lines:
        lines = ["-"]
    return lines


def box_height_for_lines(num_lines):
    title_block = 14 * mm
    inner_padding = 6 * mm
    return title_block + inner_padding + max(1, num_lines) * LINE_H


def draw_lines(c, lines, x, y_start):
    c.setFont(*FONT_BODY)
    y = y_start
    for ln in lines:
        if ln == "":
            y -= LINE_H
        else:
            c.drawString(x, y, ln)
            y -= LINE_H
    return y


# -------------------------------------------------
# PDF Header / Boxes
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
    projekt_text = f"Projekt: {projekt}"

    c.setFont("Helvetica-Bold", 16)
    c.drawString(20 * mm, height - 20 * mm, projekt_text)

    text_width = c.stringWidth(projekt_text, "Helvetica-Bold", 16)
    c.setLineWidth(0.8)
    c.line(20 * mm, height - 22 * mm, 20 * mm + text_width, height - 22 * mm)

    c.setFont("Helvetica", 9)
    c.drawRightString(width - 20 * mm, 12 * mm, f"Seite {page_no}")


def draw_box_frame(c, x, y_top, w, h, title):
    y_bottom = y_top - h

    c.setLineWidth(0.5)
    c.rect(x, y_bottom, w, h)

    c.setFont(*FONT_TITLE)
    c.drawString(x + 4 * mm, y_top - 6 * mm, title)

    c.setLineWidth(0.4)
    c.setDash(2, 2)
    c.line(x, y_top - 8 * mm, x + w, y_top - 8 * mm)
    c.setDash()

    text_y = y_top - 14 * mm
    return text_y, y_bottom


# -------------------------------------------------
# Fotos
# -------------------------------------------------
def render_photos_from_y(c, width, height, photos, new_page_func, start_y):
    c.setFont("Helvetica-Bold", 13)
    c.drawString(20 * mm, start_y, "Fotodokumentation")

    base_top = start_y - 12 * mm
    cell_w = 80 * mm
    cell_h = 60 * mm
    cell_box_h = 70 * mm

    def positions_for_page(top_y):
        return [
            (20 * mm, top_y),
            (110 * mm, top_y),
            (20 * mm, top_y - 95 * mm),
            (110 * mm, top_y - 95 * mm),
        ]

    positions = positions_for_page(base_top)

    for idx, (name, img_bytes) in enumerate(photos, start=1):
        if (idx - 1) % 4 == 0 and idx != 1:
            new_page_func()
            c.setFont("Helvetica-Bold", 13)
            c.drawString(20 * mm, height - 28 * mm, "Fotodokumentation")
            base_top = height - 40 * mm
            positions = positions_for_page(base_top)

        pos = (idx - 1) % 4
        x_img, top_y = positions[pos]

        c.setLineWidth(0.4)
        c.rect(x_img, top_y - cell_box_h, cell_w, cell_box_h)

        c.setFont("Helvetica-Bold", 9)
        title = f"Foto {idx}: {name}"
        if len(title) > 60:
            title = title[:60] + "..."
        c.drawString(x_img + 3 * mm, top_y - 6 * mm, title)

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


# -------------------------------------------------
# PDF-Erstellung
# -------------------------------------------------
def create_pdf(data, photos):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    page_no = 1

    x = 15 * mm
    box_w = width - 30 * mm
    gap = 6 * mm
    bottom_margin = 18 * mm

    def render_header():
        draw_logo(c, width, height)
        draw_header(c, width, height, data["projekt"], page_no)

    def new_page():
        nonlocal page_no
        c.showPage()
        page_no += 1
        render_header()

    render_header()
    y = height - 35 * mm

    # Stammdaten (fix)
    stammdaten_h = 40 * mm
    text_y, y_bottom = draw_box_frame(c, x, y, box_w, stammdaten_h, "Stammdaten")

    # ---- Fett formatierte Bezeichnungen ----
    c.setFont(*FONT_BODY_BOLD)
    c.drawString(x + 4 * mm, text_y, "Datum:")
    c.setFont(*FONT_BODY)
    c.drawString(x + 30 * mm, text_y, data["datum"])

    c.setFont(*FONT_BODY_BOLD)
    c.drawString(x + 90 * mm, text_y, "Geschoss/Bereich:")
    c.setFont(*FONT_BODY)
    c.drawString(x + 130 * mm, text_y, data["geschoss"])

    text_y -= 6 * mm

    c.setFont(*FONT_BODY_BOLD)
    c.drawString(x + 4 * mm, text_y, "Arbeitsort:")
    c.setFont(*FONT_BODY)
    c.drawString(x + 35 * mm, text_y, data["arbeitsort"] or "-")

    text_y -= 6 * mm

    c.setFont(*FONT_BODY_BOLD)
    c.drawString(x + 4 * mm, text_y, "Bauleitung:")
    c.setFont(*FONT_BODY)
    c.drawString(x + 35 * mm, text_y, data["bauleitung"] or "-")

    text_y -= 6 * mm

    c.setFont(*FONT_BODY_BOLD)
    c.drawString(x + 4 * mm, text_y, "Wetter:")
    c.setFont(*FONT_BODY)
    c.drawString(x + 30 * mm, text_y, ", ".join(data["wetter"]) if data["wetter"] else "-")

    c.setFont(*FONT_BODY_BOLD)
    c.drawString(x + 90 * mm, text_y, "Temperatur:")
    c.setFont(*FONT_BODY)
    c.drawString(x + 125 * mm, text_y, (data["temperatur"] + " °C") if data["temperatur"] else "-")

    y = y_bottom - gap

    # Weitere Bereiche bleiben unverändert (dynamisch)
    def draw_dynamic_textbox(title, text):
        nonlocal y
        max_text_width = box_w - 8 * mm
        lines = split_text_to_lines(c, text, FONT_BODY[0], FONT_BODY[1], max_text_width)
        h_needed = box_height_for_lines(len(lines))

        if y - h_needed < bottom_margin:
            new_page()
            y = height - 35 * mm

        text_y_loc, y_bottom_loc = draw_box_frame(c, x, y, box_w, h_needed, title)
        draw_lines(c, lines, x + 4 * mm, text_y_loc)
        y = y_bottom_loc - gap

    draw_dynamic_textbox("Ausgeführte Arbeiten", data["arbeiten"])
    draw_dynamic_textbox("Materiallieferungen", data["material"])
    draw_dynamic_textbox("Behinderungen / Mängel", data["maengel"])

    # Unterschrift (Kasten)
    sig_h = 26 * mm
    if y - sig_h < bottom_margin:
        new_page()
        y = height - 35 * mm

    text_y, y_bottom = draw_box_frame(c, x, y, box_w, sig_h, "Unterschrift")
    line_y = text_y - 6 * mm
    c.setLineWidth(0.8)
    c.line(x + 35 * mm, line_y, x + box_w - 35 * mm, line_y)
    c.setFont("Helvetica", 9)
    c.drawCentredString(x + box_w / 2, line_y - 5 * mm, "Bauleiter / Bauherr")

    y_after_sig = y_bottom - (8 * mm)

    # Fotos ggf. gleiche Seite
    if photos:
        min_needed = 90 * mm
        if y_after_sig - min_needed < bottom_margin:
            new_page()
            start_y = height - 28 * mm
        else:
            start_y = y_after_sig

        render_photos_from_y(c, width, height, photos, new_page, start_y)

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
    polier = st.number_input("Polier", min_value=0, step=1)
    vorarbeiter = st.number_input("Vorarbeiter", min_value=0, step=1)
    facharbeiter = st.number_input("Facharbeiter", min_value=0, step=1)
    bauwerker = st.number_input("Bauwerker", min_value=0, step=1)

    st.subheader("Ausgeführte Arbeiten")
    arbeiten = st.text_area("Leistungen / Besonderheiten", height=120)

    st.subheader("Materiallieferungen")
    material = st.text_area("Material / Menge / Lieferant / Uhrzeit", height=90)

    st.subheader("Behinderungen / Mängel")
    maengel = st.text_area("Beschreibung / Ursache / Verantwortlicher / Dauer", height=90)

    st.subheader("Fotos")
    fotos = st.file_uploader("Fotos hochladen (JPG/PNG)", type=["jpg", "jpeg", "png"], accept_multiple_files=True)

    submit = st.form_submit_button("PDF erzeugen")

if submit:
    photo_list = []
    if fotos:
        for f in fotos:
            photo_list.append((f.name, f.read()))

    data = {
        "projekt": (projekt or "").strip() or "Projekt",
        "datum": datum.strftime("%d.%m.%Y"),
        "geschoss": (geschoss or "").strip() or "-",
        "arbeitsort": (arbeitsort or "").strip(),
        "bauleitung": (bauleitung or "").strip(),
        "wetter": wetter,
        "temperatur": (temperatur or "").strip(),
        "arbeiten": (arbeiten or "").strip(),
        "material": (material or "").strip(),
        "maengel": (maengel or "").strip(),
    }

    pdf = create_pdf(data, photo_list)

    filename = f"Bautagebuch_{data['projekt'].replace(' ', '_')}_{datum.strftime('%Y-%m-%d')}.pdf"

    st.success("PDF erstellt.")
    st.download_button("PDF herunterladen", data=pdf, file_name=filename, mime="application/pdf")
