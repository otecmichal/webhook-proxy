import os
import sys
import json
import logging
import hmac
import hashlib
import requests
from flask import Flask, request, jsonify

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

TARGET_BASE_URL = os.environ.get("TARGET_BASE_URL")
TARGET_ENDPOINT = os.environ.get("TARGET_ENDPOINT", "/webhook")
SECRET = os.environ.get("SECRET", "")

if not TARGET_BASE_URL:
    raise ValueError("TARGET_BASE_URL environment variable is required")

logger.info(
    f"Webhook proxy configured: TARGET_BASE_URL={TARGET_BASE_URL}, TARGET_ENDPOINT={TARGET_ENDPOINT}"
)


@app.route("/webhook-proxy", methods=["POST"])
def webhook_proxy():
    request_id = os.urandom(4).hex()
    logger.info(f"[{request_id}] === NEW REQUEST ===")
    logger.info(f"[{request_id}] Method: {request.method}")
    logger.info(f"[{request_id}] Path: {request.path}")
    logger.info(f"[{request_id}] Remote Addr: {request.remote_addr}")

    # Log all incoming headers
    logger.info(f"[{request_id}] --- INCOMING HEADERS ---")
    for key, value in request.headers:
        # Mask sensitive headers
        if (
            "signature" in key.lower()
            or "auth" in key.lower()
            or "token" in key.lower()
        ):
            logger.info(f"[{request_id}] {key}: [REDACTED]")
        else:
            logger.info(f"[{request_id}] {key}: {value}")

    try:
        target_url = f"{TARGET_BASE_URL.rstrip('/')}/{TARGET_ENDPOINT.lstrip('/')}"
        logger.info(f"[{request_id}] Target URL: {target_url}")

        # Get body first (needed for signature)
        body = request.get_data()

        # Preserve all original headers except host
        headers = {}
        for key, value in request.headers:
            if key.lower() != "host":
                headers[key] = value

        # Handle signature headers - re-sign with target secret if configured
        signature_headers = [k for k in headers if "signature" in k.lower()]
        for h in signature_headers:
            del headers[h]
            logger.info(f"[{request_id}] Removed original signature header: {h}")

        # Re-sign payload with target secret if configured
        if SECRET:
            # Generate HMAC-SHA256 signature (standard for GitHub/Coolify webhooks)
            signature = hmac.new(
                SECRET.encode("utf-8"), body, hashlib.sha256
            ).hexdigest()
            headers["X-Hub-Signature-256"] = f"sha256={signature}"
            logger.info(
                f"[{request_id}] Added X-Hub-Signature-256 header with target secret"
            )

        # Ensure Content-Type is set for JSON payloads
        if not headers.get("Content-Type"):
            headers["Content-Type"] = "application/json"

        # Log forwarded headers
        logger.info(f"[{request_id}] --- FORWARDING HEADERS ---")
        for key, value in headers.items():
            if (
                "signature" in key.lower()
                or "auth" in key.lower()
                or "token" in key.lower()
            ):
                logger.info(f"[{request_id}] {key}: [REDACTED]")
            else:
                logger.info(f"[{request_id}] {key}: {value}")
        logger.info(f"[{request_id}] --- REQUEST BODY ---")
        try:
            # Try to parse as JSON for better logging
            body_json = json.loads(body)
            logger.info(
                f"[{request_id}] Body (JSON): {json.dumps(body_json, indent=2)[:1000]}"
            )
        except:
            # If not JSON, log as text
            body_text = body.decode("utf-8", errors="replace")[:1000]
            logger.info(f"[{request_id}] Body (raw): {body_text}")

        logger.info(f"[{request_id}] Body size: {len(body)} bytes")

        logger.info(f"[{request_id}] --- SENDING REQUEST TO TARGET ---")
        response = requests.post(target_url, headers=headers, data=body, timeout=30)

        logger.info(f"[{request_id}] --- TARGET RESPONSE ---")
        logger.info(f"[{request_id}] Status Code: {response.status_code}")
        logger.info(f"[{request_id}] Response Headers: {dict(response.headers)}")
        logger.info(f"[{request_id}] Response Body: {response.text[:1000]}")

        logger.info(f"[{request_id}] === REQUEST COMPLETE ===")

        return jsonify(
            {
                "status": "success",
                "target_status": response.status_code,
                "target_response": response.text,
            }
        ), response.status_code

    except requests.exceptions.RequestException as e:
        logger.error(f"[{request_id}] Request Exception: {str(e)}")
        logger.error(f"[{request_id}] === REQUEST FAILED ===")
        return jsonify({"status": "error", "message": str(e)}), 502
    except Exception as e:
        logger.error(f"[{request_id}] Exception: {str(e)}")
        logger.error(f"[{request_id}] === REQUEST FAILED ===")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
