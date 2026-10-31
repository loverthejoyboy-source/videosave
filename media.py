import json, ipaddress, threading, urllib.request, urllib.error
from urllib.parse import urlsplit, urljoin
import yt_dlp
import config as C
from validator import check


try:
    from rahad_all_downloader import alldl
    HAS_RAHAD = True
except ImportError:
    HAS_RAHAD = False

_sem = threading.BoundedSemaphore(C.MAX_PARALLEL)
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"

class Busy(Exception): pass
class Fail(Exception):
    def __init__(self, msg): super().__init__(msg); self.msg = msg

OPTS = {
    "quiet": True, 
    "no_warnings": True, 
    "skip_download": True, 
    "noplaylist": True,
    "playlist_items": "1", 
    "socket_timeout": 15, 
    "extractor_retries": 1,
    "nocheckcertificate": True, 
    "ignoreerrors": True
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
        return "YouTube is blocking our server (bot check). Trying alternative method..."
    if any(x in m for x in ("login", "log in", "cookies", "private", "age-restricted", "authenticat")):
        return "This video needs a login, is private, or is age-restricted."
    if "unsupported url" in m:
        return "This type of link isn't supported."
    return "Couldn't read this link. Trying alternative..."

def _build(info):
    if info and info.get("_type") == "playlist":
        info = next((e for e in info.get("entries") or [] if e), None)
    if not info: return None
    out, seen = [], set()
    cands = list(info.get("formats") or [])
    if info.get("url"): cands.append(info)
    for f in cands:
        if f.get("vcodec") == "none" or f.get("acodec") == "none": continue
        if f.get("protocol", "https") not in ("https", "http") or not _safe(f.get("url")): continue
        h = int(f.get("height") or 0); ext = str(f.get("ext") or "mp4")[:5]
        if (h, ext) in seen: continue
        seen.add((h, ext))
        out.append({"h": h, "label": f"{h}p" if h else "Video", "ext": ext,
                    "size": f.get("filesize") or f.get("filesize_approx"), "url": f["url"]})
    if not out: return None
    out.sort(key=lambda x: -x["h"])
    for o in out: o.pop("h")
    th = info.get("thumbnail")
    return {"title": str(info.get("title") or "Video")[:120], "thumb": th if _safe(th) else None, "formats": out[:6]}

def _cobalt(url):
    for base in C.COBALT_API_URLS:
        hdr = {"Accept": "application/json", "Content-Type": "application/json", "User-Agent": "clipkeep/1.1"}
        if C.COBALT_API_KEY: hdr["Authorization"] = "Api-Key " + C.COBALT_API_KEY
        try:
            req = urllib.request.Request(base, data=json.dumps({"url": url}).encode(), headers=hdr, method="POST")
            with urllib.request.urlopen(req, timeout=25) as r: d = json.loads(r.read(200000))
        except Exception as e:
            print("cobalt failed:", type(e).__name__, flush=True); continue
        items = []
        if d.get("status") in ("tunnel", "redirect") and _safe(d.get("url")):
            fn = str(d.get("filename") or ""); ext = fn.rsplit(".", 1)[-1][:5] if "." in fn else "mp4"
            items = [{"label": "Best", "ext": ext, "size": None, "url": d["url"]}]
        elif d.get("status") == "picker":
            for i, p in enumerate(d.get("picker") or [], 1):
                if isinstance(p, dict) and _safe(p.get("url")):
                    items.append({"label": f"{str(p.get('type') or 'item').title()} {i}", "ext": "", "size": None, "url": p["url"]})
        if items:
            return {"title": str(d.get("filename") or "Video")[:120], "thumb": None, "formats": items[:12]}
    return None

def _rahad_fallback(url):
    """তৃতীয় পক্ষের প্যাকেজ ব্যবহার করে চেষ্টা"""
    if not HAS_RAHAD:
        return None
    try:
        result = alldl(url)
        if result and result.get("videoUrl"):
            return {
                "title": result.get("data", {}).get("title", "Video")[:120],
                "thumb": None,
                "formats": [{"label": "Best", "ext": "mp4", "size": None, "url": result["videoUrl"]}]
            }
    except Exception as e:
        print("rahad fallback failed:", type(e).__name__, flush=True)
    return None

def extract(url):
    url = resolve(url)
    if not _sem.acquire(blocking=False):
        raise Busy()
    err = None
    
    # ধাপ ১: yt-dlp চেষ্টা
    try:
        with yt_dlp.YoutubeDL(OPTS) as y:
            res = _build(y.extract_info(url, download=False))
        if res: return res
    except Exception as e:
        err = e
        print("yt-dlp failed:", type(e).__name__, str(e)[:200], flush=True)
    finally:
        _sem.release()
    
    
    res = _cobalt(url)
    if res: return res
    
   
    res = _rahad_fallback(url)
    if res: return res
    
    raise Fail(_why(err) if err else "Couldn't find a downloadable video at this link.")
