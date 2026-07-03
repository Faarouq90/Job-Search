"""Daily HTML email digest via SMTP (Gmail App Password)."""
import smtplib
from datetime import date
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import config


def _tier(score: int) -> tuple[str, str]:
    if score >= 80:
        return "#1a7f37", "STRONG MATCH"
    if score >= 65:
        return "#9a6700", "GOOD MATCH"
    return "#57606a", "WORTH A LOOK"


def build_html(jobs: list[dict]) -> str:
    rows = []
    for j in jobs:
        color, label = _tier(j["score"])
        rows.append(f"""
        <tr>
          <td style="padding:14px 16px;border-bottom:1px solid #e5e7eb;">
            <div style="font-size:12px;font-weight:700;color:{color};letter-spacing:.5px;">
              {j['score']}% &middot; {label}
            </div>
            <div style="font-size:16px;font-weight:600;margin:4px 0 2px;">
              <a href="{j['url']}" style="color:#0969da;text-decoration:none;">{j['title']}</a>
            </div>
            <div style="font-size:13px;color:#57606a;">
              {j.get('company') or '—'} &middot; {j.get('location') or 'location n/a'} &middot; via {j['source']}
            </div>
            <div style="font-size:13px;color:#24292f;margin-top:6px;">{j.get('score_reason') or ''}</div>
            <div style="font-size:11px;color:#8b949e;margin-top:4px;">job id: {j['id']}
              &nbsp;&middot;&nbsp; tailor CV: <code>python main.py tailor {j['id']}</code></div>
          </td>
        </tr>""")
    return f"""
    <html><body style="font-family:-apple-system,Segoe UI,Arial,sans-serif;background:#f6f8fa;margin:0;padding:24px;">
      <table style="max-width:640px;margin:auto;background:#fff;border-radius:8px;border:1px solid #e5e7eb;width:100%;border-collapse:collapse;">
        <tr><td style="padding:20px 16px;border-bottom:2px solid #24292f;">
          <div style="font-size:20px;font-weight:700;">Job Digest — {date.today():%A %d %b %Y}</div>
          <div style="font-size:13px;color:#57606a;margin-top:4px;">{len(jobs)} new matches ≥ {config.MIN_DIGEST_SCORE}% fit</div>
        </td></tr>
        {''.join(rows)}
      </table>
    </body></html>"""


def send(jobs: list[dict]) -> bool:
    if not (config.SMTP_USER and config.SMTP_PASS):
        print("[digest] skipped — set SMTP_USER / SMTP_PASS")
        return False
    if not jobs:
        print("[digest] no jobs above threshold; no email sent")
        return False

    msg = MIMEMultipart("alternative")
    top = jobs[0]
    msg["Subject"] = f"🎯 {len(jobs)} job matches — top: {top['title']} ({top['score']}%)"
    msg["From"] = config.SMTP_USER
    msg["To"] = config.DIGEST_TO
    msg.attach(MIMEText(build_html(jobs), "html"))

    with smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT) as s:
        s.starttls()
        s.login(config.SMTP_USER, config.SMTP_PASS)
        s.sendmail(config.SMTP_USER, [config.DIGEST_TO], msg.as_string())
    print(f"[digest] sent {len(jobs)} jobs to {config.DIGEST_TO}")
    return True
