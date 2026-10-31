import hmac, hashlib, time, re, threading
from collections import defaultdict, deque
from functools import wraps
from flask import request, jsonify
import config as C

BOT = re.compile(r"curl|wget|python|requests|httpx|aiohttp|scrapy|bot|spider|crawl|headless|"
                 r"selenium|puppeteer|playwright|phantom|java|go-http|axios|okhttp|libwww|php|"
                 r"node-fetch|postman|insomnia", re.I)
_lock, _hits = threading.Lock(), defaultdict(deque)

def client_ip():
    cf = request.headers.get("CF-Connecting-IP", "").strip()  # Render-এর Cloudflare এটা সেট করে
    if cf: return cf
    xs = [x.strip() for x in request.headers.get("X-Forwarded-For", "").split(",") if x.strip()]
    return xs[-C.TRUSTED_HOPS] if len(xs) >= C.TRUSTED_HOPS else (request.remote_addr or "?")

def hit(key, limit, window):
    now = time.time()
    with _lock:
        q = _hits[key]
        while q and now - q[0] > window: q.popleft()
        if len(q) >= limit: return False
        q.append(now)
        if len(_hits) > 20000:
            for k in [k for k, v in _hits.items() if not v or now - v[-1] > 86400]: _hits.pop(k, None)
        return True

def _sig(ts): return hmac.new(C.SECRET, f"{ts}|{client_ip()}".encode(), hashlib.sha256).hexdigest()[:32]
def make_token():
    ts = str(int(time.time())); return f"{ts}.{_sig(ts)}"
def valid_token(t):
    try:
        ts, sig = str(t).split(".", 1); age = time.time() - int(ts)
    except Exception: return False
    return 2 <= age <= C.TOKEN_TTL and hmac.compare_digest(sig, _sig(ts))

def err(code, msg, kind="error"):
    return jsonify(error=msg, kind=kind), code

def guard(f):
    @wraps(f)
    def w(*a, **k):
        ua = request.headers.get("User-Agent", "")
        if len(ua) < 20 or BOT.search(ua) or request.headers.get("Sec-Fetch-Site") != "same-origin":
            return err(403, "অনুরোধ গ্রহণযোগ্য নয়।")
        if request.mimetype != "application/json":
            return err(415, "অনুরোধ গ্রহণযোগ্য নয়।")
        ip = client_ip()
        if not (hit("g", C.GLOBAL_PER_MIN, 60) and hit(ip, C.RATE_PER_MIN, 60) and hit("d:" + ip, C.RATE_PER_DAY, 86400)):
            return err(429, "অনেক বেশি অনুরোধ। এক মিনিট পরে চেষ্টা করুন।")
        return f(*a, **k)
    return w

def init_security(app):
    @app.after_request
    def h(r):
        r.headers["Content-Security-Policy"] = (
            "default-src 'none'; script-src 'self'; style-src 'self'; img-src 'self' https: data:; "
            "connect-src 'self'; base-uri 'none'; form-action 'none'; "
            "frame-ancestors 'self' https://huggingface.co https://*.huggingface.co")
        r.headers["X-Content-Type-Options"] = "nosniff"
        r.headers["Referrer-Policy"] = "no-referrer"
        r.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        if request.path.startswith("/api/"): r.headers["Cache-Control"] = "no-store"
        return r
