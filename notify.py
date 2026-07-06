"""Telegram notifications — one summary message per run via the Bot API."""
import html

import requests

import config

MAX_MESSAGE_LEN = 4096  # Telegram sendMessage hard limit


def _send(text: str) -> bool:
    if not (config.TELEGRAM_BOT_TOKEN and config.TELEGRAM_CHAT_ID):
        print("[notify] skipped — set TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID")
        return False
    try:
        resp = requests.post(
            f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/sendMessage",
            json={"chat_id": config.TELEGRAM_CHAT_ID, "text": text, "parse_mode": "HTML"},
            timeout=15,
        )
        if resp.status_code != 200:
            print(f"[notify] warning: Telegram API returned {resp.status_code}: {resp.text[:200]}")
            return False
    except requests.RequestException as e:
        print(f"[notify] warning: Telegram send failed: {e}")
        return False
    return True


def send_telegram(jobs: list[dict]) -> bool:
    """Send one summary message: total count + top 5 jobs by score. Never raises."""
    if not jobs:
        print("[notify] no jobs above threshold; no Telegram message sent")
        return False

    top = sorted(jobs, key=lambda j: j["score"], reverse=True)[:5]
    parts = [f"🎯 <b>{len(jobs)} new job matches</b>"]
    for j in top:
        block = (
            f"\n<b>{j['score']}%</b> — {html.escape(j['title'])}\n"
            f"{html.escape(j.get('company') or '—')}\n"
            f"<code>python main.py tailor {j['id']}</code>"
        )
        # stay under the limit without truncating mid-tag
        if len("\n".join(parts + [block])) > MAX_MESSAGE_LEN:
            break
        parts.append(block)

    if _send("\n".join(parts)):
        print(f"[notify] sent Telegram summary ({len(jobs)} jobs)")
        return True
    return False


def send_test() -> bool:
    return _send("Telegram notifications working ✅")
