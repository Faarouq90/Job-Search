# Job Hunter — automated daily graduate job search

Fetches jobs (Adzuna + Greenhouse/Lever/Ashby + RSS) → filters seniors/wrong region →
dedupes into PostgreSQL → scores fit 0–100 with Claude → emails you a daily digest.

## Pipeline
```
fetch → prefilter (free) → dedupe (Postgres) → AI score (Claude) → email digest → housekeeping
```
Job lifecycle: `new → notified → saved / applied / rejected`, stale listings → `expired`.

## Setup (≈15 minutes)

### 1. Adzuna key (free)
Register at https://developer.adzuna.com → copy `app_id` and `app_key`.

### 2. Gmail App Password
Google Account → Security → 2-Step Verification on → https://myaccount.google.com/apppasswords
→ create one for "Mail" → 16-char password goes in `SMTP_PASS`.

### 3. Railway
1. Push this folder to a GitHub repo, then Railway → **New Project → Deploy from GitHub**.
2. Attach your existing PostgreSQL: in the service's Variables, add a reference to
   `${{Postgres.DATABASE_URL}}` as `DATABASE_URL`.
3. Add the rest of the variables from `.env.example`.
4. `railway.json` already sets the cron: **07:30 UTC daily** (`30 7 * * *`), runs
   `python main.py run` and exits. Change the schedule in that file if you want.

First run creates the table automatically. Expect the first digest to be big
(everything is "new"); it settles to a handful of jobs per day after that.

## Commands
```
python main.py run                    # full daily loop
python main.py stats                  # counts by status
python main.py status 123 applied     # track your applications
python main.py tailor 123             # tailored CV bullets + cover letter -> .md
```
Job IDs are printed in every digest email.

## Tuning (config.py)
- `ADZUNA_QUERIES` — search terms (12 included; each costs 1 API call/day)
- `GREENHOUSE_BOARDS / LEVER_BOARDS / ASHBY_BOARDS` — company ATS tokens.
  Find a company's token in its careers-page URL (e.g. `boards.greenhouse.io/stripe`
  → token `stripe`). Wrong tokens are skipped harmlessly — verify and extend the
  starter list.
- `MIN_DIGEST_SCORE` — digest threshold (default 55)
- `SENIOR_KEYWORDS / LOCATION_KEYWORDS` — the free pre-filter
- `CANDIDATE_PROFILE` — keep this updated (e.g. when Security+ completes)

## Cost
~50–80 new jobs/day, batched 8 per call ⇒ roughly **$5–9/month** on Sonnet 4.6.
Set `ANTHROPIC_MODEL=claude-haiku-4-5` to cut that ~70% with minor quality loss.
