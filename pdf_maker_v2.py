
# pdf_maker_v2.py
# Arabic-oriented layout to mimic user's Genesis PDF style:
# - Big brand header
# - For each car: specs table with Arabic labels, followed by a 3x2 (or up to 3x3) thumbnail grid.
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, KeepTogether
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
import io, requests

# Optional Arabic font registration (uncomment and provide TTF at runtime for better Arabic rendering)
# pdfmetrics.registerFont(TTFont('Arabic', 'Tajawal-Regular.ttf'))
BASE_FONT = 'Helvetica'  # change to 'Arabic' when font is available

HEADERS = {"User-Agent": "Mozilla/5.0"}

def _styles():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="Brand", fontName=BASE_FONT, fontSize=20, leading=24, alignment=2))   # right align
    styles.add(ParagraphStyle(name="CarTitle", fontName=BASE_FONT, fontSize=12, leading=16, alignment=2))
    styles.add(ParagraphStyle(name="N", fontName=BASE_FONT, fontSize=10, leading=14, alignment=2))
    styles.add(ParagraphStyle(name="Small", fontName=BASE_FONT, fontSize=9, leading=12, alignment=2))
    return styles

def _arabic_spec_table(car):
    # A two-row x 8-cell style table (labels right-to-left) similar to user's layout
    # Row1: الحالة/الدهان | الوقود | الممشى | المقاعد | سعر فتح المزاد | السيارة
    # Row2: القير | حجم المحرك | الدفع | ...
    # We'll present as a grid of label->value pairs to resemble their PDF
    labels_values = [
        ["الحالة/الدهان", car.get("paint","")   , "الوقود", car.get("fuel","بنزين") , "الممشى", car.get("mileage",""), "سعر فتح المزاد", car.get("opening_price","")],
        ["القير"       , car.get("gear","")    , "حجم المحرك", car.get("engine",""), "الدفع", car.get("drive",""), "السيارة", f"{car.get('model','')} {car.get('year','')}"],
    ]
    tbl = Table(labels_values, colWidths=[25*mm, 35*mm, 20*mm, 35*mm, 15*mm, 30*mm, 28*mm, 40*mm])
    tbl.setStyle(TableStyle([
        ('FONT', (0,0), (-1,-1), BASE_FONT, 9),
        ('ALIGN', (0,0), (-1,-1), 'RIGHT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOX', (0,0), (-1,-1), 0.8, colors.black),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('BACKGROUND', (0,0), (-1,0), colors.whitesmoke),  # header-ish first row
    ]))
    return tbl

def _placeholder_thumb(w, h, label="صورة"):
    # Create a placeholder drawing (used when no image bytes exist)
    from reportlab.graphics.shapes import Drawing, Rect, String
    d = Drawing(w, h)
    d.add(Rect(0, 0, w, h, strokeColor=colors.grey, fillColor=colors.Color(0.95,0.95,0.95), strokeWidth=0.8))
    d.add(String(w/2, h/2, label, textAnchor='middle', fontName=BASE_FONT, fontSize=9, fillColor=colors.grey))
    return d

def _fetch_image_bytes(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        r.raise_for_status()
        return io.BytesIO(r.content)
    except Exception:
        return None

def car_card(car: dict, styles, thumbs_per_row=3, thumb_w=60*mm, thumb_h=42*mm):
    flows = []
    # Title: Model — ID
    title = f"{car.get('model','')} — ID: {car.get('id','')}"
    flows.append(Paragraph(title, styles['CarTitle']))
    flows.append(Spacer(1, 2*mm))

    # Specs table
    flows.append(_arabic_spec_table(car))
    flows.append(Spacer(1, 2*mm))

    # Thumbnail grid (max 6 or 9 images depending on available)
    imgs = car.get('image_urls') or []
    max_imgs = min(len(imgs), 9)
    cells = []
    row = []
    for idx in range(max_imgs):
        b = _fetch_image_bytes(imgs[idx])
        if b:
            im = Image(b, width=thumb_w, height=thumb_h)
            row.append(im)
        else:
            row.append(_placeholder_thumb(thumb_w, thumb_h))
        if (idx + 1) % thumbs_per_row == 0:
            cells.append(row)
            row = []
    if row:
        while len(row) < thumbs_per_row:
            row.append(_placeholder_thumb(thumb_w, thumb_h, label=""))
        cells.append(row)

    if cells:
        from reportlab.platypus import Table, TableStyle
        grid = Table(cells, colWidths=[thumb_w]*thumbs_per_row, rowHeights=[thumb_h]*len(cells), hAlign='RIGHT')
        grid.setStyle(TableStyle([
            ('LEFTPADDING', (0,0), (-1,-1), 2),
            ('RIGHTPADDING', (0,0), (-1,-1), 2),
            ('TOPPADDING', (0,0), (-1,-1), 2),
            ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ]))
        flows.append(grid)

    flows.append(Spacer(1, 5*mm))
    return [KeepTogether(flows)]

def build_brand_pdf_like_genesis(brand: str, cars: list, out_stream):
    doc = SimpleDocTemplate(out_stream, pagesize=A4,
                            leftMargin=12*mm, rightMargin=12*mm,
                            topMargin=12*mm, bottomMargin=12*mm)
    styles = _styles()
    elements = [Paragraph(brand, styles['Brand']), Spacer(1, 5*mm)]

    for car in cars:
        elements += car_card(car, styles)

    doc.build(elements)
