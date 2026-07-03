"""Amazon — unofficial amazon.jobs JSON search API (no auth required).
Amazon isn't on Greenhouse/Lever/Ashby; this queries their own careers site,
filtered to Ireland, newest first. Unofficial endpoint — if Amazon changes it,
this fails gracefully with a log line like the other fetchers.
"""
from datetime import datetime, timezone

import requests

from fetchers import strip_html

BASE = "https://www.amazon.jobs/en/search.json"
PAGE_SIZE = 100
MAX_PAGES = 3  # 300 jobs max; Ireland currently lists ~180 total


def _parse_date(s: str | None):
    if not s:
        return None
    try:  # format: "July 3, 2026" (sometimes with doubled spaces)
        return datetime.strptime(" ".join(s.split()), "%B %d, %Y").replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def fetch() -> list[dict]:
    jobs = []
    for page in range(MAX_PAGES):
        try:
            r = requests.get(
                BASE,
                params={
                    "normalized_country_code[]": "IRL",
                    "result_limit": PAGE_SIZE,
                    "offset": page * PAGE_SIZE,
                    "sort": "recent",
                },
                headers={"User-Agent": "Mozilla/5.0 (jobhunter/1.0)"},
                timeout=20,
            )
            r.raise_for_status()
            batch = r.json().get("jobs", [])
        except Exception as e:
            print(f"[amazon] page {page} failed: {e}")
            break
        for j in batch:
            desc = " ".join(filter(None, [
                j.get("description_short") or j.get("description"),
                j.get("basic_qualifications"),
            ]))
            jobs.append({
                "source": "amazon.jobs",
                "company": "Amazon",
                "title": j.get("title", ""),
                "location": j.get("location"),  # e.g. "IE, D, Dublin" / "IE, CO, Cork"
                "url": "https://www.amazon.jobs" + (j.get("job_path") or ""),
                "description": strip_html(desc)[:6000],
                "posted_at": _parse_date(j.get("posted_date")),
                "raw": {"amazon_id": j.get("id_icims") or j.get("id")},
            })
        if len(batch) < PAGE_SIZE:
            break
    print(f"[amazon] fetched {len(jobs)}")
    return jobs
