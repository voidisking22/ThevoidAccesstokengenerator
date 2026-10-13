import urllib.parse, json
from http.server import BaseHTTPRequestHandler
import requests, urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

API = "https://api-otrss.garena.com/support/callback/"

def extract_eat(raw):
    raw = raw.strip()
    if "http" in raw or "?" in raw:
        q = urllib.parse.parse_qs(urllib.parse.urlparse(raw).query)
        v = q.get("eat", [""])[0]
        if v: return v
        f = urllib.parse.parse_qs(urllib.parse.urlparse(raw).fragment)
        return f.get("eat", [""])[0]
    return raw

class handler(BaseHTTPRequestHandler):
    def _json(self, code, obj):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        try:
            length = int(self.headers.get("Content-Length", 0))
            raw_body = self.rfile.read(length).decode() if length else "{}"
            data = json.loads(raw_body or "{}")
        except Exception:
            return self._json(400, {"ok": False, "error": "invalid json"})

        raw = (data.get("eat") or "").strip()
        if not raw:
            return self._json(400, {"ok": False, "error": "no input"})

        eat = extract_eat(raw)
        if not eat:
            return self._json(400, {"ok": False, "error": "no EAT token in that link"})

        try:
            r = requests.get(API, params={"access_token": eat},
                             headers={"User-Agent": "Mozilla/5.0"},
                             allow_redirects=True, timeout=20)
            q = urllib.parse.parse_qs(urllib.parse.urlparse(r.url).query)
            at = q.get("access_token", [""])[0]
            if not at:
                return self._json(400, {
                    "ok": False,
                    "error": "token expired or invalid",
                    "raw_final": r.url[:200]
                })
            return self._json(200, {
                "ok": True,
                "access_token": at,
                "nickname": urllib.parse.unquote(q.get("nickname", ["?"])[0]),
                "uid":      q.get("account_id", ["?"])[0],
                "region":   q.get("region", ["?"])[0],
            })
        except Exception as e:
            return self._json(500, {"ok": False, "error": str(e)})
