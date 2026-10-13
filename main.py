import urllib.parse
from flask import Flask, request, jsonify
import requests, urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

app = Flask(__name__)

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

@app.route("/api/convert", methods=["POST"])
def convert():
    data = request.get_json(silent=True) or {}
    raw = (data.get("eat") or "").strip()
    if not raw:
        return jsonify({"ok": False, "error": "no input"}), 400

    eat = extract_eat(raw)
    if not eat:
        return jsonify({"ok": False, "error": "no EAT token in that link"}), 400

    try:
        r = requests.get(API, params={"access_token": eat},
                         headers={"User-Agent": "Mozilla/5.0"},
                         allow_redirects=True, timeout=20)
        q = urllib.parse.parse_qs(urllib.parse.urlparse(r.url).query)
        at = q.get("access_token", [""])[0]
        if not at:
            return jsonify({
                "ok": False,
                "error": "token expired or invalid",
                "raw_final": r.url[:200]
            }), 400
        return jsonify({
            "ok": True,
            "access_token": at,
            "nickname": urllib.parse.unquote(q.get("nickname", ["?"])[0]),
            "uid":      q.get("account_id", ["?"])[0],
            "region":   q.get("region", ["?"])[0],
        })
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500
