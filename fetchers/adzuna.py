"""Adzuna — free job-search API covering Ireland (aggregates major boards).
Register: https://developer.adzuna.com (free app_id + app_key).
Docs: https://developer.adzuna.com/docs/search
"""
from datetime import datetime

import requests

import config
from fetchers import strip_html

BASE = "https://api.adzuna.com/v1/api/jobs/ie/search/1"


def fetch() -> list[dict]:
    if not (config.ADZUNA_APP_ID and config.ADZUNA_APP_KEY):
        print("[adzuna] skipped — set ADZUNA_APP_ID / ADZUNA_APP_KEY")
        return []
    jobs, seen_urls = [], set()
    for query in config.ADZUNA_QUERIES:
        try:
            r = requests.get(
                BASE,
                params={
                    "app_id": config.ADZUNA_APP_ID,
                    "app_key": config.ADZUNA_APP_KEY,
                    "what": query,
                    "results_per_page": 30,
                    "max_days_old": 7,
                    "sort_by": "date",
                },
                timeout=20,
            )
            r.raise_for_status()
            for item in r.json().get("results", []):
                url = item.get("redirect_url")
                if url in seen_urls:
                    continue
                seen_urls.add(url)
                posted = None
                if item.get("created"):
                    try:
                        posted = datetime.fromisoformat(item["created"].replace("Z", "+00:00"))
                    except ValueError:
                        pass
                jobs.append({
                    "source": "adzuna",
                    "company": (item.get("company") or {}).get("display_name"),
                    "title": item.get("title", "").replace("<strong>", "").replace("</strong>", ""),
                    "location": (item.get("location") or {}).get("display_name"),
                    "url": url,
                    "description": strip_html(item.get("description")),
                    "posted_at": posted,
                    "raw": {"adzuna_id": item.get("id"), "query": query,
                            "salary_min": item.get("salary_min"), "salary_max": item.get("salary_max")},
                })
        except Exception as e:
            print(f"[adzuna] query '{query}' failed: {e}")
    print(f"[adzuna] fetched {len(jobs)}")
    return jobs
