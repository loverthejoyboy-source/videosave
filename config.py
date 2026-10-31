import os
TERMS_VERSION = "1.0"
PLATFORMS = {
    "youtube": ["youtube.com", "youtu.be"], "tiktok": ["tiktok.com"],
    "instagram": ["instagram.com"], "facebook": ["facebook.com", "fb.watch"],
    "x": ["x.com", "twitter.com"], "vimeo": ["vimeo.com"],
    "dailymotion": ["dailymotion.com", "dai.ly"], "reddit": ["reddit.com", "redd.it"],
}
EXTRACTORS = ["(?i)^youtube", "(?i)^tiktok", "(?i)^instagram", "(?i)^facebook",
              "(?i)^twitter", "(?i)^vimeo", "(?i)^dailymotion", "(?i)^reddit"]
RATE_PER_MIN, RATE_PER_DAY, GLOBAL_PER_MIN, MAX_PARALLEL = 10, 150, 90, 3
TOKEN_TTL = 1800
TRUSTED_HOPS = int(os.environ.get("TRUSTED_HOPS", "1"))  # প্রক্সির সংখ্যা
SECRET = (os.environ.get("APP_SECRET") or os.urandom(32).hex()).encode()
KEEPALIVE_TOKEN = os.environ.get("KEEPALIVE_TOKEN", "")
