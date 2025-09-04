# Encar PDF Service (FastAPI + Playwright + ReportLab)

This service accepts Encar vehicle IDs (or full fem.encar.com detail URLs),
scrapes details & photos, groups cars by brand, and returns a ZIP of per-brand PDFs.

## Quick Start

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -m playwright install
uvicorn main:app --host 0.0.0.0 --port 8000
```

Test:
```bash
curl -X POST http://localhost:8000/make-pdfs \
  -H "Content-Type: application/json" \
  -d '{"ids": ["39509415", "https://fem.encar.com/cars/detail/39509415"]}' \
  -o encar_pdfs.zip
```

## Notes
- Update CSS selectors in `scraper.py` after inspecting the Encar DOM.
- Throttle requests if needed. Respect website terms.
- To deploy: use Render/Railway/Cloud Run/Replit. Expose `/make-pdfs`.
- Integrate with **Make**: add `HTTP > Make a request` module to POST the same JSON;
  then save the returned ZIP to Google Drive, or extract PDFs and store per file.
