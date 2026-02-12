FROM python:3.12-slim

# Install debugging tools
RUN apt-get update && apt-get install -y \
    curl \
    iputils-ping \
    dnsutils \
    net-tools \
    telnet \
    iproute2 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

EXPOSE 80

ENV TARGET_BASE_URL=""
ENV TARGET_ENDPOINT="/webhook"

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:80", "app:app"]
