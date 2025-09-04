# main_with_frontend.py
from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Dict
import io, zipfile
from collections import defaultdict
# Choose one of the builders:
# from pdf_maker_v2 import build_brand_pdf_like_genesis as build_brand_pdf
from pdf_maker_v2 import build_brand_pdf_like_genesis as build_brand_pdf
from scraper import scrape_car_detail_by_id, scrape_car_detail_by_url

app = FastAPI(title='Encar PDF Service', version='1.1.0')
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)
app.mount('/static', StaticFiles(directory='static', html=True), name='static')

class IDs(BaseModel):
    ids: List[str]

@app.get('/health')
def health(): return {'ok': True}

@app.post('/make-pdfs')
def make_pdfs(payload: IDs):
    cars = []
    for cid in payload.ids:
        cid = str(cid).strip()
        car = scrape_car_detail_by_url(cid) if cid.startswith('http') else scrape_car_detail_by_id(cid)
        cars.append(car)
    by_brand: Dict[str, List[dict]] = defaultdict(list)
    for c in cars:
        by_brand[c.get('brand') or 'Unknown'].append(c)
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', compression=zipfile.ZIP_DEFLATED) as z:
        for brand, rows in by_brand.items():
            from io import BytesIO
            mem = BytesIO()
            build_brand_pdf(brand, rows, mem)
            mem.seek(0)
            safe = ''.join(ch for ch in (brand or 'Unknown') if ch.isalnum() or ch in (' ', '_', '-')).strip() or 'Unknown'
            z.writestr(f'{safe}.pdf', mem.read())
    buf.seek(0)
    return Response(content=buf.read(), media_type='application/zip',
                    headers={'Content-Disposition':'attachment; filename="encar_pdfs.zip"'})