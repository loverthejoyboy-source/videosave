# ভিডিও ব্যাকআপ টুল — Render-এ সেটআপ

১. GitHub-এ রিপো বানিয়ে সব ফাইল আপলোড · ২. render.com-এ Web Service (Docker, Free) · ৩. Environment Variables: `APP_SECRET`, `KEEPALIVE_TOKEN` (দুটোই ৪০+ অক্ষরের র‍্যান্ডম লেখা)।
সাইটের লিংক হবে `https://নাম.onrender.com`।

ফাইল: `config.py` সেটিংস · `validator.py` লিংক যাচাই · `security.py` রেট-লিমিট/বট/টোকেন/হেডার · `extractor.py` yt-dlp · `routes.py` API · `app.py` শুরু।
মাসে একবার Render-এ Manual Deploy → "Clear build cache & deploy" দিন (yt-dlp আপডেটের জন্য)।
`static/index.html`-এ `contact@example.com` বদলে নিজের ইমেইল দিন।
