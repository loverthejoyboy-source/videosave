import json, ipaddress, threading, urllib.request, urllib.error
from urllib.parse import urlsplit, urljoin
import yt_dlp
import config as C
from validator import check

_sem = threading.BoundedSemaphore(C.MAX_PARALLEL)
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"

class Busy(Exception): pass
class Fail(Exception):
    def __init__(self, msg): super().__init__(msg); self.msg = msg

# অডিও এবং ভিডিও একসাথে একটি MP4 ফাইলে পাওয়ার সেটআপ
OPTS = {
    "quiet": True, 
    "no_warnings": True, 
    "skip_download": True, 
    "noplaylist": True,
    "playlist_items": "1", 
    "socket_timeout": 15, 
    "extractor_retries": 1,
    "nocheckcertificate": True, 
    "ignoreerrors": True,
    "format": "best[ext=mp4]/best" # এটি সাউন্ড সহ সেরা MP4 ভিডিও খুঁজবে
}

def _safe(u):
    try:
        s = urlsplit(u or ""); h = (s.hostname or "").lower()
    except ValueError:
        return False
    if s.scheme != "https" or "." not in h or h == "localhost":
        return False
    try:
        ipaddress.ip_address(h); return False
    except ValueError:
        return True

class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k): return None

def resolve(url):
    if (urlsplit(url).hostname or "").lower() not in C.SHORT_HOSTS:
        return url
    op = urllib.request.build_opener(_NoRedirect)
    for _ in range(3):
        try:
            op.open(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=10).close(); return url
        except urllib.error.HTTPError as e:
            loc = e.headers.get("Location") if e.code in (301, 302, 303, 307, 308) else None
            if not loc: return url
            nxt = check(urljoin(url, loc))
            if not nxt: raise Fail("This short link points to an unsupported site.")
            url = nxt[1]
        except Exception:
            return url
    return url

def _why(e):
    m = str(e).lower()
    if any(x in m for x in ("sign in to confirm", "not a bot", "429", "too many requests")):
        return "The platform is blocking our free server right now. Try again later."
    if any(x in m for x in ("login", "log in", "cookies", "private", "age-restricted", "authenticat")):
        return "This video needs a login, is private, or is age-restricted."
    if "unsupported url" in m:
        return "This type of link isn't supported."
    return "Couldn't read this link."

def _build(info):
    if info and info.get("_type") == "playlist":
        info = next((e for e in info.get("entries") or [] if e), None)
    if not info: return None
    out, seen = [], set()
    
    cands = list(info.get("formats") or [])
    if info.get("url"): cands.append(info)
    
    for f in cands:
        if f.get("vcodec") == "none" and f.get("acodec") == "none": continue
        if f.get("protocol", "https") not in ("https", "http") or not _safe(f.get("url")): continue
        
        h = int(f.get("height") or 0); ext = str(f.get("ext") or "mp4")[:5]
        if ext not in ("mp4", "webm"): continue
        
        if (h, ext) in seen: continue
        seen.add((h, ext))
        
        label = f"{h}p" if h else "HD/Video"
        out.append({"h": h, "label": label, "ext": ext,
                    "size": f.get("filesize") or f.get("filesize_approx"), "url": f["url"]})
                    
    if not out: return None
    out.sort(key=lambda x: -x["h"])
    for o in out: o.pop("h")
    
    th = info.get("thumbnail")
    return {"title": str(info.get("title") or "Video")[:120], "thumb": th if _safe(th) else None, "formats": out[:6]}

def extract(url):
    url = resolve(url)
    if not _sem.acquire(blocking=False):
        raise Busy()
    err = None
    try:
        with yt_dlp.YoutubeDL(OPTS) as y:
            res = _build(y.extract_info(url, download=False))
        if res: return res
    except Exception as e:
        err = e; print("yt-dlp failed:", type(e).__name__, str(e)[:200], flush=True)
    finally:
        _sem.release()
        
    raise Fail(_why(err) if err else "Couldn't find a downloadable video.")
