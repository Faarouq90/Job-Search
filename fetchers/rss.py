"""Generic RSS/Atom job-feed fetcher. Add feeds in config.RSS_FEEDS."""
from datetime import datetime, timezone
from time import mktime

import feedparser

import config
from fetchers import strip_html


def fetch() -> list[dict]:
    jobs = []
    for name, url in config.RSS_FEEDS:
        try:
            feed = feedparser.parse(url)
            for e in feed.entries:
                posted = None
                if getattr(e, "published_parsed", None):
                    posted = datetime.fromtimestamp(mktime(e.published_parsed), tz=timezone.utc)
                jobs.append({
                    "source": f"rss:{name}",
                    "company": getattr(e, "author", None),
                    "title": getattr(e, "title", ""),
                    "location": None,  # rarely structured in RSS; AI scorer reads description
                    "url": getattr(e, "link", None),
                    "description": strip_html(getattr(e, "summary", ""))[:6000],
                    "posted_at": posted,
                    "raw": {},
                })
        except Exception as ex:
            print(f"[rss] {name}: {ex}")
    print(f"[rss] fetched {len(jobs)}")
    return jobs
