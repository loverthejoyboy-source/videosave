# Clipkeep – video backup tool

A small Flask + yt-dlp service. It validates a link, detects the platform and returns direct download links. It never stores or proxies video files.

## Deploy on Render (free, no card)
1. Create a **public GitHub repo** and upload everything in this folder (keep the `static` folder and `.github` folder).
2. On render.com sign in with GitHub, then **New → Web Service**, pick the repo.
3. Language **Docker**, Branch `main`, Instance Type **Free**.
4. Add environment variables (use the **Generate** button): `APP_SECRET` and `KEEPALIVE_TOKEN`.
5. **Deploy web service**. Your site will be at `https://<name>.onrender.com`.

## Update the site later
Upload changed files to GitHub (**Add file → Upload files**, same names overwrite). Render auto-deploys within a couple of minutes. Hard-refresh the page (Ctrl+Shift+R).

## Replace the contact email
Edit `static/index.html` and replace `contact@example.com` with your real address (used for DMCA notices).

## Optional: keep-alive (every 10 minutes)
Render free services sleep after 15 minutes idle.
1. Keep `.github/workflows/keepalive.yml` in the repo.
2. GitHub repo **Settings → Secrets and variables → Actions**, add `SPACE_URL` (your site URL, no trailing `/`) and `KEEPALIVE_TOKEN` (same value as on Render).
3. **Actions** tab → enable workflows → run **keepalive** once.
Without the secret token the endpoint returns 404. GitHub schedules can be delayed, and it disables them after 60 days of repo inactivity.

## Maintenance
Once a month: Render → **Manual Deploy → Clear build cache & deploy** (updates yt-dlp).

## Limits
- Free cloud IPs are sometimes blocked by YouTube/Instagram; the site then shows an error.
- Only combined audio+video formats are listed. The link opens in a new tab (browsers ignore `download` on cross-origin files).
- Render free: 750 instance hours/month, 5 GB bandwidth.

## Files
`config.py` settings · `validator.py` URL checks · `security.py` rate limit, bot checks, tokens, headers · `extractor.py` yt-dlp · `routes.py` API · `app.py` entry point · `static/` UI

## Fonts
Unbounded and DM Mono (SIL Open Font License), self-hosted from `static/fonts/`.
