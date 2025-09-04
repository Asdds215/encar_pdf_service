# scraper.py
# Scrapes fem.encar.com detail pages using Playwright (headless Chromium).
# Adjust CSS selectors as needed if Encar changes the DOM.
from playwright.sync_api import sync_playwright
from urllib.parse import urljoin

DEFAULT_TIMEOUT = 20000  # ms

def _txt_or_empty(locator):
    try:
        t = locator.first.text_content()
        return (t or "").strip()
    except Exception:
        return ""

def _get_first_attr(locator, attr):
    try:
        v = locator.first.get_attribute(attr)
        return v
    except Exception:
        return None

def scrape_car_detail_by_id(car_id: str) -> dict:
    url = f"https://fem.encar.com/cars/detail/{car_id}"
    return scrape_car_detail_by_url(url)

def scrape_car_detail_by_url(url: str) -> dict:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.set_default_timeout(DEFAULT_TIMEOUT)
        page.goto(url, wait_until="networkidle")

        # Title/Model/Brand (try multiple selectors for robustness)
        title = (
            _txt_or_empty(page.locator("[data-testid='title'], h1, .car-title, .title"))
            or _txt_or_empty(page.locator("meta[property='og:title']")).strip()
        )
        brand_guess = title.split()[0] if title else "Unknown"

        # Common spec fallbacks (update these selectors after inspecting Encar DOM)
        price   = _txt_or_empty(page.locator("[data-testid='price'], .price, .price-area"))
        year    = _txt_or_empty(page.locator(".year, [data-testid='year']"))
        mileage = _txt_or_empty(page.locator(".mileage, [data-testid='mileage']"))
        gear    = _txt_or_empty(page.locator(".transmission, [data-testid='transmission']"))
        engine  = _txt_or_empty(page.locator(".engine, [data-testid='engine']"))
        drive   = _txt_or_empty(page.locator(".drive, [data-testid='drive']"))
        # Body paint status: RX / RW / X / W etc.
        paint   = _txt_or_empty(page.locator(".paint, [data-testid='paint'], .damage, .bodywork"))

        # Collect image URLs from gallery (try several common selectors)
        imgs = page.locator(
            ".gallery img, .photo img, img[data-testid='image'], img[src*='encar']"
        )
        image_urls = []
        count = imgs.count()
        for i in range(count):
            el = imgs.nth(i)
            src = el.get_attribute("data-src") or el.get_attribute("src")
            if src:
                # absolutize if relative
                image_urls.append(urljoin(url, src))

        # Unique & limit to a reasonable number to keep PDFs light
        seen = set()
        unique = []
        for u in image_urls:
            if u not in seen:
                seen.add(u)
                unique.append(u)
        image_urls = unique[:9]  # up to 9 thumbs per car (3x3 grid)

        browser.close()

        return {
            "id": url.split("/")[-1],
            "brand": brand_guess or "Unknown",
            "model": title or "Unknown",
            "year": year or "",
            "mileage": mileage or "",
            "price": price or "",
            "gear": gear or "",
            "engine": engine or "",
            "drive": drive or "",
            "paint": paint or "",
            "image_urls": image_urls,
            "image_count": len(image_urls),
            "source_url": url,
        }
