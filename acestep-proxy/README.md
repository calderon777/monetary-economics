# ACE-Step Hosted Proxy (Beginner-Friendly)

This folder contains a small `FastAPI` service that sits between your GitHub Pages site and an `ACE-Step` server.

Why this exists:
- `GitHub Pages` can host your HTML and JavaScript, but it cannot run Python or GPU models.
- `ACE-Step` needs a backend server (usually with a GPU).
- Browsers also need `CORS` permission to call a different website/domain.

This proxy gives you:
- `CORS` for your GitHub Pages site
- a stable public `HTTPS` endpoint
- optional token auth
- basic rate limiting
- Topic 2 pilot endpoints for scoring, leaderboard, cohort summary, and community voting
- optional Google Sheets persistence (via your existing Google Apps Script web app pattern)

## Jargon (plain English)

- `Backend`: the server that does the real work (here: running ACE-Step music generation).
- `Proxy`: a middle server that forwards requests to another server.
- `API`: a URL-based interface your page calls (`/release_task`, `/query_result`).
- `CORS`: browser security rules that decide which websites are allowed to call your API.
- `Origin`: the website domain making the request (for you: `https://calderon777.github.io`).
- `HTTPS`: encrypted web traffic (`https://`), required when your page is served over HTTPS.
- `Reverse proxy`: a web server (like Nginx/Caddy) that receives public traffic and forwards it internally.
- `Rate limit`: a cap on how many requests one user/IP can make in a time window.
- `Token auth`: a shared secret string sent in a header to protect an API.

## Architecture (what talks to what)

`Student browser (GitHub Pages)` -> `Your proxy (this app)` -> `ACE-Step API` -> `Generated audio`

The browser only talks to your proxy. The proxy talks to ACE-Step.

## Quick Start (local test)

### 1. Install dependencies

```bash
cd acestep-proxy
pip install -r requirements.txt
```

### 2. Configure environment

Copy `.env.example` to `.env` and edit values.

Windows PowerShell quick test:

```powershell
$env:ACESTEP_TARGET_BASE = "http://127.0.0.1:8001"
$env:PROXY_ALLOWED_ORIGINS = "https://calderon777.github.io,http://localhost,http://127.0.0.1"
$env:TOPIC2_ENABLE_GOOGLE_SHEETS = "true"
$env:TOPIC2_GOOGLE_SHEETS_WORKBOOK = "Monetary Economics Pilot"
$env:TOPIC2_GOOGLE_SHEETS_ENDPOINT = "https://script.google.com/macros/s/YOUR_SCRIPT_ID/exec"
```

### 3. Run the proxy

```bash
uvicorn app:app --host 0.0.0.0 --port 8080
```

### 4. Check health

Open:

- `http://localhost:8080/healthz` (proxy health/config)
- `http://localhost:8080/health` (proxied ACE-Step health)
- `http://localhost:8080/topic2/leaderboard` (pilot scoring leaderboard)
- `http://localhost:8080/topic2/cohort-summary` (pilot cohort analytics snapshot)

## Connect your `topic2ludic` page

Your page already supports a configurable backend URL.

Use the page like this:

```text
https://calderon777.github.io/monetary-economics/topic2ludic.html?acestep_api=https://api.yourdomain.com
```

The page will then call:
- `https://api.yourdomain.com/release_task`
- `https://api.yourdomain.com/query_result`
- `https://api.yourdomain.com/v1/audio`
- `https://api.yourdomain.com/topic2/submit-score`
- `https://api.yourdomain.com/topic2/community-songs`
- `https://api.yourdomain.com/topic2/vote`

## Topic 2 pilot endpoints (new)

These endpoints support the `topic2ludic` economics-song pilot:

- `POST /topic2/submit-score`: save a submission + return rubric scores (5 criteria + average)
- `GET /topic2/leaderboard`: top/bottom scorers
- `GET /topic2/cohort-summary`: common misconceptions, revision types, inaccuracy patterns, AI over-reliance indicators
- `GET /topic2/community-songs`: public/published songs list for listening + voting
- `POST /topic2/vote`: vote by nickname (no self-voting)

