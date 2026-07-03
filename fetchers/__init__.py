"""Job fetchers. Each returns list[dict] with keys:
source, company, title, location, url, description, posted_at, raw
"""
import re

import config

_TAG = re.compile(r"<[^>]+>")


def strip_html(s: str | None) -> str:
    return _TAG.sub(" ", s or "").replace("&nbsp;", " ").replace("&amp;", "&").strip()


def prefilter(jobs: list[dict]) -> list[dict]:
    """Cheap keyword filter before spending AI tokens:
    drop obviously-senior titles and out-of-region locations."""
    out = []
    for j in jobs:
        title = (j.get("title") or "").lower()
        loc = (j.get("location") or "").lower()
        if any(k in title for k in config.SENIOR_KEYWORDS):
            continue
        # keep if location matches Ireland/remote, or location is empty (let AI judge)
        if loc and not any(k in loc for k in config.LOCATION_KEYWORDS):
            continue
        out.append(j)
    return out
