# استخدم صورة بلاي‌رايت الجاهزة (تشمل Chromium وكل التبعيات)
FROM mcr.microsoft.com/playwright/python:v1.46.0-jammy

# مكان العمل
WORKDIR /app

# نسخ المتطلبات أولاً (للاستفادة من طبقة cache)
COPY requirements.txt /app/

# ثبّت باكج البايثون
# ملاحظة: لا حاجة لأمر playwright install هنا لأن الصورة أساساً فيها المتصفحات
RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt

# نسخ بقية المشروع
COPY . /app

# المنفذ
EXPOSE 8000

# شغّل FastAPI (النسخة مع الواجهة)
CMD ["uvicorn", "main_with_frontend:app", "--host", "0.0.0.0", "--port", "8000"]