Current persistence behavior:
- In-memory storage is always used (fast pilot mode)
- Optional Google Sheets webhook persistence can be enabled simultaneously

## Google Sheets persistence (Topic 2 pilot)

The proxy can POST rows to a Google Apps Script web app endpoint, following the same pattern used by your `topicNmcqs.qmd` pages.

Set:
- `TOPIC2_ENABLE_GOOGLE_SHEETS=true`
- `TOPIC2_GOOGLE_SHEETS_ENDPOINT=https://script.google.com/macros/s/.../exec`
- `TOPIC2_GOOGLE_SHEETS_WORKBOOK=<your label>` (optional label field stored in payload)
- `TOPIC2_GOOGLE_SHEETS_TAB=topic2ludic` (single-tab mode; recommended for pilot)

The proxy sends row-style JSON payloads with:
- `sheet=topic2ludic` (single worksheet tab)
- `kind` to distinguish row types (`topic2_submission`, `topic2_score`, `topic2_vote`, `topic2_cohort_snapshot`, etc.)

This lets you keep one worksheet tab (`topic2ludic`) while still separating event types for analysis.

Example payload fields include:
- `sheet`
- `kind`
- `submission_id`
- `nickname`
- `lyrics`
- `prompt`
- `average_score`
- `revision_type`
- `unreliable_warning`

## Deploying (recommended path)

### Option A: One GPU server (simplest to start)

Run both:
- ACE-Step API on `127.0.0.1:8001`
- this proxy on `127.0.0.1:8080`

Then use `Caddy` or `Nginx` to expose `https://api.yourdomain.com` and forward traffic to `127.0.0.1:8080`.

### Option B: Two servers (cleaner separation)

- GPU server runs ACE-Step (private network)
- small CPU server runs this proxy
- proxy forwards to the GPU server private address

## Example Caddy config (HTTPS)

```caddyfile
api.yourdomain.com {
    reverse_proxy 127.0.0.1:8080
}
```

Why `Caddy`:
- easiest automatic HTTPS certificates (Let's Encrypt)

## Security notes (important)

- Do not put a secret token directly into public GitHub Pages JavaScript. Users can see it.
- If you need strong protection, use user accounts or signed short-lived tokens from another backend.
- This proxy includes only a basic in-memory rate limit. For production, add:
  - logs
  - stronger rate limiting (Redis)
  - abuse filtering
  - queue limits

## Environment Variables

- `ACESTEP_TARGET_BASE`: where the real ACE-Step API lives
- `PROXY_ALLOWED_ORIGINS`: comma-separated browser origins allowed to call this proxy
- `PROXY_SHARED_TOKEN`: optional shared token (header: `X-Proxy-Token`)
- `PROXY_REQUIRE_TOKEN`: `true/false`
- `PROXY_REQUEST_TIMEOUT_SECONDS`: timeout for long generations
- `PROXY_RATE_LIMIT_WINDOW_SECONDS`: rate-limit window
- `PROXY_RATE_LIMIT_MAX_REQUESTS`: max requests per IP in the window
- `TOPIC2_MAX_LYRICS_WORDS`, `TOPIC2_MAX_LYRICS_CHARS`
- `TOPIC2_MAX_PROMPT_WORDS`, `TOPIC2_MAX_PROMPT_CHARS`
- `TOPIC2_MAX_SCORING_SUBMISSIONS_PER_NICK`
- `TOPIC2_ENABLE_GOOGLE_SHEETS`: enable/disable Apps Script webhook persistence
- `TOPIC2_GOOGLE_SHEETS_ENDPOINT`: Apps Script Web App URL (same style as MCQ pages)
- `TOPIC2_GOOGLE_SHEETS_WORKBOOK`: optional workbook label stored in payload rows
- `TOPIC2_GOOGLE_SHEETS_TAB`: worksheet/tab name for Topic 2 pilot rows (default `topic2ludic`)

## Docker (optional)

```bash
cd acestep-proxy
docker build -t acestep-proxy .
docker run --rm -p 8080:8080 \
  -e ACESTEP_TARGET_BASE=http://host.docker.internal:8001 \
  -e PROXY_ALLOWED_ORIGINS=https://calderon777.github.io \
  acestep-proxy
```
