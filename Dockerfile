FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

EXPOSE 80

ENV TARGET_BASE_URL=""
ENV TARGET_ENDPOINT="/webhook"

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:80", "app:app"]
