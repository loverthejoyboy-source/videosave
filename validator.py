from urllib.parse import urlsplit

def check(url):
    if not isinstance(url, str) or not url.strip():
        return None
    url = url.strip()
    
    try:
        s = urlsplit(url)
        if s.scheme != "https" and s.scheme != "http":
            return None
        if not s.hostname:
            return None
        
        host = s.hostname.lower()
        
        # Direct Video Links
        if url.lower().split('?')[0].endswith(('.mp4', '.webm', '.m3u8', '.mkv')):
            return ("direct", url)
        
        # Supported Platforms
        if "snapchat.com" in host: return ("snapchat", url)
        if "youtube.com" in host or "youtu.be" in host: return ("youtube", url)
        if "instagram.com" in host: return ("instagram", url)
        if "tiktok.com" in host: return ("tiktok", url)
        if "facebook.com" in host or "fb.watch" in host: return ("facebook", url)
        if "twitter.com" in host or "x.com" in host: return ("x", url)
        
        # Any other generic site
        return ("generic", url)
        
    except Exception:
        return None
