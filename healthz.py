"""Health check for the Leave Tracker backend.

Exits 0 when GET /api/health/ returns HTTP 200 with {"status": "ok"}, otherwise exits 1.
Uses only the standard library, so it runs anywhere Python is installed.

Usage:
    python healthz.py
    HEALTHCHECK_URL=http://backend:8000/api/health/ python healthz.py
"""

import json
import os
import sys
import urllib.error
import urllib.request

DEFAULT_URL = "http://127.0.0.1:8000/api/health/"
DEFAULT_TIMEOUT_SECONDS = 3.0


def main() -> int:
    url = os.environ.get("HEALTHCHECK_URL", DEFAULT_URL)
    try:
        timeout = float(os.environ.get("HEALTHCHECK_TIMEOUT_SECONDS") or DEFAULT_TIMEOUT_SECONDS)
    except ValueError:
        print("invalid HEALTHCHECK_TIMEOUT_SECONDS: must be a number")
        return 1
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            body = json.loads(response.read().decode("utf-8"))
            if response.status == 200 and body.get("status") == "ok":
                print(f"healthy: {url}")
                return 0
            print(f"unhealthy: {url} returned {response.status} {body}")
            return 1
    except (urllib.error.URLError, TimeoutError, ValueError, OSError) as exc:
        print(f"unhealthy: {url} ({exc})")
        return 1


if __name__ == "__main__":
    sys.exit(main())
