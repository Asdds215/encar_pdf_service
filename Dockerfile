FROM python:3.11-slim
RUN apt-get update && apt-get install -y --no-install-recommends \
    libnss3 libatk1.0-0 libatk-bridge2.0-0 libdrm2 libxkbcommon0 libgbm1 \
    libasound2 libxcomposite1 libxdamage1 libxrandr2 libgtk-3-0 \
    fonts-liberation libpango-1.0-0 libpangocairo-1.0-0 \
    wget curl unzip && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt && pip install --no-cache-dir playwright && playwright install --with-deps chromium
COPY . /app
EXPOSE 8000
CMD ["uvicorn","main_with_frontend:app","--host","0.0.0.0","--port","8000"]