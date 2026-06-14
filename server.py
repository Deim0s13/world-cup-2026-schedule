#!/usr/bin/env python3
"""
Local server for the World Cup 2026 wallchart.
Serves static files and proxies:
  /scores            → ESPN scoreboard (live scores, results)
  /flags             → worldcup26.ir (team flags)
  /lineup?event=ID   → ESPN match summary, slimmed to XI + formation + subs
Usage: python3 server.py [port]   (default port: 8191)
"""
import http.server, subprocess, os, sys, time, threading, logging, json
from datetime import date
from urllib.parse import urlparse, parse_qs

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8191
DIRECTORY = os.path.dirname(os.path.abspath(__file__))
WC_API_BASE = "https://worldcup26.ir/get"
ESPN_BASE = "https://site.api.espn.com/apis/site/v2/sports/soccer/fifa.world/scoreboard"
SUMMARY_BASE = "https://site.api.espn.com/apis/site/v2/sports/soccer/fifa.world/summary"
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


def fetch_lineup(event_id: str) -> bytes:
    """Fetch ESPN match summary and slim it to ~3 KB: starting XI + formation + subs.
    The raw summary is ~400 KB, so we strip it server-side and cache the result."""
    cache_key = f"lineup:{event_id}"
    with _cache_lock:
        entry = _cache.get(cache_key)
        if entry and time.time() - entry["ts"] < CACHE_TTL:
            return entry["data"]

    raw = fetch_url(f"{SUMMARY_BASE}?event={event_id}", f"summary:{event_id}")
    d = json.loads(raw)

    rosters = []
    for r in d.get("rosters", []):
        xi = [
            {
                "n": p.get("athlete", {}).get("displayName"),
                "pos": p.get("position", {}).get("abbreviation"),
                "j": p.get("jersey"),
                "place": p.get("formationPlace"),
                "off": p.get("subbedOut"),
            }
            for p in r.get("roster", []) if p.get("starter")
        ]
        rosters.append({
            "team": r.get("team", {}).get("displayName"),
            "formation": r.get("formation"),
            "xi": xi,
        })

    subs = [
        {
            "m": e.get("clock", {}).get("displayValue"),
            "team": e.get("team", {}).get("displayName"),
            "on": e["participants"][0].get("athlete", {}).get("displayName"),
            "off": e["participants"][1].get("athlete", {}).get("displayName"),
        }
        for e in d.get("keyEvents", [])
        if e.get("type", {}).get("text") == "Substitution" and len(e.get("participants", [])) >= 2
    ]

    out = json.dumps({"rosters": rosters, "subs": subs}).encode()
    with _cache_lock:
        _cache[cache_key] = {"data": out, "ts": time.time()}
    return out


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
            except Exception as e:
                self.send_error(502, f"Scores proxy error: {e}")
        elif self.path == "/flags":
            url = f"{WC_API_BASE}/teams"
            try:
                data = fetch_url(url, "teams")
                self._send_json(data)
            except Exception as e:
                self.send_error(502, f"Flags proxy error: {e}")
        elif self.path.startswith("/lineup"):
            event_id = (parse_qs(urlparse(self.path).query).get("event") or [""])[0]
            if not event_id.isdigit():
                self.send_error(400, "Missing or invalid event id")
                return
            try:
                data = fetch_lineup(event_id)
                self._send_json(data)
            except Exception as e:
                self.send_error(502, f"Lineup proxy error: {e}")
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
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s",
                        datefmt="%Y-%m-%d %H:%M:%S")
    httpd = http.server.ThreadingHTTPServer(("", PORT), Handler)
    print(f"Serving on http://localhost:{PORT}", flush=True)
    httpd.serve_forever()
