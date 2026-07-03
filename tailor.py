"""On-demand CV tailoring + cover letter for one job:
    python main.py tailor <job_id>
Writes tailored_<id>_<company>.md — bullet rewrites, keyword map, cover letter.
"""
import re

import anthropic

import config
import db

PROMPT = """You are tailoring application materials for this candidate:

{profile}

TARGET JOB:
Title: {title}
Company: {company}
Location: {location}
Description:
{description}

Produce a markdown document with exactly these sections:

# Tailored Application — {title} @ {company}

## 1. Fit Summary
3-4 honest sentences: why this candidate fits, and the one gap to pre-empt.

## 2. Keyword Map
Table: job-description keyword -> where it maps in the candidate's projects/skills.
Only real mappings; flag missing keywords in a short list after the table.

## 3. Rewritten CV Bullets
For the 2 most relevant projects and the professional summary, rewrite bullets
to mirror the job's language. Keep every claim truthful to the profile.

## 4. Cover Letter
280-340 words, direct tone, no clichés ("I am writing to express..." banned).
Address the top 2 job requirements with concrete project evidence. Mention
Stamp 1G graduate work permission only if the company is small; for large
multinationals omit visa talk entirely.
"""

client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)


def tailor(job_id: int):
    conn = db.connect()
    job = db.get_job(conn, job_id)
    if not job:
        raise SystemExit(f"No job with id {job_id}")

    msg = client.messages.create(
        model=config.ANTHROPIC_MODEL,
        max_tokens=2500,
        messages=[{
            "role": "user",
            "content": PROMPT.format(
                profile=config.CANDIDATE_PROFILE,
                title=job["title"],
                company=job.get("company") or "the company",
                location=job.get("location") or "",
                description=(job.get("description") or "")[:5000],
            ),
        }],
    )
    text = "".join(b.text for b in msg.content if b.type == "text")

    safe_company = re.sub(r"[^a-zA-Z0-9]+", "_", (job.get("company") or "company"))[:30]
    path = f"tailored_{job_id}_{safe_company}.md"
    with open(path, "w") as f:
        f.write(text)
    db.set_status(conn, job_id, "saved")
    print(f"[tailor] wrote {path} (job marked 'saved')")
