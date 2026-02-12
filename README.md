# Webhook Proxy

A simple Flask-based webhook proxy that forwards webhook payloads from a public-facing interface to an internal endpoint.

## Environment Variables

- `TARGET_BASE_URL` (required): Base URL of the internal target service
- `TARGET_ENDPOINT` (optional): Target endpoint path (default: `/webhook`)

## Usage

### Docker

```bash
docker build -t webhook-proxy .
docker run -p 80:80 -e TARGET_BASE_URL=http://your-internal-service webhook-proxy
```

### Manual

```bash
pip install -r requirements.txt
TARGET_BASE_URL=http://your-internal-service python app.py
```

## Endpoint

- `POST /webhook-proxy` - Proxies webhook payloads to the configured target
