import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

TARGET_BASE_URL = os.environ.get("TARGET_BASE_URL")
TARGET_ENDPOINT = os.environ.get("TARGET_ENDPOINT", "/webhook")

if not TARGET_BASE_URL:
    raise ValueError("TARGET_BASE_URL environment variable is required")


@app.route("/webhook-proxy", methods=["POST"])
def webhook_proxy():
    try:
        target_url = f"{TARGET_BASE_URL.rstrip('/')}/{TARGET_ENDPOINT.lstrip('/')}"

        # Preserve all original headers except host
        headers = {}
        for key, value in request.headers:
            if key.lower() != "host":
                headers[key] = value

        # Ensure Content-Type is set for JSON payloads
        if not headers.get("Content-Type"):
            headers["Content-Type"] = "application/json"

        # Add X-GitHub-Event header if not present (needed for Coolify)
        if not headers.get("X-GitHub-Event") and not headers.get("x-github-event"):
            headers["X-GitHub-Event"] = "push"

        response = requests.post(
            target_url, headers=headers, data=request.get_data(), timeout=30
        )

        return jsonify(
            {
                "status": "success",
                "target_status": response.status_code,
                "target_response": response.text,
            }
        ), response.status_code

    except requests.exceptions.RequestException as e:
        return jsonify({"status": "error", "message": str(e)}), 502
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80)
