import os
import string
import secrets
from threading import Lock
from urllib.parse import urlparse

from flask import Flask, request, jsonify, redirect, abort

app = Flask(__name__)

# Ephemeral in-memory storage (demo only)
_URLS: dict[str, str] = {}
_LOCK = Lock()

# Base URL used to construct short_url in the response.
# In kind via port-forward, you’ll typically use http://localhost:8080
BASE_URL = os.getenv("BASE_URL", "").rstrip("/")

CODE_LENGTH = int(os.getenv("CODE_LENGTH", "6"))
MAX_ATTEMPTS = 10

ALPHABET = string.ascii_letters + string.digits


def _is_valid_url(url: str) -> bool:
    try:
        p = urlparse(url)
        return p.scheme in ("http", "https") and bool(p.netloc)
    except Exception:
        return False


def _gen_code(n: int = CODE_LENGTH) -> str:
    return "".join(secrets.choice(ALPHABET) for _ in range(n))


@app.get("/healthz")
def healthz():
    return jsonify({"status": "ok"}), 200


@app.post("/shorten")
def shorten():
    data = request.get_json(silent=True) or {}
    long_url = (data.get("url") or "").strip()

    if not long_url or not _is_valid_url(long_url):
        return jsonify({"error": "invalid url; must be http(s)://..."}), 400

    with _LOCK:
        # Try to generate a unique code
        for _ in range(MAX_ATTEMPTS):
            code = _gen_code()
            if code not in _URLS:
                _URLS[code] = long_url
                break
        else:
            return jsonify({"error": "could not allocate short code"}), 500

    # Construct short_url (best-effort). If BASE_URL not set, return relative.
    if BASE_URL:
        short_url = f"{BASE_URL}/{code}"
    else:
        short_url = f"/{code}"

    return jsonify({"short_url": short_url, "code": code}), 200


@app.get("/<code>")
def resolve(code: str):
    with _LOCK:
        long_url = _URLS.get(code)

    if not long_url:
        abort(404)

    return redirect(long_url, code=302)


if __name__ == "__main__":
    # Dev-only. In container we run gunicorn.
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")))