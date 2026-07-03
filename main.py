"""Job hunter — daily pipeline.

Commands:
    python main.py run                 # full daily loop (what Railway cron runs)
    python main.py tailor <job_id>     # tailored CV bullets + cover letter
    python main.py status <job_id> applied|saved|rejected
    python main.py stats               # quick DB summary
"""
import sys

import config  # noqa: F401  (validates required env vars on import)
import db
import digest
import scorer
from fetchers import adzuna, amazon, ats, rss, prefilter


def run():
    conn = db.connect()
    db.init(conn)

    # 1. fetch everything
    jobs = adzuna.fetch() + ats.fetch_all() + amazon.fetch() + rss.fetch()
    print(f"[run] fetched {len(jobs)} total")

    # 2. cheap pre-filter (senior titles, wrong region) before spending tokens
    jobs = prefilter(jobs)
    print(f"[run] {len(jobs)} after pre-filter")

    # 3. dedupe + insert; only genuinely-new jobs move on
    new_jobs = db.upsert_jobs(conn, jobs)
    print(f"[run] {len(new_jobs)} new after dedupe")
    new_jobs = new_jobs[: config.MAX_JOBS_PER_RUN]

    # 4. AI scoring
    if new_jobs:
        db.save_scores(conn, scorer.score_jobs(new_jobs))

    # 5. digest email for everything 'new' above threshold (incl. prior failed sends)
    candidates = db.digest_candidates(conn)
    if digest.send(candidates):
        db.mark_notified(conn, [c["id"] for c in candidates])

    # 6. housekeeping
    db.mark_below_threshold(conn)
    db.expire_stale(conn)
    print("[run] done")


def stats():
    conn = db.connect()
    db.init(conn)
    with conn.cursor() as cur:
        cur.execute("SELECT status, count(*), round(avg(score)) FROM jobs GROUP BY status ORDER BY 2 DESC")
        print(f"{'status':<10} {'count':>6} {'avg score':>10}")
        for status, count, avg in cur.fetchall():
            print(f"{status:<10} {count:>6} {str(avg or '-'):>10}")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "run"
    if cmd == "run":
        run()
    elif cmd == "tailor":
        from tailor import tailor
        tailor(int(sys.argv[2]))
    elif cmd == "status":
        conn = db.connect()
        db.set_status(conn, int(sys.argv[2]), sys.argv[3])
        print(f"job {sys.argv[2]} -> {sys.argv[3]}")
    elif cmd == "stats":
        stats()
    else:
        print(__doc__)
