"""PostgreSQL layer. One table, explicit status lifecycle:
new -> notified -> (saved | applied | rejected) ; anything stale -> expired
"""
import hashlib
import json
import re

import psycopg2
import psycopg2.extras

import config

SCHEMA = """
CREATE TABLE IF NOT EXISTS jobs (
    id          SERIAL PRIMARY KEY,
    dedupe_key  TEXT UNIQUE NOT NULL,
    source      TEXT NOT NULL,
    company     TEXT,
    title       TEXT NOT NULL,
    location    TEXT,
    url         TEXT,
    description TEXT,
    posted_at   TIMESTAMPTZ,
    first_seen  TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_seen   TIMESTAMPTZ NOT NULL DEFAULT now(),
    score       INTEGER,
    score_reason TEXT,
    seniority   TEXT,
    status      TEXT NOT NULL DEFAULT 'new',
    raw         JSONB
);
CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);
CREATE INDEX IF NOT EXISTS idx_jobs_score  ON jobs(score);
"""

_WS = re.compile(r"\s+")


def _norm(s: str | None) -> str:
    return _WS.sub(" ", (s or "").lower().strip())


def dedupe_key(company: str | None, title: str | None) -> str:
    """Same company + same title == same job, regardless of which board listed it."""
    return hashlib.sha256(f"{_norm(company)}|{_norm(title)}".encode()).hexdigest()[:32]


def connect():
    conn = psycopg2.connect(config.DATABASE_URL)
    conn.autocommit = True
    return conn


def init(conn):
    with conn.cursor() as cur:
        cur.execute(SCHEMA)


def upsert_jobs(conn, jobs: list[dict]) -> list[dict]:
    """Insert jobs; return only the genuinely-new ones (need scoring).
    Existing jobs get last_seen refreshed so they don't expire."""
    new = []
    with conn.cursor() as cur:
        for j in jobs:
            key = dedupe_key(j.get("company"), j.get("title"))
            cur.execute(
                """
                INSERT INTO jobs (dedupe_key, source, company, title, location,
                                  url, description, posted_at, raw)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (dedupe_key)
                DO UPDATE SET last_seen = now()
                RETURNING id, (xmax = 0) AS inserted
                """,
                (
                    key, j["source"], j.get("company"), j["title"],
                    j.get("location"), j.get("url"),
                    (j.get("description") or "")[:6000],
                    j.get("posted_at"),
                    json.dumps(j.get("raw") or {}, default=str),
                ),
            )
            row = cur.fetchone()
            if row and row[1]:
                j["id"] = row[0]
                new.append(j)
    return new


def save_scores(conn, scored: list[dict]):
    with conn.cursor() as cur:
        for s in scored:
            cur.execute(
                "UPDATE jobs SET score=%s, score_reason=%s, seniority=%s WHERE id=%s",
                (s["score"], s["reason"], s.get("seniority", "unknown"), s["id"]),
            )


def unscored_jobs(conn, limit: int) -> list[dict]:
    """'new' jobs awaiting a score, freshest first (backlog drains over runs)."""
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(
            """
            SELECT id, title, company, location, description
            FROM jobs
            WHERE status = 'new' AND score IS NULL
            ORDER BY first_seen DESC
            LIMIT %s
            """,
            (limit,),
        )
        return cur.fetchall()


def digest_candidates(conn):
    """New, scored jobs above threshold, best first."""
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(
            """
            SELECT id, company, title, location, url, score, score_reason, source
            FROM jobs
            WHERE status = 'new' AND score >= %s
            ORDER BY score DESC
            LIMIT 40
            """,
            (config.MIN_DIGEST_SCORE,),
        )
        return cur.fetchall()


def mark_notified(conn, ids: list[int]):
    if not ids:
        return
    with conn.cursor() as cur:
        cur.execute("UPDATE jobs SET status='notified' WHERE id = ANY(%s)", (ids,))


def mark_below_threshold(conn):
    """Low scorers skip the digest but leave the 'new' queue."""
    with conn.cursor() as cur:
        cur.execute(
            "UPDATE jobs SET status='rejected' WHERE status='new' AND score IS NOT NULL AND score < %s",
            (config.MIN_DIGEST_SCORE,),
        )


def expire_stale(conn):
    with conn.cursor() as cur:
        cur.execute(
            """
            UPDATE jobs SET status='expired'
            WHERE status IN ('new','notified')
              AND last_seen < now() - INTERVAL '%s days'
            """ % config.JOB_EXPIRY_DAYS
        )


def set_status(conn, job_id: int, status: str):
    assert status in ("new", "notified", "saved", "applied", "rejected", "expired")
    with conn.cursor() as cur:
        cur.execute("UPDATE jobs SET status=%s WHERE id=%s", (status, job_id))


def get_job(conn, job_id: int):
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute("SELECT * FROM jobs WHERE id=%s", (job_id,))
        return cur.fetchone()
