"""Greenhouse / Lever / Ashby public job-board APIs (no auth required).
Unknown board tokens 404 and are skipped gracefully.
"""
from datetime import datetime, timezone

import requests

import config
from fetchers import strip_html

TIMEOUT = 20


def _get(url, **kw):
    r = requests.get(url, timeout=TIMEOUT, headers={"User-Agent": "jobhunter/1.0"}, **kw)
    r.raise_for_status()
    return r.json()


# ------------------------------------------------------------------ greenhouse
def fetch_greenhouse() -> list[dict]:
    jobs = []
    for board in config.GREENHOUSE_BOARDS:
        try:
            data = _get(f"https://boards-api.greenhouse.io/v1/boards/{board}/jobs",
                        params={"content": "true"})
            for j in data.get("jobs", []):
                posted = None
                if j.get("updated_at"):
                    try:
                        posted = datetime.fromisoformat(j["updated_at"].replace("Z", "+00:00"))
                    except ValueError:
                        pass
                jobs.append({
                    "source": f"greenhouse:{board}",
                    "company": board,
                    "title": j.get("title", ""),
                    "location": (j.get("location") or {}).get("name"),
                    "url": j.get("absolute_url"),
                    "description": strip_html(j.get("content"))[:6000],
                    "posted_at": posted,
                    "raw": {"gh_id": j.get("id")},
                })
        except Exception as e:
            print(f"[greenhouse] {board}: {e}")
    print(f"[greenhouse] fetched {len(jobs)}")
    return jobs


# ----------------------------------------------------------------------- lever
def fetch_lever() -> list[dict]:
    jobs = []
    for board in config.LEVER_BOARDS:
        try:
            data = _get(f"https://api.lever.co/v0/postings/{board}", params={"mode": "json"})
            for j in data:
                posted = None
                if j.get("createdAt"):
                    posted = datetime.fromtimestamp(j["createdAt"] / 1000, tz=timezone.utc)
                jobs.append({
                    "source": f"lever:{board}",
                    "company": board,
                    "title": j.get("text", ""),
                    "location": (j.get("categories") or {}).get("location"),
                    "url": j.get("hostedUrl"),
                    "description": strip_html(j.get("descriptionPlain") or j.get("description"))[:6000],
                    "posted_at": posted,
                    "raw": {"lever_id": j.get("id")},
                })
        except Exception as e:
            print(f"[lever] {board}: {e}")
    print(f"[lever] fetched {len(jobs)}")
    return jobs


# ----------------------------------------------------------------------- ashby
def fetch_ashby() -> list[dict]:
    jobs = []
    for board in config.ASHBY_BOARDS:
        try:
            data = _get(f"https://api.ashbyhq.com/posting-api/job-board/{board}",
                        params={"includeCompensation": "true"})
            for j in data.get("jobs", []):
                jobs.append({
                    "source": f"ashby:{board}",
                    "company": board,
                    "title": j.get("title", ""),
                    "location": j.get("location"),
                    "url": j.get("jobUrl") or j.get("applyUrl"),
                    "description": strip_html(j.get("descriptionPlain") or "")[:6000],
                    "posted_at": None,
                    "raw": {"ashby_id": j.get("id")},
                })
        except Exception as e:
            print(f"[ashby] {board}: {e}")
    print(f"[ashby] fetched {len(jobs)}")
    return jobs


def fetch_all() -> list[dict]:
    return fetch_greenhouse() + fetch_lever() + fetch_ashby()
