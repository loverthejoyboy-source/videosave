import os

TERMS_VERSION = "1.1"

PLATFORMS = {
    "youtube": ["youtube.com", "youtu.be"], 
    "tiktok": ["tiktok.com"],
    "instagram": ["instagram.com"], 
    "facebook": ["facebook.com", "fb.watch"],
    "x": ["x.com", "twitter.com"], 
    "snapchat": ["snapchat.com"], 
    "vimeo": ["vimeo.com"],
    "dailymotion": ["dailymotion.com", "dai.ly"], 
    "reddit": ["reddit.com", "redd.it"],
}

SHORT_HOSTS = {"fb.watch", "redd.it", "vt.tiktok.com", "vm.tiktok.com", "bit.ly", "t.co"}

RATE_PER_MIN, RATE_PER_DAY, GLOBAL_PER_MIN, MAX_PARALLEL = 10, 150, 90, 3

TOKEN_TTL = 1800
TRUSTED_HOPS = int(os.environ.get("TRUSTED_HOPS", "1"))

# SECRET ঠিক করা হয়েছে। Render এর Environment Variables এ APP_SECRET সেট করলে ভালো, 
# না করলে কমপক্ষে একটি ফিক্সড স্ট্রিং থাকবে যাতে সার্ভার রিস্টার্টে টোকেন নষ্ট না হয়।
SECRET = os.environ.get("APP_SECRET", "super_secret_fixed_key_for_clipkeep_123!").encode()

KEEPALIVE_TOKEN = os.environ.get("KEEPALIVE_TOKEN", "keepalive_secret_123")
CONTACT_EMAIL = os.environ.get("CONTACT_EMAIL", "contact@example.com")

COBALT_API_URLS = [u.strip() for u in os.environ.get("COBALT_API_URLS", "").split(",") if u.strip().startswith("https://")]
COBALT_API_KEY = os.environ.get("COBALT_API_KEY", "")