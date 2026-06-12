#!/usr/bin/env python3
"""
Local server for the World Cup 2026 wallchart.
Serves static files and proxies:
  /scores     → ESPN scoreboard (live scores, results)
  /flags      → worldcup26.ir (team flags)
  /api/tsdb/* → TheSportsDB (player data)
  /api/invidious/* → Invidious (anthem audio)
Usage: python3 server.py [port]   (default port: 8191)
"""
import http.server, subprocess, os, sys, time, threading, logging
from datetime import date

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8191
DIRECTORY = os.path.dirname(os.path.abspath(__file__))
WC_API_BASE = "https://worldcup26.ir/get"
ESPN_BASE = "https://site.api.espn.com/apis/site/v2/sports/soccer/fifa.world/scoreboard"
TSDB_BASE = "https://www.thesportsdb.com/api/v1/json/3"
INVIDIOUS_BASE = os.environ.get("INVIDIOUS_URL", "https://invidious.io")
TOURNAMENT_START = "20260611"
CACHE_TTL = 60  # seconds

_cache: dict = {}
_cache_lock = threading.Lock()

def fetch_url(url: str, cache_key: str) -> bytes:
    with _cache_lock:
        entry = _cache.get(cache_key)
        if entry and time.time() - entry["ts"] < CACHE_TTL:
            return entry["data"]

    result = subprocess.run(
        ["curl", "-s", "--max-time", "10", "-H", "Accept: application/json", url],
        capture_output=True, timeout=12
    )
    if result.returncode != 0:
        raise RuntimeError(f"curl exit {result.returncode}")

    with _cache_lock:
        _cache[cache_key] = {"data": result.stdout, "ts": time.time()}
    return result.stdout


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def do_GET(self):
        if self.path == "/scores":
            today = date.today().strftime("%Y%m%d")
            url = f"{ESPN_BASE}?dates={TOURNAMENT_START}-{today}"
            try:
                data = fetch_url(url, "espn")
                self._send_json(data)
            except Exception:
                self.send_error(502, "Proxy error")
        elif self.path == "/flags":
            url = f"{WC_API_BASE}/teams"
            try:
                data = fetch_url(url, "teams")
                self._send_json(data)
            except Exception:
                self.send_error(502, "Proxy error")
        elif self.path.startswith("/api/tsdb/"):
            endpoint = self.path[10:]  # strip /api/tsdb/
            url = f"{TSDB_BASE}/{endpoint}"
            try:
                result = subprocess.run(
                    ["curl", "-s", "--max-time", "10", "-H", "Accept: application/json", url],
                    capture_output=True, timeout=12
                )
                if result.returncode != 0:
                    raise RuntimeError(f"curl exit {result.returncode}")
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.send_header("Cache-Control", "public, max-age=86400")
                self.end_headers()
                self.wfile.write(result.stdout)
            except Exception:
                self.send_error(502, "Proxy error")
        elif self.path.startswith("/api/invidious/"):
            endpoint = self.path[15:]  # strip /api/invidious/
            url = f"{INVIDIOUS_BASE}/{endpoint}"
            try:
                result = subprocess.run(
                    ["curl", "-s", "--max-time", "30", "-H", "Accept: */*", url],
                    capture_output=True, timeout=35
                )
                if result.returncode != 0:
                    raise RuntimeError(f"curl exit {result.returncode}")
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.send_header("Cache-Control", "public, max-age=3600")
                self.end_headers()
                self.wfile.write(result.stdout)
            except Exception:
                self.send_error(502, "Proxy error")
        else:
            super().do_GET()

    def end_headers(self):
        # Prevent browsers from caching HTML — ensures iOS always gets fresh code
        if self.path.endswith(".html") or self.path == "/" or "." not in self.path.split("/")[-1]:
            self.send_header("Cache-Control", "no-cache, must-revalidate")
        super().end_headers()

    def _send_json(self, data: bytes):
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, fmt, *args):
        logging.info("%s - - [%s] %s", self.address_string(),
                     self.log_date_time_string(), fmt % args)


if __name__ == "__main__":
    import socket
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s",
                        datefmt="%Y-%m-%d %H:%M:%S")
    class DualStackServer(http.server.ThreadingHTTPServer):
        address_family = socket.AF_INET6
        def server_bind(self):
            self.socket.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 0)
            super().server_bind()
    try:
        httpd = DualStackServer(("::", PORT), Handler)
    except OSError:
        httpd = http.server.ThreadingHTTPServer(("", PORT), Handler)
    print(f"Serving on http://localhost:{PORT}", flush=True)
    httpd.serve_forever()
