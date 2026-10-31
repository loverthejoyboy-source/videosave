import re
from urllib.parse import urlsplit
from config import PLATFORMS
_BAD = re.compile(r"[\x00-\x20\x7f\\<>\"'`{}|^]")

def check(url):
    """Return (platform, url) if valid, else None. Only https links on the allowlist.""" 
    if not isinstance(url, str) or not 12 <= len(url) <= 400 or _BAD.search(url):
        return None
    try:
        u = urlsplit(url)
        host, port = (u.hostname or "").lower(), u.port
    except ValueError:
        return None
    if u.scheme != "https" or u.username or u.password or port not in (None, 443):
        return None
    for name, doms in PLATFORMS.items():
        if any(host == d or host.endswith("." + d) for d in doms):
            return name, url
    return None
