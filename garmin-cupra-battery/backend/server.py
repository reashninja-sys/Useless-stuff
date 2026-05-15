"""
Lightweight HTTP server that the Garmin widget polls for Cupra battery data.

Run with:  python server.py
Or:        gunicorn server:app

The /battery endpoint returns JSON that the watch widget understands.
Results are cached for CACHE_TTL seconds (default 5 min) to avoid hammering
the Cupra API on every wrist-raise.
"""

import os
import time
import logging
import threading
from datetime import datetime

from dotenv import load_dotenv
from flask import Flask, jsonify

from cupra_api import CupraClient, CupraAuthError, CupraAPIError

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

USERNAME = os.environ["CUPRA_USERNAME"]
PASSWORD = os.environ["CUPRA_PASSWORD"]
VIN = os.environ["CUPRA_VIN"]
CACHE_TTL = int(os.environ.get("CACHE_TTL", "300"))
PORT = int(os.environ.get("PORT", "5000"))

_client: CupraClient = CupraClient(USERNAME, PASSWORD, VIN)
_cache: dict = {
    "battery_level": None,
    "range_km": None,
    "charging": False,
    "charging_state": None,
    "last_updated": "--:--",
    "last_fetch": 0.0,
    "error": None,
}
_lock = threading.Lock()


def _fetch() -> None:
    data = _client.get_battery_status()
    now = datetime.now().strftime("%H:%M")
    with _lock:
        _cache.update(
            battery_level=data["battery_level"],
            range_km=data["range_km"],
            charging=data["charging"],
            charging_state=data["charging_state"],
            last_updated=now,
            last_fetch=time.time(),
            error=None,
        )
    logger.info(
        "Battery %s%%  range %skm  charging=%s",
        data["battery_level"],
        data["range_km"],
        data["charging"],
    )


@app.route("/battery")
def battery():
    with _lock:
        stale = time.time() - _cache["last_fetch"] > CACHE_TTL

    if stale:
        try:
            _fetch()
        except (CupraAuthError, CupraAPIError) as exc:
            logger.error("Cupra error: %s", exc)
            with _lock:
                _cache["error"] = str(exc)
        except Exception as exc:
            logger.exception("Unexpected fetch error")
            with _lock:
                _cache["error"] = str(exc)

    with _lock:
        if _cache["error"] and _cache["battery_level"] is None:
            return jsonify({"error": _cache["error"]}), 503

        return jsonify({
            "battery_level": _cache["battery_level"] or 0,
            "range_km": _cache["range_km"],
            "charging": _cache["charging"],
            "charging_state": _cache["charging_state"],
            "last_updated": _cache["last_updated"],
        })


@app.route("/health")
def health():
    with _lock:
        age = time.time() - _cache["last_fetch"]
    return jsonify({"status": "ok", "cache_age_s": round(age)})


@app.route("/refresh")
def refresh():
    """Force a fresh fetch (useful for testing)."""
    try:
        _fetch()
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500
    with _lock:
        return jsonify({"battery_level": _cache["battery_level"], "ok": True})


if __name__ == "__main__":
    logger.info("Performing initial Cupra data fetch...")
    try:
        _fetch()
    except Exception as exc:
        logger.warning("Initial fetch failed (will retry on first request): %s", exc)

    logger.info("Starting server on http://0.0.0.0:%d", PORT)
    app.run(host="0.0.0.0", port=PORT, debug=False)
