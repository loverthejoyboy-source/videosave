import threading, ipaddress
from urllib.parse import urlsplit
import yt_dlp
from config import EXTRACTORS, MAX_PARALLEL

_sem = threading.BoundedSemaphore(MAX_PARALLEL)
class Busy(Exception): pass
class Fail(Exception): pass

OPTS = {"quiet": True, "no_warnings": True, "skip_download": True, "noplaylist": True,
        "playlist_items": "1", "socket_timeout": 15, "extractor_retries": 1,
        "allowed_extractors": EXTRACTORS}

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

def extract(url):
    if not _sem.acquire(blocking=False):
        raise Busy()
    try:
        with yt_dlp.YoutubeDL(OPTS) as y:
            info = y.extract_info(url, download=False)
    except Exception:
        raise Fail()
    finally:
        _sem.release()
    if info and info.get("_type") == "playlist":
        info = next((e for e in info.get("entries") or [] if e), None)
    if not info:
        raise Fail()
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
    if not out: raise Fail()
    out.sort(key=lambda x: -x["h"])
    for o in out: o.pop("h")
    th = info.get("thumbnail")
    return {"title": str(info.get("title") or "Video")[:120],
            "thumb": th if _safe(th) else None, "formats": out[:6]}
