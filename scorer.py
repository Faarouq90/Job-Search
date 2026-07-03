"""AI scoring: batches of jobs -> Claude -> {score 0-100, seniority, reason}.
Senior roles get seniority='senior' and score 0 regardless of skills match.
"""
import json

import anthropic

import config

SYSTEM = f"""You score job postings for a specific candidate. Be honest and calibrated —
most jobs should score 30-70; reserve 85+ for near-perfect fits.

CANDIDATE PROFILE:
{config.CANDIDATE_PROFILE}

SCORING RULES:
- seniority: one of "intern", "graduate", "junior", "mid", "senior".
  If the role requires 3+ years professional experience, or the title/description
  implies senior/staff/lead/manager, set seniority to "mid" or "senior" and score <= 15.
- score 0-100 = probability-weighted fit: skills overlap, level match, location
  (Dublin/Ireland/remote-from-Ireland strongly preferred), visa friendliness
  (large multinationals and companies stating visa support score higher; the
  candidate is on Stamp 1G graduate permission).
- reason: ONE punchy sentence (max 25 words) explaining the score. Mention the
  single biggest plus and biggest minus.

OUTPUT: respond with ONLY a JSON array, no markdown fences, no prose:
[{{"index": 0, "score": 72, "seniority": "graduate", "reason": "..."}}, ...]
One object per input job, matching the given index."""

client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)


def _score_batch(batch: list[dict]) -> list[dict]:
    payload = [
        {
            "index": i,
            "title": j.get("title"),
            "company": j.get("company"),
            "location": j.get("location"),
            "description": (j.get("description") or "")[:2500],
        }
        for i, j in enumerate(batch)
    ]
    msg = client.messages.create(
        model=config.ANTHROPIC_MODEL,
        max_tokens=1500,
        system=SYSTEM,
        messages=[{"role": "user", "content": json.dumps(payload, ensure_ascii=False)}],
    )
    text = "".join(b.text for b in msg.content if b.type == "text").strip()
    if text.startswith("```"):
        text = text.strip("`").removeprefix("json").strip()
    results = json.loads(text)

    scored = []
    for r in results:
        try:
            j = batch[int(r["index"])]
        except (KeyError, IndexError, ValueError):
            continue
        scored.append({
            "id": j["id"],
            "score": max(0, min(100, int(r.get("score", 0)))),
            "seniority": str(r.get("seniority", "unknown"))[:20],
            "reason": str(r.get("reason", ""))[:400],
        })
    return scored


def score_jobs(jobs: list[dict]) -> list[dict]:
    scored = []
    for i in range(0, len(jobs), config.SCORE_BATCH_SIZE):
        batch = jobs[i:i + config.SCORE_BATCH_SIZE]
        try:
            scored.extend(_score_batch(batch))
        except Exception as e:
            print(f"[scorer] batch {i // config.SCORE_BATCH_SIZE} failed: {e}")
    print(f"[scorer] scored {len(scored)}/{len(jobs)}")
    return scored
