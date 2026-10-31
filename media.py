import json, ipaddress, threading, urllib.request, urllib.error, re, requests, os
from urllib.parse import urlsplit, urljoin
import yt_dlp
from bs4 import BeautifulSoup
import config as C
from validator import check

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
    "ignoreerrors": True,
    "format": "best[ext=mp4]/best",
    "http_headers": {
        "User-Agent": UA,
        "Accept-Language": "en-US,en;q=0.9"
    },
    "extractor_args": {
        "youtube": {
            "player_client": ["android", "web_safari"]
        }
    }
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
        return "The platform is blocking our free server right now. Try again later or use another link."
    if any(x in m for x in ("login", "log in", "cookies", "private", "age-restricted", "authenticat")):
        return "This video needs a login, is private, or is age-restricted."
    return "Couldn't find a direct video link. Try another link."

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

def _cobalt_api(url):
    apis = [
        "https://api.cobalt.tools/api/json",
        "https://co.wuk.sh/api/json"
    ]
    for api in apis:
        try:
            req = urllib.request.Request(api, data=json.dumps({"url": url}).encode(), headers={
                "Accept": "application/json",
                "Content-Type": "application/json",
                "User-Agent": UA
            }, method="POST")
            with urllib.request.urlopen(req, timeout=15) as r:
                d = json.loads(r.read(200000))
                
            if d.get("status") in ("tunnel", "redirect") and _safe(d.get("url")):
                return {
                    "title": "Video",
                    "thumb": None,
                    "formats": [{"label": "Best", "ext": "mp4", "size": None, "url": d["url"]}]
                }
            elif d.get("status") == "picker":
                items = []
                for i, p in enumerate(d.get("picker") or [], 1):
                    if isinstance(p, dict) and _safe(p.get("url")):
                        items.append({"label": f"Video {i}", "ext": "mp4", "size": None, "url": p["url"]})
                if items:
                    return {"title": "Video", "thumb": None, "formats": items}
        except Exception as e:
            print(f"Cobalt API failed: {type(e).__name__}", flush=True)
            continue
    return None

def _snapchat_extract(url):
    match = re.search(r'snapchat\.com/(?:add/|@)([a-zA-Z0-9._-]+)', url)
    if not match:
        return None
    username = match.group(1)
    APIFY_TOKEN = os.environ.get("APIFY_TOKEN", "")
    
    if not APIFY_TOKEN:
        print("Apify token not configured.", flush=True)
        return None
    
    try:
        actor_id = "maximedupre~snapchat-story-viewer"
        run_url = f"https://api.apify.com/v2/acts/{actor_id}/run-sync-get-dataset-items?token={APIFY_TOKEN}"
        resp = requests.post(run_url, json={"profiles": [f"@{username}"], "maxItems": 20}, timeout=60)
        
        if resp.status_code != 200:
            return None
        
        data = resp.json()
        if not data: return None
        
        formats = []
        title = username
        thumb = None
        
        for item in data:
            if item.get("profile", {}).get("displayName"):
                title = item["profile"]["displayName"]
            if item.get("profile", {}).get("avatarUrl"):
                thumb = item["profile"]["avatarUrl"]
            
            for snap in item.get("snaps", []):
                media_url = snap.get("mediaUrl")
                if media_url and _safe(media_url):
                    media_type = snap.get("mediaType", "video")
                    ext = "mp4" if media_type == "video" else "jpg"
                    formats.append({"label": f"{media_type.title()} {len(formats)+1}", "ext": ext, "size": None, "url": media_url})
        
        if formats:
            return {"title": title, "thumb": thumb, "formats": formats[:12]}
    except Exception:
        pass
    return None

def _scrape_html(url):
    req = urllib.request.Request(url, headers={
        "User-Agent": UA,
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": url
    })
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            html = r.read(2000000).decode('utf-8', errors='ignore')
            
            matches = re.findall(r'https?://[^\s"\'<>]+\.(?:mp4|m3u8|webm)[^\s"\'<>]*', html)
            if matches:
                video_url = matches[0].replace('\\/', '/')
                ext = "m3u8" if ".m3u8" in video_url else ("webm" if ".webm" in video_url else "mp4")
                title = "Video"
                t_match = re.search(r'<title>(.*?)</title>', html, re.IGNORECASE)
                if t_match: title = t_match.group(1).strip()[:120]
                return {"title": title, "thumb": None, "formats": [{"label": "Best Available", "ext": ext, "size": None, "url": video_url}]}
            
            soup = BeautifulSoup(html, 'html.parser')
            for tag in soup.find_all(['video', 'source']):
                src = tag.get('src')
                if src and src.startswith('http'):
                    ext = "mp4" if ".mp4" in src else "m3u8"
                    return {"title": soup.title.string if soup.title else "Video", "thumb": None, "formats": [{"label": "Video", "ext": ext, "size": None, "url": src}]}
    except Exception as e:
        print("Scrape failed:", type(e).__name__, str(e)[:200], flush=True)
    return None

def extract(url):
    url = resolve(url)
    
    if "snapchat.com" in url and ("/add/" in url or "/@" in url):
        res = _snapchat_extract(url)
        if res: return res
    
    if url.lower().split('?')[0].endswith(('.mp4', '.webm', '.m3u8', '.mkv')):
        ext = url.split('?')[0].rsplit('.', 1)[-1]
        return {"title": "Direct Video", "thumb": None, "formats": [{"label": "Direct", "ext": ext, "size": None, "url": url}]}

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
        
    res = _cobalt_api(url)
    if res: return res
        
    res = _scrape_html(url)
    if res: return res
        
    raise Fail(_why(err) if err else "Couldn't find a downloadable video.")
