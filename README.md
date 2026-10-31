# Clipkeep – video backup tool

Flask + yt-dlp service running on Render (Docker). It validates a link, detects the platform and returns direct download links. It never stores or proxies video files.

## Deploy on Render (free, no card)
1. Upload this folder to a public GitHub repo (keep `static/` and `.github/`).
2. Render → **New → Web Service** → pick the repo → Language **Docker** → Instance **Free**.
3. Add the environment variables below, then **Deploy web service**.

## Environment variables (Render → your service → Environment)
| Name | Required | Purpose |
|---|---|---|
| `APP_SECRET` | yes | Signs session tokens (long random text) |
| `KEEPALIVE_TOKEN` | optional | Secret for the `/api/keepalive` ping |
| `CONTACT_EMAIL` | recommended | Shown in the Terms for DMCA notices. No code edit needed |
| `COBALT_API_URLS` | optional | Your own Cobalt instance(s), comma-separated https URLs, used as a fallback |
| `COBALT_API_KEY` | optional | Only if your Cobalt instance requires a key |
| `TRUSTED_HOPS` | optional | Number of trusted proxies for IP detection (default 1) |

## Supported links
Single public videos from YouTube, TikTok, Instagram, Facebook, X, Snapchat (Spotlight), Vimeo, Dailymotion and Reddit. To add a site, add its domain to `PLATFORMS` and its extractor name to `EXTRACTORS` in `config.py`. Profiles, playlists and bulk downloads are intentionally not supported.

## Why a link may fail
Free cloud servers share IP ranges that platforms often block (YouTube, Instagram and Facebook most of all). The site then shows a specific message such as "The platform is blocking our free server right now". Server logs (Render → **Logs**) show the underlying yt-dlp error. Private, age-restricted or login-only videos cannot be fetched.

## Optional fallback: your own Cobalt instance
1. Render → **New → Web Service → Existing Image** → `ghcr.io/imputnet/cobalt:11`, Free instance.
2. Add env var `API_URL` = the public URL of that service (with trailing `/`).
3. In your Clipkeep service set `COBALT_API_URLS` to the same URL. More fallbacks: add more URLs separated by commas.
Notes: two always-on free services exceed Render's 750 free hours per month, and Cobalt runs on the same kind of server IPs, so it may be blocked too.

## Update the site
Upload changed files to GitHub (**Add file → Upload files**). Render redeploys automatically. Hard-refresh with Ctrl+Shift+R.

## Keep-alive (free instances sleep after 15 minutes idle)
Keep `.github/workflows/keepalive.yml`, then in GitHub **Settings → Secrets and variables → Actions** add `SPACE_URL` (site URL, no trailing `/`) and `KEEPALIVE_TOKEN` (same as on Render). The endpoint returns 404 without the token. GitHub schedules can be delayed and are disabled after 60 days of repo inactivity.

## Maintenance
Monthly: Render → **Manual Deploy → Clear build cache & deploy** to update yt-dlp.

## Files
`config.py` settings · `validator.py` URL checks · `security.py` rate limit, bot checks, tokens, headers · `media.py` yt-dlp and Cobalt · `routes.py` API · `app.py` entry point · `static/` UI

Fonts: Unbounded and DM Mono (SIL Open Font License), self-hosted.
