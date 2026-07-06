"""Central configuration. Everything tunable lives here or in env vars."""
import os

# Load a local .env for development, if present. On Railway (and any other
# host that injects real env vars) there is no .env, so this is a harmless
# no-op — real environment variables always win.
try:
    from dotenv import load_dotenv
    load_dotenv()
except ModuleNotFoundError:
    pass

# ---------------------------------------------------------------- env helpers
def env(key: str, default: str | None = None, required: bool = False) -> str | None:
    val = os.environ.get(key, default)
    if required and not val:
        raise SystemExit(f"Missing required env var: {key}")
    return val

# ------------------------------------------------------------------- secrets
DATABASE_URL      = env("DATABASE_URL", required=True)
ANTHROPIC_API_KEY = env("ANTHROPIC_API_KEY", required=True)
ANTHROPIC_MODEL   = env("ANTHROPIC_MODEL", "claude-sonnet-4-6")

ADZUNA_APP_ID  = env("ADZUNA_APP_ID")   # free at developer.adzuna.com
ADZUNA_APP_KEY = env("ADZUNA_APP_KEY")

SMTP_HOST = env("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(env("SMTP_PORT", "587"))
SMTP_USER = env("SMTP_USER")            # your gmail address
SMTP_PASS = env("SMTP_PASS")            # gmail App Password (not your login password)
DIGEST_TO = env("DIGEST_TO", "faarouqsocials@gmail.com")

TELEGRAM_BOT_TOKEN = env("TELEGRAM_BOT_TOKEN")  # from @BotFather
TELEGRAM_CHAT_ID   = env("TELEGRAM_CHAT_ID")    # your chat with the bot

# ------------------------------------------------------------------- tuning
MIN_DIGEST_SCORE   = int(env("MIN_DIGEST_SCORE", "55"))   # jobs below this never emailed
MAX_JOBS_PER_RUN   = int(env("MAX_JOBS_PER_RUN", "120"))  # cap on new jobs scored per run
SCORE_BATCH_SIZE   = 8                                    # jobs per Claude call
JOB_EXPIRY_DAYS    = 35                                   # mark stale jobs expired

# ------------------------------------------------------- Adzuna search terms
# Each term = one Adzuna query (Ireland-wide). Keep the list short; Adzuna
# free tier allows ~250 calls/day and we use 1 call per term per run.
ADZUNA_QUERIES = [
    # security
    "graduate security",
    "junior security analyst",
    "SOC analyst",
    "cloud security",
    "DevSecOps",
    "security intern",
    # cloud / devops / infra
    "graduate devops",
    "junior devops",
    "cloud engineer graduate",
    "junior cloud engineer",
    "associate cloud engineer",
    "junior infrastructure engineer",
    "graduate site reliability engineer",
    "junior network engineer",
    # software
    "graduate software engineer",
    "junior software engineer",
    "software intern",
    "junior developer",
    # IT / sysadmin / support
    "graduate IT",
    "junior IT",
    "IT intern",
    "IT support",
    "IT technician",
    "junior system administrator",
    "system administrator",
    "service desk analyst",
    "helpdesk",
    "desktop support",
    "technical support engineer",
    "IT operations",
]

# ---------------------------------------------- ATS boards (public APIs, no key)
# Greenhouse: https://boards-api.greenhouse.io/v1/boards/<token>/jobs
# Lever:      https://api.lever.co/v0/postings/<token>?mode=json
# Ashby:      https://api.ashbyhq.com/posting-api/job-board/<token>
# Edit freely — unknown tokens fail gracefully (skipped with a log line).
GREENHOUSE_BOARDS = [
    "stripe", "datadoghq", "cloudflare", "hubspot", "intercom",
    "tines", "elastic", "gitlab", "twilio", "okta",
    # Irish HQ / large Dublin offices (verified to list Irish roles)
    "flipdish", "letsgetchecked", "squarespace", "toast", "mongodb", "udemy",
]
LEVER_BOARDS = [
    "tenable", "kodifhq",
]
ASHBY_BOARDS = [
    "openai", "ramp",
    "wayflyer",   # Dublin fintech
]

# ------------------------------------------------------------- extra RSS feeds
# Generic RSS/Atom job feeds. Add any feed URL that emits job postings.
RSS_FEEDS = [
    # ("source name", "feed url")
    # e.g. ("WeWorkRemotely-DevOps", "https://weworkremotely.com/categories/remote-devops-sysadmin-jobs.rss"),
]

# --------------------------------------------- pre-filter (saves Claude tokens)
# Titles containing any of these are dropped before AI scoring.
SENIOR_KEYWORDS = [
    "senior", "staff ", "principal", "lead ", "head of", "director",
    "manager", "vp ", "vice president", "architect", "distinguished",
    "sr.", "sr ", "iii", " iv",
]
# Locations must contain one of these (case-insensitive) OR be remote-friendly.
LOCATION_KEYWORDS = ["dublin", "cork", "ireland", "remote", "hybrid", "leinster", "munster", "kildare", "wicklow", "meath"]

# ------------------------------------------------------------- candidate profile
CANDIDATE_PROFILE = """
Name: Faarouq Asaju
Location: Dublin, Ireland — also happy to work in Cork or anywhere in Ireland, and remote/hybrid
(work authorisation: Stamp 1G graduate permission in progress)
Education: BSc (Hons) Computer Science, Griffith College Dublin, graduating June 2026, 2:1
Target roles (priority order): Cloud Security Engineer, SOC Analyst, Cybersecurity Analyst,
DevSecOps, DevOps, Cloud Engineer, Platform Engineer, Site Reliability Engineer,
Infrastructure Engineer, Network Engineer, System Administrator, Software Engineer,
Backend/Full-stack Developer, QA/Test Engineer, IT Support / Service Desk / Helpdesk,
IT Technician, Technical Support Engineer, IT Operations, Data Analyst/Engineer, and any
other graduate/junior/entry-level/internship tech or IT role with transferable fit —
cast a wide net; score any role the candidate could plausibly do at entry level.
Level: GRADUATE / ENTRY-LEVEL / JUNIOR / INTERN ONLY. No senior, staff, lead, manager,
or roles requiring 3+ years professional experience.

Skills: Python, Bash, SQL, FastAPI, PostgreSQL, React/TypeScript, Node.js,
AWS (IAM, EC2, S3, Lambda, CloudTrail, GuardDuty, Security Hub), boto3, Terraform,
Docker, GitHub Actions CI/CD, Semgrep, Trivy, Gitleaks, OWASP Dependency Check,
Linux hardening (CIS Benchmarks), log analysis (auditd/journalctl), LLM API integration.

Certifications: AWS Cloud Practitioner (done), CompTIA Security+ (in progress).

Flagship projects: AWS Cloud Security Posture Management tool (Python/boto3);
Linux Hardening Scanner with CIS/NIST control mapping; Secure CI/CD pipeline
(SAST, container scanning, secrets detection); AI Smart Scheduling Assistant
(FastAPI + PostgreSQL + GPT-4o-mini + React, deployed, 138 tests).

Experience: retail tech support (Currys PC World), web dev internship (Tech Vault).
No professional security/DevOps employment yet — projects carry the profile.

Weak spots (score honestly around these): no professional experience in target field,
no completed security cert yet, limited Splunk/Wireshark hands-on.
"""
