# pdf_maker.py
# Builds per-brand PDFs with car cards and thumbnail grids using ReportLab.
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, KeepTogether, PageBreak
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.lib.units import mm
import io, requests, os

# Optional: register an Arabic-friendly TTF if you have one available at runtime.
# You can drop a font file next to the app and uncomment:
# pdfmetrics.registerFont(TTFont('Arabic', 'Tajawal-Regular.ttf'))
# BASE_FONT = 'Arabic'
BASE_FONT = 'Helvetica'

HEADERS = {"User-Agent": "Mozilla/5.0"}

def fetch_image_bytes(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=20)
        r.raise_for_status()
        return io.BytesIO(r.content)
    except Exception:
        return None

def _styles():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="H1", fontName=BASE_FONT, fontSize=18, leading=22))
    styles.add(ParagraphStyle(name="H3", fontName=BASE_FONT, fontSize=12, leading=16))
    styles.add(ParagraphStyle(name="N", fontName=BASE_FONT, fontSize=10, leading=14))
    return styles

def car_card_flow(car: dict, styles, thumbs_per_row=3, thumb_w=55*mm, thumb_h=40*mm):
    flows = []
    title = f"{car.get('model','')} — {car.get('year','')} — ID: {car.get('id','')}"
    flows.append(Paragraph(title, styles['H3']))
    flows.append(Spacer(1, 3*mm))

    # Specs table
    spec_data = [
        ["السعر", car.get('price',''), "الممشى", car.get('mileage','')],
        ["القير", car.get('gear',''),  "المحرك", car.get('engine','')],
        ["الدفع", car.get('drive',''), "الحالة", car.get('paint','')],
        ["عدد الصور", str(car.get('image_count', 0)), "المصدر", car.get('source_url','')],
    ]
    spec_table = Table(spec_data, colWidths=[24*mm, 60*mm, 24*mm, 60*mm])
    spec_table.setStyle(TableStyle([
        ('BOX', (0,0), (-1,-1), 0.6, colors.black),
        ('INNERGRID', (0,0), (-1,-1), 0.4, colors.grey),
        ('BACKGROUND', (0,0), (-1,0), colors.whitesmoke),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('FONT', (0,0), (-1,-1), BASE_FONT, 9),
        ('ALIGN', (0,0), (-1,-1), 'RIGHT'),
    ]))
    flows.append(spec_table)
    flows.append(Spacer(1, 3*mm))

    # Thumbnail grid
    imgs = car.get('image_urls') or []
    if not imgs:
        flows.append(Paragraph("لا توجد صور متاحة لهذه السيارة.", styles['N']))
    else:
        row, grid = [], []
        for idx, url in enumerate(imgs):
            b = fetch_image_bytes(url)
            if b:
                im = Image(b, width=thumb_w, height=thumb_h)
            else:
                # placeholder table
                im = Table([["لا يمكن تحميل الصورة"]], colWidths=[thumb_w], rowHeights=[thumb_h])
                im.setStyle(TableStyle([
                    ('BOX', (0,0), (-1,-1), 0.5, colors.red),
                    ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                    ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                    ('FONT', (0,0), (-1,-1), BASE_FONT, 9),
                ]))
            row.append(im)
            if (idx + 1) % thumbs_per_row == 0:
                grid.append(row)
                row = []
        if row:
            while len(row) < thumbs_per_row:
                row.append(Spacer(1, thumb_h))
            grid.append(row)

        grid_table = Table(grid, hAlign='RIGHT',
                           colWidths=[thumb_w]*thumbs_per_row,
                           rowHeights=[thumb_h]*len(grid))
        grid_table.setStyle(TableStyle([
            ('LEFTPADDING', (0,0), (-1,-1), 2),
            ('RIGHTPADDING', (0,0), (-1,-1), 2),
            ('TOPPADDING', (0,0), (-1,-1), 2),
            ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ]))
        flows.append(grid_table)

    flows.append(Spacer(1, 6*mm))
    return [KeepTogether(flows)]

def build_brand_pdf(brand: str, cars: list, out_path: str):
    doc = SimpleDocTemplate(out_path, pagesize=A4,
                            leftMargin=15*mm, rightMargin=15*mm,
                            topMargin=15*mm, bottomMargin=15*mm)
    styles = _styles()
    elements = [Paragraph(brand, styles['H1']), Spacer(1, 6*mm)]
    for i, car in enumerate(cars):
        elements += car_card_flow(car, styles)
        # Page break between cars (optional). Comment if not desired:
        # if i < len(cars)-1: elements.append(PageBreak())
    doc.build(elements)
