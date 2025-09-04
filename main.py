# main.py
# FastAPI service: POST /make-pdfs with JSON {"ids": [39509415, ...]}
# Returns application/zip containing per-brand PDFs.
from fastapi import FastAPI, Response
from pydantic import BaseModel
from typing import List, Dict
import io, zipfile, os
from collections import defaultdict

from scraper import scrape_car_detail_by_id, scrape_car_detail_by_url
# من:

# إلى:
from pdf_maker_v2 import build_brand_pdf_like_genesis as build_brand_pdf

app = FastAPI(title="Encar PDF Service", version="1.0.0")

class IDs(BaseModel):
    ids: List[str]

@app.get("/health")
def health():
    return {"ok": True}

@app.post("/make-pdfs")
def make_pdfs(payload: IDs):
    # 1) scrape cars
    cars = []
    for cid in payload.ids:
        cid = str(cid).strip()
        if cid.startswith("http"):
            car = scrape_car_detail_by_url(cid)
        else:
            car = scrape_car_detail_by_id(cid)
        cars.append(car)

    # 2) group by brand
    by_brand: Dict[str, List[dict]] = defaultdict(list)
    for c in cars:
        brand = c.get("brand") or "Unknown"
        by_brand[brand].append(c)

    # 3) build PDFs in-memory & zip
    memzip = io.BytesIO()
    with zipfile.ZipFile(memzip, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for brand, rows in by_brand.items():
            safe = "".join(ch for ch in brand if ch.isalnum() or ch in (" ", "_", "-")).strip() or "Unknown"
            pdf_buf = io.BytesIO()
            build_brand_pdf(brand, rows, pdf_buf)
            pdf_buf.seek(0)
            zf.writestr(f"{safe}.pdf", pdf_buf.read())
    memzip.seek(0)

    return Response(
        content=memzip.read(),
        media_type="application/zip",
        headers={
            "Content-Disposition": 'attachment; filename="encar_pdfs.zip"'
        },
    )

# To run locally:
#   pip install -r requirements.txt
#   playwright install
#   uvicorn main:app --host 0.0.0.0 --port 8000
