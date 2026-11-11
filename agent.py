"""
Privenstaff Lead Agent v2 — Event Intelligence
Focus: New York City (Manhattan first, then the other four boroughs).
Every morning it:
  1. Collects SIGNALS: NYC event permits, hiring posts for event staff, news/blogs/
     announcements, and a Claude web sweep of event calendars and discussions.
  2. Triages them: keeps real opportunities in NYC, drops competitors.
  3. Goes to the SOURCE: finds the person who books event staff, with published
     email/phone and the URL where each was found.
  4. Also discovers new venues/caterers/planners (Google Places).
  5. Logs everything to Google Sheets and emails you a morning brief.
Legal by design: official APIs, public RSS, public web pages only. No login walls,
no guessed emails, every contact comes with its source.
"""
import os, re, json, time, random, hashlib, datetime, smtplib, imaplib
import email.utils
import email as emaillib
from email.utils import parseaddr
from zoneinfo import ZoneInfo
import xml.etree.ElementTree as ET
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from urllib.parse import urlparse

import requests
from concurrent.futures import ThreadPoolExecutor
import gspread
import anthropic
from google.oauth2.service_account import Credentials

# ======================= SETTINGS (edit freely) =======================
MODEL = "claude-sonnet-5"                    # deep web research (finding the right person)
FAST_MODEL = "claude-haiku-4-5-20251001"     # cheaper model for sorting, pitches, reading pastes
MAX_SIGNALS = int(os.getenv("MAX_SIGNALS", "100000"))   # NO LIMIT: research every kept signal
NEWS_QUERIES_PER_DAY = 14                                # Google News searches per day
SCOUT_THEMES_PER_DAY = 4                                 # Claude web sweeps per day
WORKERS = 6                                              # leads researched in parallel
BACKFILL_PER_DAY = 100000                                    # old rows missing a pitch, filled per run
REFRESH_PER_DAY = 100000                                      # old rows with NO contact, re-researched per tab
RESEARCH_SEARCHES = 5                                    # web searches per lead
MAX_NEW_LEADS = int(os.getenv("MAX_NEW_LEADS", "100000"))  # NO LIMIT on new companies
QUERIES_PER_DAY = 12                                     # Places searches per day
PER_SEARCH_CAP = 60                                       # max new companies from one search (variety)

# Company discovery (Google Places)
CATEGORIES = ["event venues", "catering companies", "event planners", "wedding planners",
              "banquet halls", "hotels with event space", "corporate event planning companies",
              "rooftop event spaces", "country clubs", "party rental companies",
              "wedding venues", "private dining restaurants"]
# NYC focus: Manhattan first (split into neighborhoods so it gets more searches),
# then the other four boroughs.
AREAS = ["Midtown Manhattan NY", "Lower Manhattan NY", "Upper East Side Manhattan NY",
         "Upper West Side Manhattan NY", "Chelsea Manhattan NY", "SoHo Tribeca Manhattan NY",
         "Harlem Manhattan NY", "Brooklyn NY", "Queens NY", "Bronx NY", "Staten Island NY"]

# Hiring posts (Adzuna API) — companies hiring event staff directly
JOB_TITLES = ["banquet server", "event server", "event bartender", "catering server",
              "event staff", "banquet captain", "event coordinator", "catering captain",
              "banquet bartender", "private event server", "cocktail server", "waitstaff",
              "catering staff", "banquet houseman", "barback", "event host"]
JOB_SEARCHES_PER_DAY = 14          # normal months
JOB_SEARCHES_SURGE = 28            # busy seasons (see SURGE_MONTHS)
SURGE_MONTHS = {4, 5, 6, 10, 11, 12}   # wedding season + holiday party season
# A job title must contain one of these to count (filters out line cooks, managers of stores, etc.)
EVENT_ROLE_WORDS = ["server", "bartend", "banquet", "catering", "event", "captain", "wait",
                    "barback", "busser", "runner", "host", "houseman", "cocktail"]
URGENT_WORDS = ["immediate", "urgent", "asap", "start today", "this weekend", "weekend",
                "on-call", "on call", "per diem", "per-diem", "as needed", "flexible",
                "part-time", "part time", "seasonal", "temporary", "temp ", "holiday",
                "hiring now", "hiring immediately", "same day pay", "daily pay"]
SKIP_EMPLOYER_WORDS = ["corporate office", "headquarters", "remote", "cruise", "senior living",
                       "assisted living", "nursing", "hospital", "healthcare", "health system",
                       "rehabilitation", "school district"]
# Titles with these words are not event-staff jobs (sales, office, kitchen, etc.)
EXCLUDE_TITLE_WORDS = ["sales", "director", "account", "marketing", "recruit", "admin",
                       "vice president", "intern", "cashier", "barista", "cook", "chef",
                       "dishwasher", "housekeep", "driver", "security", "analyst", "engineer"]
NYC_PLACE_WORDS = ["new york, ny", "manhattan", "brooklyn", "queens", "bronx", "staten island",
                   "long island city", "astoria", "flushing", "jamaica", "harlem", "new york city",
                   "new york county", "kings county", "richmond county"]
NOT_NYC_WORDS = ["new jersey", ", nj", "hudson county", "essex county", "bergen county",
                 "union county", "passaic", "middlesex", "morris county", "westchester",
                 "nassau", "suffolk", "connecticut", "hoboken", "jersey city", "newark"]
FREQUENT_HIRER_POSTS = 3           # posts in 60 days that mark a "frequent event hirer"
JOB_AREAS = ["Manhattan, NY", "New York, NY", "Brooklyn, NY", "Queens, NY", "Bronx, NY",
             "Staten Island, NY"]

# News, announcements, blogs (Google News RSS)
NEWS_QUERIES = ['gala New York', 'benefit dinner New York', 'fundraiser gala NYC',
                'new event venue opening New York', 'hotel opening New York',
                'new restaurant private dining NYC', 'conference announced New York',
                'Javits Center upcoming show', 'new event space Manhattan',
                'new event space Brooklyn', 'new event venue Queens',
                'Bronx event venue opening', 'site:bizbash.com New York',
                'grand opening celebration NYC', 'awards ceremony New York',
                'product launch event New York', 'charity ball New York',
                'catering company expands New York', 'annual gala Manhattan',
                'honorees announced gala New York', 'benefit luncheon New York',
                'hotel ballroom renovation New York', 'new rooftop bar Manhattan opening',
                'restaurant opening Manhattan private events', 'Brooklyn wedding venue new',
                'museum gala New York', 'nonprofit fundraiser Brooklyn',
                'holiday party venue New York', 'corporate event New York announced',
                'fashion show New York event', 'film premiere after party New York',
                'book launch party New York', 'art gallery opening reception New York',
                'food festival New York tickets', 'wine tasting event Manhattan',
                'pop-up event Manhattan brand', 'summit New York City announced',
                'site:ny.eater.com opening', 'site:timeout.com/newyork events']

# Claude web sweep themes (calendars, programs, discussions)
SCOUT_THEMES = ["upcoming galas, benefits and charity fundraisers",
                "upcoming conferences, trade shows, summits and expos",
                "new event venues, hotels and restaurants opening or reopening",
                "bridal shows, wedding expos and venue showcases",
                "brand activations, product launches and pop-up events",
                "museum, university and nonprofit event programs and seasons",
                "holiday party season and corporate event programs",
                "public forum and community discussions about event planning or event staffing needs",
                "hotels and banquet halls advertising their fall and holiday event calendars",
                "museum and landmark venues that rent space for private events and their upcoming bookings",
                "restaurant groups and hospitality groups opening new locations",
                "fashion, film, art and media industry parties, premieres and launches",
                "sports, entertainment and concert venue hospitality and VIP events",
                "large Eventbrite, Partiful and ticketed parties and festivals with food and drink",
                "caterers and event planners announcing big contracts, new venues or expansions",
                "school, university and alumni galas, reunions and fundraising dinners"]

# Skip competitors (other staffing agencies) in hiring posts
COMPETITOR_WORDS = ["staffing", "staff agency", "personnel", "recruit", "temps", "talent",
                    "workforce", "employment", "hire quest", "labor", "manpower"]

# ---------------- OUTREACH (email sending with your approval) ----------------
# Flow: the agent drafts an email for every lead with an email address -> you review/edit it
# in the sheet -> type Send in the "Approve" column -> the next run sends it and logs it.
# A short follow-up goes out automatically after FOLLOWUP_DAYS unless "Reply Status" is filled.
OUTREACH_COLS = ["Email Subject", "Email Body", "Approve", "Sent On", "Follow-up Sent On",
                 "Reply Status"]
SENDER_NAME = "Juan Benson"
SENDER_TITLE = "Owner, Privenstaff"
SENDER_PHONE = "212-470-9043"
SENDER_SITE = "www.Privenstaff.net"
SEND_LIMIT_PER_DAY = int(os.getenv("SEND_LIMIT_PER_DAY", "25"))  # max per send run
# Hard cap for the whole day (New York date), counting everything already sent today.
# Protects the Gmail account: a new or recently-flagged account should stay around 20-30/day.
DAILY_SEND_CAP = int(os.getenv("DAILY_SEND_CAP", "25"))
# Mail-server answers that mean "stop sending now" (limits, blocks, login problems)
STOP_SIGNALS = ("5.4.5", "4.7.0", "421", "454", "5.7.0", "5.7.1", "5.7.8", "sending limit",
                "Username and Password", "rate limit", "temporarily", "blocked", "disabled",
                "535", "authentication", "authenticationfailed", "incorrect authentication",
                "login failed", "invalid credentials")
DRAFTS_PER_DAY = 100000
# Addresses the receiving server rejects right away (doesn't exist, mailbox full, etc.)
RECIPIENT_BAD = ("5.1.1", "5.1.0", "5.1.2", "user unknown", "does not exist", "no such user",
                 "mailbox unavailable", "invalid recipient", "recipient address rejected",
                 "unknown recipient", "address rejected", "not found")
BOUNCE_STOP_MIN = 10        # after at least this many rejected addresses in one run...
BOUNCE_STOP_RATE = 0.20     # ...stop the run if more than 20% of attempts were rejected
FOLLOWUP_DAYS = 4
AUTO_FOLLOWUP = True
# Auto-send: 0 = OFF (every email needs your approval). Set to e.g. 8 to auto-send leads with
# fit score >= 8 AND a personal email (not info@/hello@/events@...). Everything else still waits.
AUTO_SEND_MIN_FIT = 0
APPROVE_WORDS = {"send", "true", "x", "yes", "approved", "ok", "\u2713", "\u2714"}  # checkbox = TRUE
GENERIC_INBOXES = ("info@", "hello@", "contact@", "events@", "event@", "sales@", "careers@",
                   "jobs@", "hr@", "admin@", "office@", "reservations@", "rsvp@", "bookings@",
                   "privateevents@", "inquiries@", "catering@")
REPLY_CHECK_DAYS = 21              # how far back the agent reads your Gmail inbox for replies
PROBLEMS = []                      # collected during the run, shown in the morning email
# Everything about email outreach lives in its own tab, left-to-right in the order you use it
# Drop any emails from other sources here; the agent cleans them, writes the message in the
# Privenstaff format and moves them to the Email Queue for your approval.
DROP_HEADERS = ["Email", "Name", "Company", "Message or Notes", "Source", "Status", "Processed On"]
DROP_SIGNOFF = "Email us at jbenson@privenstaff.net or call 212-470-9043."
DROP_PER_RUN = 300                 # big lists are processed in chunks of this size, every hour
QUEUE_HEADERS = ["Approve", "Send At", "Company", "Contact Name", "Title", "Email", "Fit Score",
                 "Email Subject", "Email Body", "Sent On", "Follow-up Sent On", "Follow-up 2 Sent On", "Reply Status",
                 "Lead Type", "Pitch Angle", "Source Tab", "Date Added", "Sent From", "Segment", "Variant"]
TEXT_BATCH_HEADERS = ["Date", "Contacts", "Text Batch (copy this cell)", "Done"]
TEXT_SIGNOFF = "Email me at jbenson@privenstaff.net"
# ---- TEXT ENGINE (daily MassText batches) — change these in daily-leads.yml ----
TEXTS_PER_DAY = int(os.getenv("TEXTS_PER_DAY", "300"))          # contacts per day
TEXT_BATCH_SIZE = int(os.getenv("TEXT_BATCH_SIZE", "50"))       # contacts per Text Batches cell
PHONE_LOOKUPS_PER_DAY = int(os.getenv("PHONE_LOOKUPS_PER_DAY", "150"))  # find missing phones
TEXT_AGAIN_DAYS = int(os.getenv("TEXT_AGAIN_DAYS", "60"))       # never text a number again sooner
TEXT_STOP_LINE = os.getenv("TEXT_STOP_LINE", "0") == "1"        # add "Reply STOP to opt out."
DNT_HEADERS = ["Phone", "Name", "Reason", "Added On"]            # "Do Not Text" tab
# ---- EMAIL FINDER: reads company websites for published email addresses ----
EMAIL_LOOKUPS_PER_DAY = int(os.getenv("EMAIL_LOOKUPS_PER_DAY", "200"))
SKIP_SITES = ("linkedin.", "facebook.", "instagram.", "twitter.", "x.com", "yelp.", "google.",
              "eventbrite.", "tripadvisor.", "youtube.", "tiktok.", "nytimes.", "timeout.",
              "eater.", "bizbash.", "theknot.", "weddingwire.", "indeed.", "glassdoor.",
              "adzuna.", "ziprecruiter.", "culinaryagents.", "patch.com", "wikipedia.", "cvent.",
              "nyc.gov", "data.cityofnewyork", "prnewswire.", "businesswire.", "opentable.",
              "resy.", "sevenrooms.", "peerspace.", "splacer.", "tagvenue.", "partyslate.")
BAD_EMAIL_BITS = ("example.", "sentry", "wixpress", "noreply", "no-reply", "donotreply",
                  "privacy@", "abuse@", "webmaster@", "postmaster@", "@2x", ".png", ".jpg",
                  ".jpeg", ".gif", ".webp", ".svg", "domain.com", "email.com", "yourname",
                  "careers@", "jobs@", "hr@", "press@", "media@", "billing@", "accounts@",
                  "support@", "help@", "legal@", "@sentry", "godaddy", "squarespace")
GOOD_INBOXES = ("events", "event", "privateevents", "private", "catering", "sales", "booking",
                "bookings", "banquet", "weddings", "groups", "partyplanning", "gm", "manager")
PHONE_RE = re.compile(r"\+?1?[\s.-]?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}(?:\s*(?:x|ext\.?)\s*\d+)?",
                      re.I)
OUTREACH_LOG_HEADERS = ["Sent At", "Type", "To", "Company", "Subject", "Tab", "Row", "From"]
EMAIL_RE = re.compile(r"^[^@\s,;]+@[^@\s,;]+\.[a-z]{2,}$", re.I)

COMPANY_HEADERS = ["Date Found", "Company", "Category", "Area", "Contact Name", "Title",
                   "Email", "Phone", "Contact Source", "Website", "Address", "Google Rating",
                   "Fit Score", "Why a Fit", "Pitch Angle", "Place ID", "Status", "Texted On",
                   "Phone Checked", "Email Checked"]
SIGNAL_HEADERS = ["Date Found", "Signal Type", "Headline", "Event Date", "Organizer",
                  "Venue", "Contact Name", "Title", "Email", "Phone", "Contact Source",
                  "Alt Contact", "Urgency", "Fit Score", "Pitch Angle", "Signal URL",
                  "Status", "Signal ID", "Hiring Flags", "Pay Posted", "Texted On", "Phone Checked",
                  "Email Checked"]
INBOX_HEADERS = ["Paste Listings or Links Here", "Source", "Notes", "Status", "Processed On",
                 "Leads Found"]
MAX_INBOX_LEADS = 100000               # pasted leads deep-researched per run; the rest are saved now
                                   # and researched automatically over the next runs
HIRING_LOG_HEADERS = ["Date Seen", "Company", "Job Title", "Location", "Pay", "Job Type",
                      "URL", "Job ID"]
# ======================================================================

TODAY = datetime.date.today()


def rotate(items, n):
    """Pick a different, well-mixed set of items each day (repeatable per date)."""
    return random.Random(TODAY.toordinal()).sample(items, min(n, len(items)))


def domain_of(url):
    return urlparse(url).netloc.lower().removeprefix("www.") if url else ""


def make_id(*parts):
    return hashlib.sha1("|".join(p or "" for p in parts).lower().encode()).hexdigest()[:16]


def parse_json(text, array=False):
    """Robust JSON extraction. For arrays it collects every complete {...} object, so a
    reply that got cut off or has extra prose still yields all the finished items."""
    text, dec, found, i = text or "", json.JSONDecoder(), [], 0
    while True:
        j = text.find("{", i)
        if j < 0:
            break
        try:
            obj, end = dec.raw_decode(text, j)
            if isinstance(obj, dict):
                if not array:
                    return obj
                found.append(obj)
            i = end
        except ValueError:
            i = j + 1
    return found if array else {}


class OutOfCredits(Exception):
    pass


CREDITS = {"out": False}   # flips to True the moment the balance runs out


def problem(msg):
    if msg not in PROBLEMS:
        PROBLEMS.append(msg)


def ask_claude(client, prompt, searches=0, max_tokens=4000, fast=False):
    messages = [{"role": "user", "content": prompt}]
    kwargs = dict(model=FAST_MODEL if fast else MODEL, max_tokens=max_tokens)
    if searches:
        kwargs["tools"] = [{"type": "web_search_20250305", "name": "web_search",
                            "max_uses": searches}]
    text = ""
    try:
        for _ in range(4):
            resp = client.messages.create(messages=messages, **kwargs)
            text += "".join(b.text for b in resp.content if b.type == "text")
            if resp.stop_reason == "pause_turn":   # long web research: let it continue
                messages = [messages[0], {"role": "assistant", "content": resp.content}]
                continue
            if resp.stop_reason == "max_tokens":
                print("  Note: Claude reply hit the length limit; keeping finished items.")
            break
    except Exception as e:
        if "credit balance is too low" in str(e):
            CREDITS["out"] = True
            raise OutOfCredits() from e
        print(f"  Claude call failed: {e}")
        problem(f"AI call failed: {str(e)[:120]}")
    return text


def signal(kind, headline, url, details, event_date="", company=""):
    return {"type": kind, "headline": headline, "url": url or "", "details": details,
            "event_date": event_date, "company": company,
            "id": make_id(kind, url or headline)}


# ------------------------- SIGNAL COLLECTORS -------------------------

def collect_permits():
    """NYC Open Data: approved event permits for the next month.
    OFF by default: nyc_permits.py now handles permits (its own "NYC Permits" tab).
    Set the env var AGENT_PERMITS=1 to turn this old collector back on."""
    if os.getenv("AGENT_PERMITS", "0") != "1":
        return []
    try:
        r = requests.get("https://data.cityofnewyork.us/resource/tvpp-9vvx.json",
                         params={"$limit": 1000}, timeout=60)
        rows = r.json()
    except Exception as e:
        print(f"  Permits failed: {e}")
        return []
    out = []
    for x in rows:
        etype = (x.get("event_type") or "").lower()
        if any(k in etype for k in ("sport", "farmers market", "production", "construction",
                                     "stickball", "sidewalk sale", "theater load")):
            continue  # skip event types that never need hospitality staff
        name = x.get("event_name", "")
        details = (f"{x.get('event_type','')} permit; agency {x.get('event_agency','')}; "
                   f"{x.get('event_location','')}, {x.get('event_borough','')}")
        out.append(signal("City event permit", name,
                          "https://data.cityofnewyork.us/d/tvpp-9vvx", details,
                          (x.get("start_date_time") or "")[:10]))
        out[-1]["id"] = make_id("permit", x.get("event_id") or name)
    return out[:180]


def adzuna(path, **params):
    params.update(app_id=os.environ["ADZUNA_APP_ID"], app_key=os.environ["ADZUNA_APP_KEY"])
    params.setdefault("content-type", "application/json")
    r = requests.get(f"https://api.adzuna.com/v1/api/jobs/us/{path}", params=params, timeout=30)
    r.raise_for_status()
    return r.json()


def fmt_pay(j):
    lo, hi = j.get("salary_min"), j.get("salary_max")
    if not (lo or hi):
        return ""
    def one(v):  # Adzuna reports yearly figures; show hourly when it looks like hourly work
        return f"${v/2080:.0f}/hr" if v and v > 1000 else (f"${v:.0f}/hr" if v else "")
    return one(lo) if lo == hi or not hi else f"{one(lo)}-{one(hi)}"


def collect_jobs(log_ws=None):
    """Adzuna: businesses hiring event staff themselves = direct, current need.
    Groups posts by company, scores urgency, tracks repeat hirers over 60 days."""
    if not (os.getenv("ADZUNA_APP_ID") and os.getenv("ADZUNA_APP_KEY")):
        return []
    n = JOB_SEARCHES_SURGE if TODAY.month in SURGE_MONTHS else JOB_SEARCHES_PER_DAY
    posts = {}
    for title, area in rotate([(t, a) for t in JOB_TITLES for a in JOB_AREAS], n):
        try:
            jobs = adzuna("search/1", what=title, where=area, results_per_page=50,
                          max_days_old=10).get("results", [])
        except Exception as e:
            print(f"  Jobs failed ({title}, {area}): {e}")
            continue
        for j in jobs:
            company = (j.get("company") or {}).get("display_name", "").strip()
            jt = (j.get("title") or "").lower()
            text = f"{jt} {(j.get('description') or '').lower()}"
            loc = j.get("location") or {}
            place = " ".join([loc.get("display_name", "")] + list(loc.get("area") or [])).lower()
            if (not company or any(w in company.lower() for w in COMPETITOR_WORDS)
                    or any(w in f"{text} {company.lower()}" for w in SKIP_EMPLOYER_WORDS)
                    or not any(w in jt for w in EVENT_ROLE_WORDS)
                    or any(w in jt for w in EXCLUDE_TITLE_WORDS)
                    or any(w in place for w in NOT_NYC_WORDS)
                    or not any(w in place for w in NYC_PLACE_WORDS)):
                continue
            posts[str(j.get("id") or j.get("redirect_url"))] = (company, j)

    # Hiring log: remember every post, so we can spot companies that hire again and again
    history = {}
    if log_ws is not None:
        try:
            hdr = sheet_headers(log_ws, HIRING_LOG_HEADERS)
            rows = log_ws.get_all_values()[1:]
            ci, di, ii = hdr.index("Company"), hdr.index("Date Seen"), hdr.index("Job ID")
            cutoff = (TODAY - datetime.timedelta(days=60)).isoformat()
            known_ids = {r[ii] for r in rows if len(r) > ii}
            for r in rows:
                if len(r) > max(ci, di) and r[di] >= cutoff:
                    history[r[ci].lower()] = history.get(r[ci].lower(), 0) + 1
            new = [(pid, c, j) for pid, (c, j) in posts.items() if pid not in known_ids]
            if new:
                log_ws.append_rows([[safe_cell(v) for v in (
                    TODAY.isoformat(), c, j.get("title", ""),
                    (j.get("location") or {}).get("display_name", ""), fmt_pay(j),
                    j.get("contract_time", ""), j.get("redirect_url", ""), pid)]
                    for pid, c, j in new], value_input_option="USER_ENTERED")
                for _, c, _ in new:
                    history[c.lower()] = history.get(c.lower(), 0) + 1
        except Exception as e:
            print(f"  Hiring log skipped: {e}")

    by_company = {}
    for company, j in posts.values():
        by_company.setdefault(company, []).append(j)

    out = []
    month = TODAY.strftime("%Y-%m")
    for company, jobs in by_company.items():
        titles = sorted({j.get("title", "") for j in jobs})
        blob = " ".join(f"{j.get('title','')} {j.get('description','')}" for j in jobs).lower()
        urgent = sorted({w.strip() for w in URGENT_WORDS if w in blob})
        count60 = max(history.get(company.lower(), 0), len(jobs))
        flags = []
        if count60 >= FREQUENT_HIRER_POSTS:
            flags.append(f"Frequent event hirer ({count60} posts/60 days) - likely staffs per event")
        if len(jobs) > 1:
            flags.append(f"{len(jobs)} open roles now")
        if urgent:
            flags.append("Urgent/flexible: " + ", ".join(urgent[:5]))
        pay = next((fmt_pay(j) for j in jobs if fmt_pay(j)), "")
        loc = (jobs[0].get("location") or {}).get("display_name", "")
        details = (f"FLAGS: {'; '.join(flags) or 'none'}. PAY: {pay or 'not posted'}. "
                   f"ROLES: {', '.join(titles[:6])}. {loc}. "
                   f"{(jobs[0].get('description') or '')[:200]}")
        sig = signal("Hiring post", f"{company} is hiring: {', '.join(titles[:3])}",
                     jobs[0].get("redirect_url"), details, company=company)
        sig["id"] = make_id("hire", company, month)   # re-alerts at most once a month
        sig["flags"], sig["pay"] = "; ".join(flags), pay
        out.append(sig)

    # Top hiring employers for event roles in NYC (weekly, Mondays)
    if TODAY.weekday() == 0:
        for what in ("banquet", "catering", "event server", "bartender"):
            try:
                board = adzuna("top_companies", what=what, where="New York, NY").get("leaderboard", [])
            except Exception as e:
                print(f"  Top companies failed ({what}): {e}")
                continue
            for x in board[:10]:
                name = x.get("canonical_name") or x.get("display_name") or ""
                if not name or any(w in name.lower() for w in COMPETITOR_WORDS):
                    continue
                sig = signal("Top event hirer", f"{name}: one of NYC's top employers for {what} jobs",
                             "", f"FLAGS: Top hirer, {x.get('count', '?')} current {what} posts in NYC "
                             f"- steady staffing need.", company=name)
                sig["id"] = make_id("tophire", name, month)
                sig["flags"] = f"Top NYC {what} employer ({x.get('count', '?')} posts)"
                out.append(sig)
    return out


def collect_news():
    """Google News RSS: announcements, openings, galas, blogs (last 7 days)."""
    out = []
    for q in rotate(NEWS_QUERIES, NEWS_QUERIES_PER_DAY):
        try:
            r = requests.get("https://news.google.com/rss/search", timeout=30,
                             params={"q": f"{q} when:14d", "hl": "en-US", "gl": "US",
                                     "ceid": "US:en"})
            items = list(ET.fromstring(r.content).iter("item"))[:20]
        except Exception as e:
            print(f"  News failed ({q}): {e}")
            continue
        for it in items:
            src = it.findtext("source") or ""
            out.append(signal("News / announcement", it.findtext("title") or "",
                              it.findtext("link"), f"Source: {src}. Published {it.findtext('pubDate')}"))
    return out


def collect_scout(client):
    """Claude web sweeps (several themes per day, run in parallel)."""
    themes = rotate(SCOUT_THEMES, SCOUT_THEMES_PER_DAY)
    with ThreadPoolExecutor(WORKERS) as pool:
        return [s for batch in pool.map(lambda t: scout_theme(client, t), themes) for s in batch]


def scout_theme(client, theme):
    text = ask_claude(client, f"""Today is {TODAY}. Search the web for {theme} in New York City
(Manhattan first, then Brooklyn, Queens, the Bronx and Staten Island), happening or announced for the next 120 days. Check event
calendars, venue calendars, nonprofit gala pages, convention center schedules, industry
blogs, and public discussion threads. Return up to 20 real items with a real source URL.
Reply with ONLY a JSON array:
[{{"headline": "", "event_date": "YYYY-MM-DD or ''", "organizer": "", "venue": "",
   "url": "", "summary": ""}}]""", searches=8, max_tokens=10000)
    out = []
    for x in parse_json(text, array=True):
        out.append(signal("Web intelligence", x.get("headline", ""), x.get("url"),
                          f"Organizer: {x.get('organizer','')}. Venue: {x.get('venue','')}. "
                          f"{x.get('summary','')}", x.get("event_date", ""),
                          x.get("organizer", "")))
    return out


# ------------------------- TRIAGE + RESEARCH -------------------------

def triage(client, signals, keep_all=False):
    """One cheap call to keep only real staffing opportunities."""
    must_keep = ("\nIMPORTANT: every item below was hand-picked by the owner. KEEP EVERY ITEM; "
                 "just fill in the fields.\n") if keep_all else ""
    kept = []
    for start in range(0, len(signals), 25):
        batch = signals[start:start + 25]
        listing = "\n".join(f"{i}. [{s['type']}] {s['headline']} | {s['event_date']} | "
                            f"{s['details'][:320]}" for i, s in enumerate(batch))
        text = ask_claude(client, f"""You screen leads for Privenstaff, an event & hospitality
staffing agency (servers, bartenders, captains, event coordinators) focused on New York
City: Manhattan first, then Brooklyn, Queens, the Bronx and Staten Island.
Today is {TODAY}. Keep items where some organization will likely need that staff now or
soon: galas, benefits, weddings, conferences, launches, parties, premieres, openings of
venues/hotels/restaurants, caterers or planners growing, venues/caterers hiring event staff,
and permitted events in parks or plazas that could be catered. When unsure, KEEP it with a
low fit score rather than drop it. Drop only: other staffing agencies, anything clearly
outside the five NYC boroughs, events already over, pure sports or street fairs, and news
with no organization to contact.

Hiring posts and top hirers are STRONG signals: a venue, caterer, hotel, restaurant or
planner hiring event roles has a staffing need right now. Keep them. Mark urgency High when
FLAGS show urgent/flexible/per-diem/weekend wording or a frequent event hirer. A frequent
event hirer usually runs on per-event temp staff, which makes them MORE likely to contract
an agency. For hiring posts, the pitch angle should reference the post, e.g. offer to cover
their events while they fill the role; if they hire per event, offer to be their go-to
bench; if PAY is posted, contrast hiring and scheduling part-timers at that rate with
booking Privenstaff only for the nights they need.

{must_keep}{listing}

Reply with ONLY a JSON array of keepers:
[{{"i": 0, "organizer": "who hosts or pays", "venue": "", "event_date": "YYYY-MM-DD or ''",
   "urgency": "High|Medium|Low", "fit_score": 1-10,
   "pitch_angle": "one sentence Privenstaff can open with"}}]""", max_tokens=8000, fast=True)
        for k in parse_json(text, array=True):
            i = k.get("i")
            if isinstance(i, int) and 0 <= i < len(batch):
                kept.append({**batch[i], **k})
    rank = {"High": 0, "Medium": 1, "Low": 2}
    kept.sort(key=lambda s: (rank.get(s.get("urgency"), 3), -int(s.get("fit_score") or 0)))
    return kept


def hunter_contacts(domain):
    key = os.getenv("HUNTER_API_KEY")
    if not key or not domain:
        return []
    try:
        r = requests.get("https://api.hunter.io/v2/domain-search", timeout=30,
                         params={"domain": domain, "api_key": key, "limit": 10})
        return [{"name": f"{e.get('first_name') or ''} {e.get('last_name') or ''}".strip(),
                 "title": e.get("position") or "", "email": e.get("value"),
                 "confidence": e.get("confidence")}
                for e in r.json().get("data", {}).get("emails", [])]
    except Exception:
        return []


def find_decision_maker(client, org, context, website=""):
    """Go to the source: the person who books event staff."""
    known = hunter_contacts(domain_of(website))
    text = ask_claude(client, f"""Find the person who books event staff (servers, bartenders,
captains) for this opportunity, for Privenstaff, a New York City event staffing agency.

Organization: {org}
Website: {website or "find it"}
Context: {context}
Contacts from Hunter.io (published sources): {json.dumps(known) if known else "none"}

Search the organization's site (team, contact, events, press pages), press releases,
event and gala committee pages, venue event-sales pages, and public LinkedIn profiles.
Likely titles: Director of Events, Event Manager, Catering Sales Manager, Banquet Manager,
Special Events Director, Development Director (for galas), Owner, General Manager.
If the event is at a venue whose catering team books staff, give the most likely buyer and
put the other in alt_contact.

Rules: only contact details published publicly; give the URL where you found them; never
guess or construct an email; prefer a direct email over info@; business phone lines only.

Reply with ONLY JSON:
{{"contact_name": "", "title": "", "email": "", "phone": "", "contact_source": "URL",
  "website": "", "alt_contact": "name, title, email/phone", "fit_score": 1-10,
  "why_fit": "one sentence",
  "pitch_angle": "one-sentence opener Privenstaff can use with this contact. Make it
   specific: tie it to something real you found (an upcoming event, busy season, new
   space, recent expansion, venue size, catering menu) and how reliable event staff
   helps them. No generic lines."}}""", searches=RESEARCH_SEARCHES, max_tokens=3000)
    return parse_json(text)


# ------------------------- COMPANY DISCOVERY -------------------------

def places_search(query):
    headers = {"Content-Type": "application/json",
               "X-Goog-Api-Key": os.environ["GOOGLE_PLACES_API_KEY"],
               "X-Goog-FieldMask": ("places.id,places.displayName,places.formattedAddress,"
                                    "places.websiteUri,places.nationalPhoneNumber,"
                                    "places.rating,places.businessStatus,nextPageToken")}
    results, token = [], None
    for _ in range(3):
        body = {"textQuery": query, "pageSize": 20}
        if token:
            body["pageToken"] = token
        r = requests.post("https://places.googleapis.com/v1/places:searchText",
                          headers=headers, json=body, timeout=30)
        r.raise_for_status()
        data = r.json()
        results += data.get("places", [])
        token = data.get("nextPageToken")
        if not token:
            break
        time.sleep(2)
    return [p for p in results if p.get("businessStatus", "OPERATIONAL") == "OPERATIONAL"]


# ------------------------- SHEETS + EMAIL -------------------------

def open_tabs():
    info = json.loads(os.environ["GOOGLE_SERVICE_ACCOUNT_JSON"])
    creds = Credentials.from_service_account_info(
        info, scopes=["https://www.googleapis.com/auth/spreadsheets"])
    book = gspread.authorize(creds).open_by_key(os.environ["SHEET_ID"])

    def tab(title, headers, also=()):
        """Find a tab by NAME (never by position, so a Dashboard tab in front is safe)."""
        ws = None
        for name in (title,) + tuple(also):
            try:
                ws = book.worksheet(name)
                break
            except gspread.WorksheetNotFound:
                continue
        if ws is None:
            ws = book.add_worksheet(title=title, rows=2000, cols=len(headers))
        if not ws.row_values(1):
            ws.append_row(headers)
        return ws
    # The company leads tab is called "Sheet1" in your sheet (or "Companies" if you rename it)
    return (tab("Sheet1", COMPANY_HEADERS, also=("Companies",)), tab("Signals", SIGNAL_HEADERS),
            tab("Hiring Log", HIRING_LOG_HEADERS), tab("Inbox", INBOX_HEADERS),
            tab("Outreach Log", OUTREACH_LOG_HEADERS), tab("Text Batches", TEXT_BATCH_HEADERS),
            tab("Email Queue", QUEUE_HEADERS), tab("Email Drop", DROP_HEADERS))


def sheet_headers(ws, defaults):
    """Read the sheet's real header row, so you can reorder columns or add your own.
    Any standard column that's missing gets added back at the far right."""
    hdr = [h.strip() for h in ws.row_values(1)]
    if not any(hdr):
        ws.append_row(defaults)
        return list(defaults)
    missing = [h for h in defaults if h not in hdr]
    if missing:
        if ws.col_count < len(hdr) + len(missing):
            ws.add_cols(len(hdr) + len(missing) - ws.col_count)
        start = gspread.utils.rowcol_to_a1(1, len(hdr) + 1)
        ws.update(range_name=start, values=[missing])
        hdr += missing
    return hdr


def column(rows, headers, name):
    i = headers.index(name)
    return {r[i] for r in rows if len(r) > i and r[i]}


def html_table(headers, rows):
    head = "".join(f"<th>{h}</th>" for h in headers)
    body = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in rows)
    return (f"<table border='1' cellpadding='6' style='border-collapse:collapse;"
            f"font-family:Arial;font-size:13px'><tr style='background:#222;color:#fff'>"
            f"{head}</tr>{body}</table>")


def send_email(signals, companies, panel=None):
    panel = panel or {}
    sheet_url = f"https://docs.google.com/spreadsheets/d/{os.environ['SHEET_ID']}"
    html = f"<h2>Privenstaff morning brief – {TODAY.strftime('%A, %B %d')}</h2>"
    probs = panel.get("problems", [])
    html += ("<p style='background:#e8f5e9;padding:8px'>✅ <b>All systems OK</b>: credits, "
             "Gmail and sources working.</p>" if not probs else
             "<p style='background:#fff3e0;padding:8px'>⚠️ <b>Needs attention:</b><br>"
             + "<br>".join(probs[:6]) + "</p>")
    replies, sent, pending = panel.get("replies", []), panel.get("sent", []), panel.get("pending", [])
    html += f"<h3>💬 Replies ({len(replies)})</h3>"
    html += html_table(["Status", "Company", "Email"],
                       [[x["status"], x["company"], x["email"]] for x in replies]) \
        if replies else "<p>No new replies.</p>"
    html += f"<h3>✅ Waiting for your approval ({len(pending)})</h3>"
    html += (html_table(["Fit", "Company", "Contact", "Subject", "Tab"],
                        [[x["fit"], x["company"], x["contact"], x["subject"], x["tab"]]
                         for x in pending[:15]])
             + (f"<p><small>+{len(pending) - 15} more in the sheet</small></p>"
                if len(pending) > 15 else "")) if pending else "<p>Nothing waiting.</p>"
    texts = panel.get("texts", [])
    if texts:
        total = sum(n for n, _ in texts)
        html += (f"<h3>📱 Today's text batch ({total} contacts)</h3>"
                 "<pre style='white-space:pre-wrap;font-family:Arial;font-size:13px'>"
                 + "\n\n".join(t for _, t in texts).replace("<", "&lt;") + "</pre>")
    res = panel.get("results", [])
    if res:
        html += "<h3>📈 Outreach results (last 7 days)</h3>"
        html += html_table(["Group", "Name", "Sent", "Replies", "Reply rate", "Booked"],
                           [[r[1], r[2], r[3], r[4], r[5], r[6]] for r in res])
    html += f"<h3>📤 Sent this run ({len(sent)})</h3>"
    html += html_table(["Type", "Company", "To", "Subject"],
                       [[x["type"], x["company"], x["to"], x["subject"]] for x in sent]) \
        if sent else "<p>No emails sent this run.</p>"
    html += f"<h3>🔥 Event intelligence ({len(signals)})</h3>"
    html += html_table(
        ["Urgency", "Signal", "Event date", "Contact", "Email / Phone", "Pitch angle"],
        [[s["Urgency"], f"<a href='{s['Signal URL']}'>{s['Headline']}</a><br><small>"
          f"{s['Organizer']} · {s['Venue']}</small>", s["Event Date"],
          f"{s['Contact Name']}<br><small>{s['Title']}</small>",
          f"{s['Email']}<br>{s['Phone']}", f"<small>{s['Pitch Angle']}</small>"]
         for s in signals]) if signals else "<p>No new signals today.</p>"
    html += f"<h3>🏢 New companies ({len(companies)})</h3>"
    html += html_table(
        ["Company", "Contact", "Email / Phone", "Fit", "Pitch angle"],
        [[f"<b>{c['Company']}</b><br><small>{c['Category']} · {c['Area']}</small>",
          f"{c['Contact Name']}<br><small>{c['Title']}</small>",
          f"{c['Email']}<br>{c['Phone']}", c["Fit Score"], f"<small>{c['Pitch Angle']}</small>"]
         for c in companies]) if companies else "<p>No new companies today.</p>"
    html += f"<p><a href='{sheet_url}'>Open the full lead sheet</a></p>"

    subject = (f"{'⚠️ ' if probs else ''}Privenstaff brief – {TODAY.strftime('%b %d')}: "
               f"{len(pending)} to approve, {len(replies)} replies, "
               f"{len(signals) + len(companies)} new leads")
    cfg = panel.get("cfg") or {"settings": dict(SENDING_DEFAULTS), "senders": []}
    boxes = [x for x in cfg["senders"] if x["active"] and x["password"]]
    to = os.environ.get("REPORT_TO") or (boxes[0]["email"] if boxes else "")
    if not boxes or not to:
        print("Morning brief not emailed: no active sending mailbox (or REPORT_TO) set up.")
        return
    mailer = Mailer(cfg)
    try:
        mailer.send(boxes[0], to, subject, html, html=True)   # one email to yourself
    finally:
        mailer.close()


# ------------------------- MAIN -------------------------

def safe_cell(v):
    """Stop Sheets from reading phone numbers like +1 718... as formulas (#ERROR!)."""
    v = "" if v is None else str(v)
    return "'" + v if v[:1] in ("=", "+", "-", "@") else v


def write_pitches(client, items):
    """items: list of dicts describing leads. Returns a pitch per item (same order).
    One cheap call per 20 leads, no web search, using what we already know."""
    pitches = [""] * len(items)
    for start in range(0, len(items), 20):
        batch = items[start:start + 20]
        listing = "\n".join(f"{i}. " + json.dumps(x, ensure_ascii=False)
                            for i, x in enumerate(batch))
        text = ask_claude(client, f"""Write a pitch angle for each lead below for Privenstaff, a New York
City event staffing agency (servers, bartenders, captains, event coordinators).
Each pitch is ONE sentence Privenstaff can open an email with. Address the contact by
first name if one is given. Tie it to something specific in the lead's details (their
venue type, events, opening, expansion, conference, size). No generic lines, no invented
facts, and do not start with a symbol.

{listing}

Reply with ONLY a JSON array: [{{"i": 0, "pitch_angle": ""}}]""", max_tokens=6000, fast=True)
        for k in parse_json(text, array=True):
            i = k.get("i")
            if isinstance(i, int) and 0 <= i < len(batch) and k.get("pitch_angle"):
                pitches[start + i] = k["pitch_angle"].strip()
    return pitches


def fill_missing(client, rows, fields):
    """Give every new row a Pitch Angle, even if the research step didn't return one."""
    todo = [r for r in rows if not str(r.get("Pitch Angle", "")).strip()]
    if not todo:
        return
    print(f"Writing {len(todo)} missing pitch angles")
    for r, p in zip(todo, write_pitches(client, [{f: r.get(f, "") for f in fields} for r in todo])):
        r["Pitch Angle"] = p


def backfill_pitches(client, ws, fields):
    """Fill Pitch Angle for older rows that are still blank (a batch each run)."""
    values = ws.get_all_values()
    if len(values) < 2 or "Pitch Angle" not in values[0]:
        return
    hdr = values[0]
    col = hdr.index("Pitch Angle")
    todo = []
    for n, row in enumerate(values[1:], start=2):
        row = row + [""] * (len(hdr) - len(row))
        name = row[hdr.index(fields[0])] if fields[0] in hdr else ""
        if name.strip() and not row[col].strip():
            todo.append((n, {f: row[hdr.index(f)] for f in fields if f in hdr}))
        if len(todo) >= BACKFILL_PER_DAY:
            break
    if not todo:
        return
    print(f"Backfilling {len(todo)} older rows missing a pitch angle")
    pitches = write_pitches(client, [d for _, d in todo])
    updates = [{"range": gspread.utils.rowcol_to_a1(n, col + 1), "values": [[safe_cell(p)]]}
               for (n, _), p in zip(todo, pitches) if p]
    if updates:
        ws.batch_update(updates, value_input_option="USER_ENTERED")


def refresh_empty_contacts(client, ws, name_col, context_cols, website_col=None):
    """Re-research older rows that were saved with no contact (e.g. API was down that day)."""
    values = ws.get_all_values()
    if len(values) < 2:
        return
    hdr = values[0]
    need = ["Contact Name", "Title", "Email", "Phone", "Contact Source"]
    if name_col not in hdr or any(c not in hdr for c in need):
        return
    todo = []
    for n, row in enumerate(values[1:], start=2):
        row = row + [""] * (len(hdr) - len(row))
        g = lambda c: row[hdr.index(c)] if c in hdr else ""
        if g(name_col).strip() and not g("Contact Name").strip() and not g("Contact Source").strip():
            ctx = ". ".join(f"{c}: {g(c)}" for c in context_cols if g(c))
            todo.append((n, g(name_col), ctx, g(website_col) if website_col else "", g("Phone")))
        if len(todo) >= REFRESH_PER_DAY:
            break
    if not todo:
        return
    print(f"Re-researching {len(todo)} older rows with no contact")
    with ThreadPoolExecutor(WORKERS) as pool:
        found = list(pool.map(lambda t: find_decision_maker(client, t[1], t[2], t[3]), todo))
    updates = []
    for (n, _, _, _, old_phone), dm in zip(todo, found):
        vals = {"Contact Name": dm.get("contact_name", ""), "Title": dm.get("title", ""),
                "Email": dm.get("email", ""), "Phone": dm.get("phone") or old_phone,
                "Contact Source": dm.get("contact_source") or "Re-researched: none published"}
        if "Pitch Angle" in hdr and dm.get("pitch_angle"):
            vals["Pitch Angle"] = dm["pitch_angle"]
        if "Fit Score" in hdr and dm.get("fit_score"):
            vals["Fit Score"] = dm["fit_score"]
        if "Why a Fit" in hdr and dm.get("why_fit"):
            vals["Why a Fit"] = dm["why_fit"]
        for col, v in vals.items():
            updates.append({"range": gspread.utils.rowcol_to_a1(n, hdr.index(col) + 1),
                            "values": [[safe_cell(v)]]})
    if updates:
        ws.batch_update(updates, value_input_option="USER_ENTERED")


SIGNAL_PITCH_FIELDS = ["Headline", "Organizer", "Venue", "Event Date", "Contact Name",
                       "Title", "Signal Type"]
COMPANY_PITCH_FIELDS = ["Company", "Category", "Area", "Contact Name", "Title", "Why a Fit",
                        "Google Rating"]


def detect_source(text):
    t = text.lower()
    for key, name in (("linkedin", "LinkedIn"), ("indeed", "Indeed"), ("google", "Google Jobs"),
                      ("glassdoor", "Glassdoor"), ("ziprecruiter", "ZipRecruiter"),
                      ("culinaryagents", "Culinary Agents"), ("culinary agents", "Culinary Agents"),
                      ("poached", "Poached")):
        if key in t:
            return name
    return "Manual"


def collect_inbox(client, ws):
    """Read everything you pasted into the Inbox tab and turn it into leads.
    Paste a whole page into one cell, or let Sheets spread it over many rows: all new rows are
    combined and read together. The agent never opens LinkedIn/Indeed pages itself."""
    if ws is None:
        return [], []
    hdr = sheet_headers(ws, INBOX_HEADERS)
    values = ws.get_all_values()
    ti, si, st = (hdr.index("Paste Listings or Links Here"), hdr.index("Source"),
                  hdr.index("Status"))
    pending = []
    for n, row in enumerate(values[1:], start=2):
        row = row + [""] * (len(hdr) - len(row))
        # join all cells in the row (a paste can spill into several columns)
        text = " ".join(c for i, c in enumerate(row)
                        if i not in (si, st, hdr.index("Processed On"),
                                     hdr.index("Leads Found"), hdr.index("Notes"))).strip()
        if text and not row[st].strip().lower().startswith("done"):
            pending.append((n, text, row[si].strip()))
    if not pending:
        print("Inbox: nothing new")
        return [], []

    # combine rows into chunks the AI can read in one go
    chunks, cur, cur_rows = [], "", []
    for n, text, src in pending:
        if cur and len(cur) + len(text) > 35000:
            chunks.append((cur, cur_rows)); cur, cur_rows = "", []
        cur += text + "\n"; cur_rows.append((n, src))
    chunks.append((cur, cur_rows))

    out, done = [], []
    for text, rows in chunks:
        source = next((src for _, src in rows if src), "") or detect_source(text)
        if len(re.sub(r"https?://\S+", "", text).strip()) < 20:
            done += [(n, 0, "Needs text: paste the listing text along with the link", source)
                     for n, _ in rows]
            continue
        reply = ask_claude(client, f"""The owner of Privenstaff (an NYC event staffing agency: servers,
bartenders, captains, event coordinators) copied this page from {source}. It may include menus,
ads, marketplace items and other clutter: ignore those.

Pull out every restaurant, venue, hotel, caterer, club, bar, hospitality group or organization
that is a real prospect for event staffing. Favor places with private events, catering,
banquets, rooftops, bars/lounges, hotels, fine dining, restaurant groups and anything marked
hiring or opening soon. SKIP: grocery stores and markets, fast-food chains, coffee
shops and bakeries with no events, and anything outside the five NYC boroughs (NJ, CT,
Long Island, Westchester). If a place is "Part of" a group, put the group name in details.

TEXT:
{text[:40000]}

Reply with ONLY a JSON array, best prospects first:
[{{"company": "", "role_or_event": "hiring for what, or opening/event", "location": "",
   "date": "", "pay": "", "url": "",
   "details": "type of place, group it belongs to, hiring now / opening soon, anything useful"}}]""",
                           max_tokens=10000, fast=True)
        items = parse_json(reply, array=True)
        found = 0
        for x in items:
            company = (x.get("company") or "").strip()
            if not company:
                continue
            found += 1
            sig = signal(f"Manual: {source}",
                         f"{company}: {x.get('role_or_event', '')}".strip(": "),
                         x.get("url") or "",
                         f"FLAGS: hand-picked by owner. PAY: {x.get('pay') or 'not posted'}. "
                         f"{x.get('location', '')}. {x.get('details', '')}",
                         x.get("date", ""), company)
            sig["id"] = make_id("inbox", company)
            sig["pay"] = x.get("pay", "")
            sig["flags"] = f"Hand-picked from {source}"
            out.append(sig)
        first = True
        for n, _ in rows:
            done.append((n, found if first else "", "Done" if found else
                         "Done: no prospects found", source))
            first = False
    for i, sig in enumerate(out):
        sig["defer"] = i >= MAX_INBOX_LEADS   # saved now, contact researched on later runs
    print(f"Inbox: {len(pending)} pasted rows, {len(out)} prospects extracted "
          f"({min(len(out), MAX_INBOX_LEADS)} researched now)")
    return out, [(n, c, status, src, hdr) for n, c, status, src in done]


def mark_inbox(ws, done):
    if not done:
        return
    updates = []
    for n, count, status, source, hdr in done:
        for col, val in (("Status", status), ("Processed On", TODAY.isoformat()),
                         ("Leads Found", count), ("Source", source)):
            updates.append({"range": gspread.utils.rowcol_to_a1(n, hdr.index(col) + 1),
                            "values": [[str(val)]]})
    ws.batch_update(updates, value_input_option="USER_ENTERED")


def run_signals(client, ws, log_ws=None, inbox_ws=None):
    hdr = sheet_headers(ws, SIGNAL_HEADERS)
    seen = column(ws.get_all_values()[1:], hdr, "Signal ID")
    raw = []
    for name, fn in [("permits", collect_permits), ("jobs", lambda: collect_jobs(log_ws)),
                     ("news", collect_news), ("web sweep", lambda: collect_scout(client))]:
        found = fn()
        print(f"Collected {len(found)} from {name}")
        raw += found
    fresh = [s for s in {s["id"]: s for s in raw}.values() if s["id"] not in seen]
    print(f"{len(fresh)} new signals to triage")
    keepers = triage(client, fresh)
    print(f"Triage kept {len(keepers)} real opportunities (researching up to {MAX_SIGNALS})")
    keepers = keepers[:MAX_SIGNALS]

    # Your hand-picked leads from the Inbox tab go first and are never filtered out
    inbox_done = []
    try:
        manual, inbox_done = collect_inbox(client, inbox_ws)
        manual = [m for m in {m["id"]: m for m in manual}.values() if m["id"] not in seen]
        if manual:
            scored = {m["id"]: m for m in triage(client, manual, keep_all=True)}
            # Your pasted leads are NEVER dropped: anything the AI didn't score gets defaults
            manual_keep = [scored.get(m["id"]) or {**m, "organizer": m.get("company", ""),
                                                   "urgency": "Medium", "fit_score": 6}
                           for m in manual]
            print(f"Inbox: {len(manual_keep)} pasted leads going to Signals")
            keepers = manual_keep + keepers
    except OutOfCredits:
        raise
    except Exception as e:
        print(f"  Inbox skipped: {e}")

    picked, seen_orgs = [], set()
    for s in keepers:
        org = s.get("organizer") or s.get("company") or s["headline"]
        if org.lower() in seen_orgs:
            continue
        seen_orgs.add(org.lower())
        picked.append((org, s))

    def research(item):
        org, s = item
        if s.get("defer"):
            return {}   # saved now; the re-research step fills the contact on later runs
        if CREDITS["out"]:
            return None
        print(f"  Going to the source: {org}")
        try:
            return find_decision_maker(client, org, f"{s['type']}: {s['headline']}. {s['details']}")
        except OutOfCredits:
            return None   # not researched: left out today, picked up again next run

    with ThreadPoolExecutor(WORKERS) as pool:
        results = list(pool.map(research, picked))

    rows = []
    for (org, s), dm in zip(picked, results):
        if dm is None:
            continue
        rows.append({
            "Date Found": TODAY.isoformat(), "Signal Type": s["type"],
            "Headline": s["headline"], "Event Date": s.get("event_date", ""),
            "Organizer": org, "Venue": s.get("venue", ""),
            "Contact Name": dm.get("contact_name", ""), "Title": dm.get("title", ""),
            "Email": dm.get("email", ""), "Phone": dm.get("phone", ""),
            "Contact Source": dm.get("contact_source", ""),
            "Alt Contact": dm.get("alt_contact", ""), "Urgency": s.get("urgency", ""),
            "Fit Score": s.get("fit_score", ""), "Pitch Angle": s.get("pitch_angle", ""),
            "Signal URL": s["url"], "Status": "New", "Signal ID": s["id"],
            "Hiring Flags": s.get("flags", ""), "Pay Posted": s.get("pay", "")})
    if rows:
        if not CREDITS["out"]:
            try:
                fill_missing(client, rows, SIGNAL_PITCH_FIELDS if "Signal ID" in hdr
                             else COMPANY_PITCH_FIELDS)
            except OutOfCredits:
                pass
        ws.append_rows([[safe_cell(r.get(h, "")) for h in hdr] for r in rows],
                       value_input_option="USER_ENTERED")
    try:
        if not CREDITS["out"]:   # if credits ran out, the paste is retried next run
            mark_inbox(inbox_ws, inbox_done)   # only after the leads are safely saved
    except Exception as e:
        print(f"  Could not mark Inbox rows: {e}")
    return rows


def run_companies(client, ws):
    hdr = sheet_headers(ws, COMPANY_HEADERS)
    existing = ws.get_all_values()[1:]
    seen_ids = column(existing, hdr, "Place ID")
    seen_domains = {domain_of(d) for d in column(existing, hdr, "Website")}
    combos = rotate([(c, a) for c in CATEGORIES for a in AREAS], QUERIES_PER_DAY)
    rows, candidates = [], []
    for category, area in combos:
        try:
            places = places_search(f"{category} in {area}")
        except Exception as e:
            print(f"  Places failed: {e}")
            continue
        taken = 0
        for p in places:
            if len(candidates) >= MAX_NEW_LEADS or taken >= PER_SEARCH_CAP:
                break
            if ", NY " not in p.get("formattedAddress", ""):
                continue  # keep New York addresses only
            pid, website = p.get("id"), p.get("websiteUri", "")
            dom = domain_of(website)
            if pid in seen_ids or (dom and dom in seen_domains):
                continue
            candidates.append((category, area, p, website))
            taken += 1
            seen_ids.add(pid)
            if dom:
                seen_domains.add(dom)

    def research(item):
        category, area, p, website = item
        company = p.get("displayName", {}).get("text", "")
        if CREDITS["out"]:
            return None
        print(f"  Researching company: {company}")
        try:
            return find_decision_maker(client, company, f"{category} in {area}", website)
        except OutOfCredits:
            return None

    with ThreadPoolExecutor(WORKERS) as pool:
        results = list(pool.map(research, candidates))

    for (category, area, p, website), dm in zip(candidates, results):
        if dm is None:
            continue
        company = p.get("displayName", {}).get("text", "")
        pid = p.get("id")
        rows.append({
            "Date Found": TODAY.isoformat(), "Company": company, "Category": category,
            "Area": area, "Contact Name": dm.get("contact_name", ""),
            "Title": dm.get("title", ""), "Email": dm.get("email", ""),
            "Phone": dm.get("phone") or p.get("nationalPhoneNumber", ""),
            "Contact Source": dm.get("contact_source", ""), "Website": website,
            "Address": p.get("formattedAddress", ""), "Google Rating": p.get("rating", ""),
            "Fit Score": dm.get("fit_score", ""), "Why a Fit": dm.get("why_fit", ""),
            "Pitch Angle": dm.get("pitch_angle", ""), "Place ID": pid, "Status": "New"})
    rows.sort(key=lambda r: -int(r["Fit Score"]) if str(r["Fit Score"]).isdigit() else 0)
    if rows:
        if not CREDITS["out"]:
            try:
                fill_missing(client, rows, SIGNAL_PITCH_FIELDS if "Signal ID" in hdr
                             else COMPANY_PITCH_FIELDS)
            except OutOfCredits:
                pass
        ws.append_rows([[safe_cell(r.get(h, "")) for h in hdr] for r in rows],
                       value_input_option="USER_ENTERED")
    return rows


# ======================= TEXT ENGINE =======================
# Every day: (1) finds missing phone numbers for leads (Google Places), (2) picks the best
# leads with a phone that were never texted (Signals first, then companies), (3) writes a short,
# specific text pitch for each, (4) saves MassText-format batches and marks the leads as texted.

def norm_phone(value):
    """10-digit US number from any format, or ''."""
    m = PHONE_RE.search(str(value or ""))
    if not m:
        return ""
    digits = re.sub(r"\D", "", re.split(r"(?i)x|ext", m.group(0))[0])
    if len(digits) == 11 and digits.startswith("1"):
        digits = digits[1:]
    return digits if len(digits) == 10 and digits[0] not in "01" else ""


def show_phone(d):
    return f"({d[:3]}) {d[3:6]}-{d[6:]}"


def places_lookup(query):
    """One quick Google Places search; returns (name, phone) of the best match or ("", "")."""
    try:
        r = requests.post("https://places.googleapis.com/v1/places:searchText", timeout=30,
                          headers={"Content-Type": "application/json",
                                   "X-Goog-Api-Key": os.environ["GOOGLE_PLACES_API_KEY"],
                                   "X-Goog-FieldMask": "places.displayName,places.nationalPhoneNumber,"
                                                       "places.formattedAddress"},
                          json={"textQuery": query, "pageSize": 3})
        for p in r.json().get("places", []):
            phone = p.get("nationalPhoneNumber", "")
            if phone and ", NY " in p.get("formattedAddress", ""):
                return p.get("displayName", {}).get("text", ""), phone
    except Exception as e:
        print(f"  Phone lookup failed ({query[:40]}): {e}")
    return "", ""


def _words(text):
    stop = {"the", "of", "and", "nyc", "new", "york", "inc", "llc", "group", "events", "event",
            "hotel", "restaurant", "at", "&", "-", "co", "company"}
    return {w for w in re.findall(r"[a-z0-9]+", (text or "").lower()) if w not in stop and len(w) > 2}


def enrich_phones(sources, budget):
    """Fill in missing phone numbers (a few each day) with Google Places. Each row is only
    checked once ("Phone Checked" column)."""
    if not os.getenv("GOOGLE_PLACES_API_KEY") or budget <= 0:
        return 0
    found = 0
    for ws, name_col, extra_col in sources:
        if budget <= 0:
            break
        hdr = sheet_headers(ws, SIGNAL_HEADERS if name_col == "Organizer" else COMPANY_HEADERS)
        values = ws.get_all_values()
        updates = []
        for n, r in enumerate(values[1:], start=2):
            if budget <= 0:
                break
            r = r + [""] * (len(hdr) - len(r))
            g = lambda c: r[hdr.index(c)].strip() if c in hdr else ""
            name = g(name_col)
            if not name or norm_phone(g("Phone")) or g("Phone Checked"):
                continue
            budget -= 1
            got_name, phone = places_lookup(f"{name} {g(extra_col)} New York".strip())
            ok = phone and (_words(name) & _words(got_name))     # must be the same business
            if ok:
                found += 1
                updates.append({"range": gspread.utils.rowcol_to_a1(n, hdr.index("Phone") + 1),
                                "values": [[safe_cell(phone)]]})
            updates.append({"range": gspread.utils.rowcol_to_a1(n, hdr.index("Phone Checked") + 1),
                            "values": [[f"{TODAY.isoformat()} {'found' if ok else 'none'}"]]})
        if updates:
            ws.batch_update(updates, value_input_option="USER_ENTERED")
    print(f"Phone finder: {found} new phone numbers found")
    return found


def write_text_pitches(client, items):
    """Short, specific text-message pitches (one sentence, about 150 characters)."""
    out = [""] * len(items)
    if client is None or CREDITS["out"]:
        return out
    for start in range(0, len(items), 25):
        batch = items[start:start + 25]
        listing = "\n".join(f"{i}. " + json.dumps(x, ensure_ascii=False) for i, x in enumerate(batch))
        try:
            text = ask_claude(client, f"""Write ONE short text-message pitch for each lead below, for
Privenstaff, an NYC event staffing company (servers, bartenders, captains, event coordinators).
Rules: one sentence, max 150 characters, plain and friendly, specific to the lead (their event,
venue, hiring post, opening or season), starts with "Privenstaff can" or similar, no greeting,
no name, no sign-off, no emojis, no links, no invented facts.

{listing}

Reply with ONLY a JSON array: [{{"i": 0, "sms": ""}}]""", max_tokens=6000, fast=True)
        except OutOfCredits:
            break
        for k in parse_json(text, array=True):
            i = k.get("i")
            if isinstance(i, int) and 0 <= i < len(batch) and k.get("sms"):
                out[start + i] = k["sms"].strip()
    return out


def short_pitch(text, limit=170):
    text = re.sub(r"\s+", " ", str(text or "")).strip()
    if len(text) <= limit:
        return text
    cut = text[:limit]
    return (cut[:cut.rfind(".") + 1] if "." in cut[40:] else cut.rsplit(" ", 1)[0] + ".").strip()


def build_texts(client, sources, texts_ws, dnt_ws, queue_ws=None):
    """Pick today's text contacts across Signals and Companies and save MassText batches.
    Leads emailed in the last 3 days go first, and their text mentions the email."""
    if texts_ws is None:
        return []
    emailed = set()
    if queue_ws is not None:
        try:
            qv = queue_ws.get_all_values()
            qh = qv[0]
            since = (TODAY - datetime.timedelta(days=3)).isoformat()
            for r in qv[1:]:
                r = r + [""] * (len(qh) - len(r))
                if r[qh.index("Sent On")][:10] >= since and not r[qh.index("Reply Status")]:
                    emailed.add(r[qh.index("Email")].strip().lower())
        except Exception as e:
            print(f"  Email/text link skipped: {e}")
    sheet_headers(texts_ws, TEXT_BATCH_HEADERS)
    blocked = set()
    if dnt_ws is not None:
        try:
            sheet_headers(dnt_ws, DNT_HEADERS)
            blocked = {norm_phone(r[0]) for r in dnt_ws.get_all_values()[1:] if r}
        except Exception as e:
            print(f"  Do Not Text list skipped: {e}")
    cutoff = (TODAY - datetime.timedelta(days=TEXT_AGAIN_DAYS)).isoformat()
    urgency = {"high": 0, "medium": 1, "low": 2}
    stop_words = ("do not", "stop", "not interested", "unsubscribed", "wrong number", "booked")
    cands, recent = [], set()
    for prio, (ws, name_col) in enumerate(sources):
        hdr = sheet_headers(ws, SIGNAL_HEADERS if name_col == "Organizer" else COMPANY_HEADERS)
        for n, r in enumerate(ws.get_all_values()[1:], start=2):
            r = r + [""] * (len(hdr) - len(r))
            g = lambda c: r[hdr.index(c)].strip() if c in hdr else ""
            ph = norm_phone(g("Phone"))
            if not ph:
                continue
            if g("Texted On"):
                if g("Texted On")[:10] >= cutoff:
                    recent.add(ph)
                continue
            if any(w in g("Status").lower() for w in stop_words):
                continue
            fit = int(g("Fit Score")) if g("Fit Score").isdigit() else 5
            was_emailed = g("Email").lower() in emailed
            cands.append({"ws": ws, "hdr": hdr, "row": n, "phone": ph,
                          "prio": -1 if was_emailed else prio, "emailed": was_emailed,
                          "urg": urgency.get(g("Urgency").lower(), 1), "fit": fit,
                          "date": g("Date Found"), "contact": g("Contact Name"),
                          "company": g(name_col), "pitch": g("Pitch Angle"),
                          "about": " | ".join(x for x in (g("Headline"), g("Signal Type"), g("Category"),
                                                          g("Venue"), g("Event Date"), g("Why a Fit")) if x)})
    cands.sort(key=lambda c: (c["prio"], c["urg"], -c["fit"], c["date"]), reverse=False)
    picked, seen = [], set(blocked) | recent
    for c in cands:
        if c["phone"] in seen:
            continue
        seen.add(c["phone"])
        picked.append(c)
        if len(picked) >= TEXTS_PER_DAY:
            break
    if not picked:
        print("Text engine: no new contacts with a phone today")
        return []
    sms = write_text_pitches(client, [{"company": c["company"], "contact": c["contact"],
                                       "about": c["about"][:300], "pitch_angle": c["pitch"][:300]}
                                      for c in picked])
    entries = []
    for c, p in zip(picked, sms):
        pitch = p or short_pitch(c["pitch"]) or \
            "Privenstaff can supply servers, bartenders and captains for your events on short notice."
        if not pitch.endswith((".", "!", "?")):
            pitch += "."
        if c.get("emailed"):
            pitch += " I also just sent you an email."
        who = c["contact"] if first_name(c["contact"]) else (clean_company(c["company"]) or c["contact"])
        msg = f"How much staff do you need? {pitch} {TEXT_SIGNOFF}"
        if TEXT_STOP_LINE:
            msg += " Reply STOP to opt out."
        entries.append(f"{who}\n{show_phone(c['phone'])}\n\n{msg}")
    chunks = [entries[i:i + TEXT_BATCH_SIZE] for i in range(0, len(entries), TEXT_BATCH_SIZE)]
    for i, chunk in reversed(list(enumerate(chunks))):     # part 1 ends up on top (row 2)
        part = f" (part {i + 1} of {len(chunks)})" if len(chunks) > 1 else ""
        texts_ws.insert_row([TODAY.isoformat() + part, len(chunk), "\n\n".join(chunk), ""], index=2,
                            value_input_option="RAW")
    # mark the leads as texted so they are never picked again
    by_ws = {}
    for c in picked:
        by_ws.setdefault(id(c["ws"]), (c["ws"], []))[1].append(
            {"range": gspread.utils.rowcol_to_a1(c["row"], c["hdr"].index("Texted On") + 1),
             "values": [[TODAY.isoformat()]]})
    for ws, ups in by_ws.values():
        ws.batch_update(ups, value_input_option="RAW")
    print(f"Text engine: {len(picked)} contacts in {len(chunks)} batch(es) "
          f"({sum(1 for c in picked if c.get('emailed'))} just emailed, "
          f"{sum(1 for c in picked if c['prio'] == 0)} from Signals, "
          f"{sum(1 for c in picked if c['prio'] == 1)} from companies)")
    return [(len(ch), "\n\n".join(ch)) for ch in chunks]


# ======================= EMAIL FINDER =======================

EMAIL_FIND_RE = re.compile(r"[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}", re.I)


def _fetch(url):
    try:
        r = requests.get(url, timeout=12, allow_redirects=True,
                         headers={"User-Agent": "Mozilla/5.0 (compatible; PrivenstaffBot/1.0)"})
        if r.status_code == 200 and "text/html" in r.headers.get("content-type", "text/html"):
            return r.text[:600000]
    except Exception:
        pass
    return ""


def _email_rank(em, site):
    local, dom = em.split("@", 1)
    score = 0
    if site and (dom == site or dom.endswith("." + site) or site.endswith(dom)):
        score += 10                                   # their own domain
    if any(local.startswith(g) for g in GOOD_INBOXES):
        score += 6                                    # events@, catering@, sales@ ...
    elif re.match(r"^[a-z]+([._-][a-z]+)?$", local) and local not in ("info", "hello", "contact",
                                                                      "office", "admin", "team"):
        score += 8                                    # looks like a person (maria@, j.smith@)
    elif local in ("info", "hello", "contact", "office", "team"):
        score += 3
    return score


def site_emails(url):
    """Published emails on a company's site: home page + contact/about/events pages."""
    if not url:
        return []
    if not url.startswith("http"):
        url = "https://" + url
    site = domain_of(url)
    if not site or any(b in site for b in SKIP_SITES):
        return []
    root = f"https://{site}"
    home = _fetch(url) or _fetch(root)
    if not home:
        return []
    pages = [home]
    links = re.findall(r'href=["\']([^"\'#]+)["\']', home, re.I)
    wanted = [l for l in links if re.search(r"contact|about|event|private|catering|book|team|"
                                            r"inquir|wedding|party", l, re.I)]
    seen = set()
    for l in wanted:
        full = l if l.startswith("http") else root + ("" if l.startswith("/") else "/") + l
        if domain_of(full) != site or full in seen:
            continue
        seen.add(full)
        html = _fetch(full)
        if html:
            pages.append(html)
        if len(seen) >= 4:
            break
    text = " ".join(pages)
    text = re.sub(r"\s*(\[at\]|\(at\)|\{at\})\s*", "@", text, flags=re.I)
    text = re.sub(r"\s*(\[dot\]|\(dot\))\s*", ".", text, flags=re.I)
    found = {e.lower().strip(".") for e in EMAIL_FIND_RE.findall(text)}
    found = [e for e in found if not any(b in e for b in BAD_EMAIL_BITS) and EMAIL_RE.match(e)]
    return sorted(found, key=lambda e: -_email_rank(e, site))


def find_emails(sources, budget):
    """Fill in missing emails from company websites (free). Each row is checked once."""
    if budget <= 0:
        return 0
    total = 0
    for ws, name_col, site_cols, defaults in sources:
        if budget <= 0:
            break
        hdr = sheet_headers(ws, defaults)
        values = ws.get_all_values()
        todo = []
        for n, r in enumerate(values[1:], start=2):
            r = r + [""] * (len(hdr) - len(r))
            g = lambda c: r[hdr.index(c)].strip() if c in hdr else ""
            if not g(name_col) or EMAIL_RE.match(g("Email")) or g("Email Checked"):
                continue
            url = next((g(c) for c in site_cols if g(c).startswith("http") and
                        not any(b in domain_of(g(c)) for b in SKIP_SITES)), "")
            if not url:
                continue
            todo.append((n, url))
            if len(todo) >= budget:
                break
        if not todo:
            continue
        budget -= len(todo)
        with ThreadPoolExecutor(8) as pool:
            results = list(pool.map(lambda t: site_emails(t[1]), todo))
        updates = []
        for (n, url), ems in zip(todo, results):
            if ems:
                total += 1
                updates.append({"range": gspread.utils.rowcol_to_a1(n, hdr.index("Email") + 1),
                                "values": [[ems[0]]]})
            updates.append({"range": gspread.utils.rowcol_to_a1(n, hdr.index("Email Checked") + 1),
                            "values": [[f"{TODAY.isoformat()} {'found on ' + domain_of(url) if ems else 'none'}"]]})
        ws.batch_update(updates, value_input_option="RAW")
    print(f"Email finder: {total} new email addresses found on company websites")
    return total


# ======================= SEGMENTS + SUBJECT VARIANTS =======================

SEGMENT_ANGLES = {
    "Venue": "They host events in their own space: offer extra servers and bartenders for busy "
             "nights and big buyouts, so their regular team is never stretched.",
    "Hotel": "Hotel banquets and private events: offer trained banquet servers and captains to "
             "backfill on peak dates and large functions.",
    "Caterer": "Caterers staff every event: offer a reliable on-call bench of servers, bartenders "
               "and captains for overflow and last-minute bookings.",
    "Planner": "Planners book vendors for clients: offer one call that staffs every event, so "
               "staffing is one less vendor to chase.",
    "Hiring": "They are hiring event roles right now: offer to cover their events while they "
              "fill the positions, booking staff only for the nights they need.",
    "Event": "They have an upcoming event (gala, conference, launch, party): offer polished "
             "servers, bartenders and captains for that specific event.",
    "Other": "Offer reliable event staff (servers, bartenders, captains) on short notice.",
}


def segment_of(*texts):
    t = " ".join(x or "" for x in texts).lower()
    if any(w in t for w in ("hiring", "job", "top event hirer")):
        return "Hiring"
    if any(w in t for w in ("hotel", "banquet hall", "ballroom")):
        return "Hotel"
    if any(w in t for w in ("cater",)):
        return "Caterer"
    if any(w in t for w in ("planner", "planning", "event management", "production")):
        return "Planner"
    if any(w in t for w in ("gala", "benefit", "conference", "summit", "launch", "premiere",
                            "fundraiser", "festival", "expo", "permit", "news", "web intelligence",
                            "party", "show")):
        return "Event"
    if any(w in t for w in ("venue", "rooftop", "restaurant", "club", "loft", "space", "bar",
                            "lounge", "private dining")):
        return "Venue"
    return "Other"


VARIANT_STYLES = {
    "A": "Subject: short and specific to them (e.g. 'Staff for your December gala').",
    "B": "Subject: a short question (e.g. 'Need extra servers this season?').",
}


def variant_winner(queue_ws):
    """After enough sends, the subject style with the better reply rate wins more often."""
    try:
        values = queue_ws.get_all_values()
        hdr = values[0]
        if "Variant" not in hdr:
            return None
        stats = {"A": [0, 0], "B": [0, 0]}
        for r in values[1:]:
            r = r + [""] * (len(hdr) - len(r))
            v = r[hdr.index("Variant")]
            if v in stats and r[hdr.index("Sent On")]:
                stats[v][0] += 1
                if r[hdr.index("Reply Status")].lower().startswith(("replied", "booked")):
                    stats[v][1] += 1
        if min(stats["A"][0], stats["B"][0]) < 40:
            return None
        ra, rb = (stats[v][1] / stats[v][0] for v in "AB")
        if max(ra, rb) >= 1.3 * max(min(ra, rb), 0.001):
            return "A" if ra > rb else "B"
    except Exception:
        pass
    return None


def pick_variant(email, winner):
    h = int(hashlib.md5(email.lower().encode()).hexdigest(), 16) % 100
    if winner:
        return winner if h < 80 else ("B" if winner == "A" else "A")
    return "A" if h < 50 else "B"


SPAM_WORDS = {"free": "complimentary", "guarantee": "promise", "guaranteed": "dependable",
              "act now": "", "limited time": "", "urgent": "timely", "100%": "fully",
              "click here": "", "risk-free": "", "no obligation": "", "winner": "",
              "cash": "", "cheap": "affordable", "best price": "great rates", "$$$": ""}


def clean_spam(text):
    """Remove words that push emails into spam folders; no exclamation marks."""
    t = text.replace("!", ".")
    for bad, good in SPAM_WORDS.items():
        t = re.sub(rf"\b{re.escape(bad)}\b", good, t, flags=re.I)
    t = re.sub(r"[ \t]{2,}", " ", t)
    t = re.sub(r"\s+([,.])", r"\1", t)              # no space before punctuation
    t = re.sub(r",\s*\.", ".", t)                     # ", ." left by a removed phrase
    return re.sub(r"\.\.+", ".", t).strip()


def text_batches(rows):
    """Build MassText-format batches (Name / Phone / message) from new Signals rows.
    Returns a list of (count, text) chunks, each small enough for one Sheets cell."""
    entries = []
    for r in rows:
        m = PHONE_RE.search(str(r.get("Phone", "")))
        if not m:
            continue
        contact = str(r.get("Contact Name", "")).strip()
        name = contact if first_name(contact) else (str(r.get("Organizer", "")).strip() or contact)
        if not name:
            continue
        pitch = str(r.get("Pitch Angle", "")).strip() or \
            "Privenstaff can supply servers, bartenders and captains for your events on short notice."
        if not pitch.endswith((".", "!", "?")):
            pitch += "."
        entries.append(f"{name}\n{m.group(0).strip()}\n\nHow much staff do you need? {pitch} "
                       f"{TEXT_SIGNOFF}")
    chunks, cur, n = [], "", 0
    for e in entries:
        if cur and len(cur) + len(e) > 40000:
            chunks.append((n, cur.strip())); cur, n = "", 0
        cur += e + "\n\n"; n += 1
    if cur:
        chunks.append((n, cur.strip()))
    return chunks


def save_text_batches(ws, rows):
    if ws is None:
        return []
    sheet_headers(ws, TEXT_BATCH_HEADERS)
    chunks = text_batches(rows)
    for i, (n, text) in enumerate(reversed(chunks)):   # newest batch on top (row 2)
        part = f" (part {len(chunks) - i} of {len(chunks)})" if len(chunks) > 1 else ""
        ws.insert_row([TODAY.isoformat() + part, n, text, ""], index=2,
                      value_input_option="RAW")
    print(f"Text batch: {sum(n for n, _ in chunks)} contacts with phone numbers")
    return chunks


NY_TZ = ZoneInfo("America/New_York")


def ny_now():
    return datetime.datetime.now(NY_TZ)


def parse_send_at(value):
    """Read the 'Send At' cell (New York time). Accepts e.g. 10/6/2026 9:30 AM,
    10/6/2026 14:00, 2026-10-06 09:30, or just a date (= 9:00 AM that day).
    Returns a datetime, None if empty, or False if it can't be understood."""
    v = re.sub(r"\s+", " ", str(value or "").strip().upper())
    if not v:
        return None
    v = re.sub(r"\s*(AM|PM)$", r" \1", v)
    for fmt in ("%m/%d/%Y %I:%M %p", "%m/%d/%Y %I:%M:%S %p", "%m/%d/%Y %H:%M", "%m/%d/%Y %H:%M:%S",
                "%m/%d/%y %I:%M %p", "%m/%d/%y %H:%M", "%Y-%m-%d %I:%M %p", "%Y-%m-%d %H:%M",
                "%Y-%m-%d %H:%M:%S", "%m/%d/%Y %I %p", "%Y-%m-%d %I %p"):
        try:
            return datetime.datetime.strptime(v, fmt).replace(tzinfo=NY_TZ)
        except ValueError:
            pass
    for fmt in ("%m/%d/%Y", "%m/%d/%y", "%Y-%m-%d"):
        try:
            return datetime.datetime.strptime(v, fmt).replace(hour=9, tzinfo=NY_TZ)
        except ValueError:
            pass
    return False


def ensure_send_at_column(ws):
    """Add the 'Send At' column right next to 'Approve' on older Email Queue tabs."""
    hdr = ws.row_values(1)
    if hdr and "Send At" not in hdr:
        pos = hdr.index("Approve") + 2 if "Approve" in hdr else 2
        ws.insert_cols([["Send At"]], col=pos)


def first_name(name):
    name = (name or "").strip()
    if not name or any(w in name.lower() for w in ("not ", "team", "publicly", "unknown", "(")):
        return ""
    first = re.split(r"[\s/]+", name)[0]
    return first if first.isalpha() and len(first) > 1 else ""


def clean_company(name):
    """A usable company name, or '' (blank, an email address, or 'not found'-style text)."""
    name = (name or "").strip()
    bad = ("not ", "n/a", "unknown", "none", "@", "publicly")
    return "" if (not name or any(w in name.lower() for w in bad)) else name


def _greeting(contact, company):
    fn, co = first_name(contact), clean_company(company)
    return f"Hi {fn}," if fn else (f"Hello {co} team," if co else "Hello,")


FOLLOWUP_HOOKS = {
    "Venue": "We can send extra servers and bartenders for your busiest nights and buyouts",
    "Hotel": "We can backfill banquet servers and captains for your peak dates",
    "Caterer": "We can be your on-call bench for overflow and last-minute events",
    "Planner": "One call to us staffs your client events, start to finish",
    "Hiring": "We can cover your events while you fill those open roles",
    "Event": "We still have trained servers, bartenders and captains available for your event",
    "Other": "We have trained servers, bartenders and captains available on short notice",
}


def followup_body(contact, company, segment="Other"):
    """Step 2 (a few days after the first email): short, with a concrete hook."""
    co = clean_company(company)
    about = f"event staffing for {co}" if co else "event staffing for your upcoming events"
    hook = FOLLOWUP_HOOKS.get(segment, FOLLOWUP_HOOKS["Other"])
    return (f"{_greeting(contact, company)}\n\nJust following up on my note about {about}. "
            f"{hook}, at rates below the big agencies. I'd be glad to send a quick rate sheet "
            f"or jump on a 10-minute call. Would that help?")


def final_body(contact, company):
    """Step 3 (about 10 days after the first email): polite close-the-loop note."""
    co = clean_company(company)
    who = f"at {co} " if co else ""
    return (f"{_greeting(contact, company)}\n\nI don't want to keep filling your inbox, so this "
            f"is my last note. If someone else {who}handles event staffing, could you point me "
            f"to them? And if the timing just isn't right, no problem at all: we're here whenever "
            f"you need servers, bartenders or captains on short notice.")


def signature():
    addr = os.getenv("BUSINESS_ADDRESS", "").strip()
    return (f"\n\nBest regards,\n{SENDER_NAME}\n{SENDER_TITLE}\nP. {SENDER_PHONE} | {SENDER_SITE}"
            f"\n\n--\nPrivenstaff | {addr}\nReply \"Unsubscribe\" to opt out.")


def draft_batch(client, items):
    """items: list of dicts with lead details. Returns [(subject, body)] in the same order."""
    out = [("", "")] * len(items)
    for start in range(0, len(items), 10):
        batch = items[start:start + 10]
        listing = "\n".join(f"{i}. " + json.dumps(d, ensure_ascii=False)
                            for i, d in enumerate(batch))
        text = ask_claude(client, f"""Write a short cold outreach email from {SENDER_NAME}, owner of
Privenstaff, an NYC event staffing company (servers, bartenders, captains, event coordinators),
to each lead below. Rules:
- Greet by first_name if given ("Hi Maria,"), otherwise "Hello {{company}} team,".
- 3 to 5 short sentences, plain and friendly, no hype, no exclamation marks.
- Build it around the lead's pitch angle / details (their event, hiring post, venue, season).
- Use the lead's "angle" (their type of business) as the main idea of the email.
- Say Privenstaff provides great staff at rates lower than larger established agencies.
- End by asking for a quick call.
- Do NOT add a sign-off, name, phone or signature (added automatically). No placeholders.
- Avoid spam-trigger words (free, guarantee, urgent, act now, limited time, cash, click here).
- Subject: under 8 words, no clickbait, following the lead's "subject_style".

{listing}

Reply with ONLY a JSON array: [{{"i": 0, "subject": "", "body": ""}}]""", max_tokens=6000, fast=True)
        for k in parse_json(text, array=True):
            i = k.get("i")
            if isinstance(i, int) and 0 <= i < len(batch) and k.get("body"):
                out[start + i] = (clean_spam(k.get("subject", "").strip()),
                                  clean_spam(k["body"].strip()))
    return out


def process_email_drop(client, drop_ws, queue_ws):
    """Clean emails you dropped in the 'Email Drop' tab, write a Privenstaff message for each,
    and add them to the Email Queue (not approved). Uses the cheap model, no web search."""
    dhdr = sheet_headers(drop_ws, DROP_HEADERS)
    qhdr = sheet_headers(queue_ws, QUEUE_HEADERS)
    ei = qhdr.index("Email")
    queued = {r[ei].strip().lower() for r in queue_ws.get_all_values()[1:] if len(r) > ei}
    todo, marks, seen_now = [], [], set()
    for n, r in enumerate(drop_ws.get_all_values()[1:], start=2):
        r = r + [""] * (len(dhdr) - len(r))
        g = lambda c: r[dhdr.index(c)].strip()
        raw = g("Email")
        if not raw or g("Status").lower().startswith(("added", "duplicate", "invalid")):
            continue
        m = re.search(r"[^@\s<>,;()\[\]]+@[^@\s<>,;()\[\]]+\.[a-z]{2,}", raw.replace("[at]", "@"), re.I)
        em = m.group(0) if m else ""
        if not EMAIL_RE.match(em):
            marks.append((n, "Invalid email"))
            continue
        if em.lower() in queued or em.lower() in seen_now:
            marks.append((n, "Duplicate: already in Email Queue"))
            continue
        if len(todo) >= DROP_PER_RUN:
            continue   # the rest wait for the next hourly run
        seen_now.add(em.lower())
        todo.append((n, {"email": em, "name": g("Name"), "company": g("Company"),
                         "message_or_notes": g("Message or Notes"), "source": g("Source")}))
    written = []
    for start in range(0, len(todo), 15):
        batch = todo[start:start + 15]
        listing = "\n".join(f"{i}. " + json.dumps(d, ensure_ascii=False)
                            for i, (_, d) in enumerate(batch))
        text = ask_claude(client, f"""Write a short outreach email for Privenstaff, an NYC event staffing
company (servers, bartenders, captains, event coordinators), to each lead below.
Body format, exactly:
"<greeting> do you still need staff? <1-2 sentences in Privenstaff's voice, e.g. 'Privenstaff can...',
tailored to the lead> {DROP_SIGNOFF}"
- Greeting: "Hi <first name>," if a real person's name is given, otherwise "Hello <company> team,".
- If message_or_notes contains a message or details, keep its specifics (event, dates, roles) but
  rewrite it cleanly in this format. Fix grammar. No exclamation marks, no invented facts.
- Subject: under 8 words, specific to them.

{listing}

Reply with ONLY a JSON array: [{{"i": 0, "subject": "", "body": ""}}]""", max_tokens=8000, fast=True)
        got = {k.get("i"): k for k in parse_json(text, array=True)}
        for i, (n, d) in enumerate(batch):
            k = got.get(i) or {}
            if not k.get("body"):
                continue   # left as-is; retried next run
            written.append((n, d, k.get("subject", "").strip(), k["body"].strip()))
    if written:
        queue_ws.append_rows([[safe_cell({
            "Date Added": TODAY.isoformat(), "Company": d["company"], "Contact Name": d["name"],
            "Email": d["email"], "Email Subject": subj, "Email Body": body,
            "Lead Type": d["source"] or "Email Drop", "Source Tab": "Email Drop"}.get(h, ""))
            for h in qhdr] for _, d, subj, body in written], value_input_option="RAW")
        marks += [(n, "Added to Email Queue") for n, _, _, _ in written]
    if marks:
        si, pi = dhdr.index("Status") + 1, dhdr.index("Processed On") + 1
        drop_ws.batch_update(
            [{"range": gspread.utils.rowcol_to_a1(n, si), "values": [[st]]} for n, st in marks] +
            [{"range": gspread.utils.rowcol_to_a1(n, pi), "values": [[TODAY.isoformat()]]}
             for n, _ in marks])
    print(f"Email Drop: {len(written)} added to Email Queue, "
          f"{sum(1 for _, st in marks if st != 'Added to Email Queue')} skipped")


def queue_emails(client, sources, queue_ws):
    """Fill the Email Queue tab: one row per lead with an email address, with a ready
    draft. Old drafts/sent dates already sitting in Signals/Companies are carried over."""
    qhdr = sheet_headers(queue_ws, QUEUE_HEADERS)
    ei = qhdr.index("Email")
    queued = {r[ei].strip().lower() for r in queue_ws.get_all_values()[1:] if len(r) > ei}
    new = []
    for ws, tab in sources:
        values = ws.get_all_values()
        if len(values) < 2 or "Email" not in values[0]:
            continue
        hdr = values[0]
        for r in values[1:]:
            g = lambda c: r[hdr.index(c)].strip() if c in hdr and hdr.index(c) < len(r) else ""
            em = g("Email")
            if not EMAIL_RE.match(em) or em.lower() in queued:
                continue
            queued.add(em.lower())
            new.append({
                "Date Added": TODAY.isoformat(), "Company": g("Company") or g("Organizer"),
                "Contact Name": g("Contact Name"), "Title": g("Title"), "Email": em,
                "Fit Score": g("Fit Score"), "Email Subject": g("Email Subject"),
                "Email Body": g("Email Body"), "Approve": g("Approve"), "Sent On": g("Sent On"),
                "Follow-up Sent On": g("Follow-up Sent On"), "Reply Status": g("Reply Status"),
                "Lead Type": g("Signal Type") or g("Category"), "Pitch Angle": g("Pitch Angle"),
                "Source Tab": tab,
                "_ctx": {c: g(c) for c in ("Headline", "Category", "Signal Type", "Event Date",
                                            "Venue", "Hiring Flags", "Pay Posted", "Why a Fit",
                                            "Pitch Angle") if g(c)}})
    winner = variant_winner(queue_ws)
    for x in new:
        x["Segment"] = segment_of(x["Lead Type"], x["_ctx"].get("Headline", ""),
                                  x["_ctx"].get("Hiring Flags", ""), x["Company"])
        x["Variant"] = pick_variant(x["Email"], winner)
    need = [x for x in new if not x["Email Body"] and not x["Sent On"]][:DRAFTS_PER_DAY]
    stopped = False
    if need:
        print(f"Drafting {len(need)} outreach emails for the Email Queue"
              + (f" (subject style {winner} is winning)" if winner else ""))
        try:
            drafts = draft_batch(client, [{"company": x["Company"],
                                           "first_name": first_name(x["Contact Name"]),
                                           "title": x["Title"],
                                           "angle": SEGMENT_ANGLES[x["Segment"]],
                                           "subject_style": VARIANT_STYLES[x["Variant"]],
                                           **x["_ctx"]} for x in need])
            for x, (subj, body) in zip(need, drafts):
                x["Email Subject"], x["Email Body"] = subj, body
        except OutOfCredits:
            stopped = True
    ready = [x for x in new if x["Email Body"] or x["Sent On"]]   # undrafted ones wait
    ready.sort(key=lambda x: -int(x["Fit Score"]) if str(x["Fit Score"]).isdigit() else 0)
    if ready:
        queue_ws.append_rows([[safe_cell(x.get(h, "")) for h in qhdr] for x in ready],
                             value_input_option="RAW")
        print(f"Email Queue: {len(ready)} new emails ready for approval")
    if stopped:
        raise OutOfCredits()


# ======================= EMAIL SENDING (privenstaff.net mailboxes) =======================
# Settings and the list of sending mailboxes live in the "Email Sending" tab of the Sheet
# (built by the Sheet's Apps Script). Mailbox passwords are NOT in the Sheet: they live in
# the GitHub secret SMTP_PASSWORDS as JSON, e.g. {"juan@privenstaff.net": "pass1", ...}.
# Emails rotate between active mailboxes, in small batches, with random pauses.

SENDING_TAB = "Email Sending"
SENDING_DEFAULTS = {
    "Sending Status": "PAUSED",          # ACTIVE or PAUSED (master switch)
    "Automatic Sending": "On",           # On = sends by itself; Off = only "Send now"
    "Morning Blast": "On",               # On = most of the day's emails go out in the morning
    "Blast Start Hour": "8",             # New York time
    "Blast End Hour": "10",
    "Blast Share Percent": "80",         # % of the Daily Total Cap sent during the blast
    "Check Every Minutes": "15",         # how often the timer starts a sending run
    "Auto-Approve Drafts": "On",         # On = new drafts send without you typing Send
    "Auto-Approve Min Fit": "0",         # only auto-send leads with at least this fit score (0 = all)
    "Daily Total Cap": "60",             # all mailboxes together, per day
    "Per-Sender Daily Cap": "20",        # default per mailbox (can be set per mailbox)
    "Batch Size Per Run": "10",          # max emails per send run
    "Delay Min Seconds": "45",           # random pause between emails
    "Delay Max Seconds": "120",
    "Window Start Hour": "9",            # New York time, scheduled runs only
    "Window End Hour": "17",
    "Weekdays Only": "Yes",
    "Follow-ups": "On",
    "Follow-up After Days": "4",
    "Final Email After Days": "10",      # 3rd and last email of the sequence
    "Test Email To": "",
    "SMTP Host": "mail.privenstaff.net",
    "SMTP Port": "465",
    "SMTP Security": "SSL",              # SSL (port 465) or STARTTLS (port 587)
    "IMAP Host": "mail.privenstaff.net",
    "IMAP Port": "993",
    "Reply-To": "",
}
SENDER_HEADERS = ["Active", "Email", "Display Name", "Daily Cap", "Sent Today", "Sent Total",
                  "Last Used", "Last Test", "Last Error", "Notes"]
YES_WORDS = ("yes", "y", "true", "on", "x", "active", "1", "\u2713", "\u2714")


def _yes(v):
    return str(v or "").strip().lower() in YES_WORDS


def _int(v, default):
    try:
        return int(float(str(v).strip()))
    except (TypeError, ValueError):
        return default


def load_sending_config(book):
    """Read settings + mailboxes from the 'Email Sending' tab. Falls back to the old Gmail
    secrets (GMAIL_USER / GMAIL_APP_PASSWORD) only if the tab is missing."""
    cfg = {"settings": dict(SENDING_DEFAULTS), "senders": [], "ws": None, "hdr": {},
           "source": "none"}
    passwords = {}
    try:
        passwords = {k.strip().lower(): v for k, v in
                     json.loads(os.getenv("SMTP_PASSWORDS", "") or "{}").items()}
    except Exception:
        problem("SMTP_PASSWORDS secret is not valid JSON")
    shared = os.getenv("SMTP_PASSWORD", "")
    ws = None
    try:
        ws = book.worksheet(SENDING_TAB)
    except Exception:
        ws = None
    if ws is not None:
        cfg["ws"], cfg["source"] = ws, "sheet"
        values = ws.get_all_values()
        seen_keys = set()
        for r in values:                       # settings = first rows above "LIVE STATS"
            key = r[0].strip() if r else ""
            if key == "LIVE STATS":
                break
            if len(r) >= 2 and key in SENDING_DEFAULTS and key not in seen_keys and r[1].strip() != "":
                cfg["settings"][key] = r[1].strip()
                seen_keys.add(key)
        # mailbox table: find its header row (has "Email" and "Display Name")
        for ri, r in enumerate(values):
            cells = [c.strip() for c in r]
            if "Email" in cells and "Display Name" in cells:
                hdr = {h: i for i, h in enumerate(cells) if h}
                cfg["hdr"] = hdr
                for rj in range(ri + 1, len(values)):
                    row = values[rj] + [""] * (len(cells) - len(values[rj]))
                    em = row[hdr["Email"]].strip()
                    if not em:
                        if not any(row[i].strip() for i in hdr.values()):
                            break
                        continue
                    cap = _int(row[hdr["Daily Cap"]] if "Daily Cap" in hdr else "",
                               _int(cfg["settings"]["Per-Sender Daily Cap"], 20))
                    cfg["senders"].append({
                        "row": rj + 1, "email": em,
                        "name": (row[hdr["Display Name"]].strip() or SENDER_NAME),
                        "active": _yes(row[hdr["Active"]]) if "Active" in hdr else True,
                        "cap": cap,
                        "password": passwords.get(em.lower()) or shared,
                    })
                break
    elif os.getenv("GMAIL_USER") and os.getenv("GMAIL_APP_PASSWORD"):
        cfg["source"] = "gmail"
        cfg["settings"].update({"Sending Status": "ACTIVE", "SMTP Host": "smtp.gmail.com",
                                "SMTP Port": "465", "SMTP Security": "SSL",
                                "IMAP Host": "imap.gmail.com", "IMAP Port": "993",
                                "Daily Total Cap": str(DAILY_SEND_CAP),
                                "Batch Size Per Run": str(SEND_LIMIT_PER_DAY),
                                "Window Start Hour": "0", "Window End Hour": "24",
                                "Weekdays Only": "No", "Delay Min Seconds": "3",
                                "Delay Max Seconds": "5"})
        cfg["senders"].append({"row": 0, "email": os.environ["GMAIL_USER"], "name": SENDER_NAME,
                               "active": True, "cap": DAILY_SEND_CAP,
                               "password": os.environ["GMAIL_APP_PASSWORD"]})
    for snd in cfg["senders"]:
        if snd["active"] and not snd["password"]:
            problem(f"No password for {snd['email']}: add it to the SMTP_PASSWORDS secret")
    return cfg


def sender_note(cfg, snd, column, text):
    """Write 'Last Test' / 'Last Error' for one mailbox row in the Email Sending tab."""
    ws, hdr = cfg.get("ws"), cfg.get("hdr") or {}
    if ws is None or not snd.get("row") or column not in hdr:
        return
    try:
        ws.update(range_name=gspread.utils.rowcol_to_a1(snd["row"], hdr[column] + 1),
                  values=[[text[:200]]])
    except Exception as e:
        print(f"  Could not write {column}: {e}")


class Mailer:
    """Keeps one SMTP connection per mailbox for the length of a run, and saves a copy of
    every email it sends into that mailbox's Sent folder (via IMAP), so you can see them in
    Roundcube / Thunderbird like any email you send yourself."""

    def __init__(self, cfg):
        st = cfg["settings"]
        self.host = st["SMTP Host"]
        self.port = _int(st["SMTP Port"], 465)
        self.starttls = st["SMTP Security"].strip().upper() == "STARTTLS"
        self.reply_to = st.get("Reply-To", "") or os.getenv("REPLY_TO", "")
        self.imap_host = st.get("IMAP Host", "") or self.host
        self.imap_port = _int(st.get("IMAP Port", "993"), 993)
        self.conns = {}
        self.imaps = {}
        self.sent_folders = {}

    def _conn(self, snd):
        key = snd["email"].lower()
        if key in self.conns:
            return self.conns[key]
        if self.starttls:
            c = smtplib.SMTP(self.host, self.port, timeout=60)
            c.ehlo()
            c.starttls()
            c.ehlo()
        else:
            c = smtplib.SMTP_SSL(self.host, self.port, timeout=60)
        c.login(snd["email"], snd["password"])
        self.conns[key] = c
        return c

    def _imap(self, snd):
        key = snd["email"].lower()
        if key not in self.imaps:
            M = imaplib.IMAP4_SSL(self.imap_host, self.imap_port)
            M.login(snd["email"], snd["password"])
            self.imaps[key] = M
        return self.imaps[key]

    def _sent_folder(self, M, key):
        """Find the mailbox's Sent folder (cPanel usually calls it INBOX.Sent)."""
        if key in self.sent_folders:
            return self.sent_folders[key]
        folder = None
        try:
            _, lines = M.list()
            names = []
            for raw in lines or []:
                line = raw.decode(errors="ignore") if isinstance(raw, bytes) else str(raw)
                m = re.match(r'\((?P<flags>[^)]*)\)\s+(?:"[^"]*"|NIL)\s+(?P<name>.+)$', line)
                if not m:
                    continue
                name = m.group("name").strip().strip('"')
                names.append(name)
                if "\\sent" in m.group("flags").lower():
                    folder = name
                    break
            if not folder:
                for want in ("INBOX.Sent", "Sent", "INBOX/Sent", "Sent Items", "Sent Messages"):
                    if want in names:
                        folder = want
                        break
            if not folder:
                folder = next((n for n in names if n.lower().endswith("sent")), "INBOX.Sent")
        except Exception:
            folder = "INBOX.Sent"
        self.sent_folders[key] = folder
        return folder

    def save_to_sent(self, snd, msg):
        """Best effort: never stops sending if saving the copy fails."""
        key = snd["email"].lower()
        try:
            M = self._imap(snd)
            folder = self._sent_folder(M, key)
            typ, _ = M.append(folder, "\\Seen", imaplib.Time2Internaldate(time.time()),
                              msg.as_bytes())
            if typ != "OK":
                print(f"  Note: could not save a copy in {snd['email']}'s {folder} folder")
        except Exception as e:
            self.imaps.pop(key, None)
            print(f"  Note: copy not saved to Sent for {snd['email']}: {str(e)[:80]}")

    def send(self, snd, to, subject, body, html=False):
        msg = MIMEText(body, "html" if html else "plain", "utf-8")
        msg["Subject"] = subject
        msg["From"] = f"{snd['name']} <{snd['email']}>"
        msg["To"] = to
        msg["Date"] = emaillib.utils.formatdate(localtime=True)
        msg["Message-ID"] = emaillib.utils.make_msgid(domain=snd["email"].split("@")[-1])
        if self.reply_to and not html:
            msg["Reply-To"] = self.reply_to
        if not html:
            # Unsubscribe header: mail apps show an "Unsubscribe" button, which Gmail/Yahoo
            # expect from anyone sending in volume (replies land in this mailbox and are
            # marked Unsubscribed automatically by the reply check).
            msg["List-Unsubscribe"] = f"<mailto:{snd['email']}?subject=Unsubscribe>"
        try:
            self._conn(snd).send_message(msg)
        except (smtplib.SMTPServerDisconnected, smtplib.SMTPSenderRefused):
            self.conns.pop(snd["email"].lower(), None)       # reconnect once
            self._conn(snd).send_message(msg)
        if not html:                                          # outreach emails, not the brief
            self.save_to_sent(snd, msg)

    def close(self):
        for c in self.conns.values():
            try:
                c.quit()
            except Exception:
                pass
        for M in self.imaps.values():
            try:
                M.logout()
            except Exception:
                pass
        self.conns, self.imaps = {}, {}


def run_sender_test(cfg):
    """Mode 'test': log in to EVERY listed mailbox (on or off) via SMTP + IMAP and send a
    test email, so you can test a new mailbox before switching it on."""
    st = cfg["settings"]
    to = st.get("Test Email To", "").strip()
    mailer = Mailer(cfg)
    results = []
    for snd in cfg["senders"]:
        stamp = ny_now().strftime("%Y-%m-%d %H:%M")
        if not snd["password"]:
            sender_note(cfg, snd, "Last Test", f"FAILED {stamp}: no password in SMTP_PASSWORDS")
            results.append((snd["email"], False))
            continue
        try:
            mailer.send(snd, to or snd["email"], f"Privenstaff test from {snd['email']}",
                        f"Test email from {snd['email']} via {mailer.host}.\n"
                        f"If you can read this, sending from this mailbox works.")
            imap_ok = "IMAP ok"
            try:
                M = imaplib.IMAP4_SSL(st["IMAP Host"], _int(st["IMAP Port"], 993))
                M.login(snd["email"], snd["password"])
                M.logout()
            except Exception as e:
                imap_ok = f"IMAP failed: {str(e)[:60]}"
            sender_note(cfg, snd, "Last Test", f"OK {stamp} (sent to {to or snd['email']}; {imap_ok})")
            results.append((snd["email"], True))
            print(f"  Test OK: {snd['email']}")
        except Exception as e:
            sender_note(cfg, snd, "Last Test", f"FAILED {stamp}: {str(e)[:120]}")
            problem(f"Test failed for {snd['email']}: {str(e)[:80]}")
            results.append((snd["email"], False))
            print(f"  Test FAILED: {snd['email']}: {e}")
        time.sleep(2)
    mailer.close()
    print(f"Mailbox test done: {sum(1 for _, ok in results if ok)}/{len(results)} OK")
    return results


def run_outreach(tabs, log_ws, cfg=None, mode="send"):
    """Send approved emails (Approve = Send) and due follow-ups from the Email Queue,
    rotating between active mailboxes within all caps. mode: send (scheduled, respects the
    sending window) or send_now (button: ignores the window, still respects PAUSED)."""
    cfg = cfg or {"settings": dict(SENDING_DEFAULTS), "senders": []}
    st = cfg["settings"]
    if not os.getenv("BUSINESS_ADDRESS", "").strip():
        print("Outreach paused: add a BUSINESS_ADDRESS secret (US law requires a postal "
              "address in marketing emails).")
        problem("Outreach paused: add the BUSINESS_ADDRESS secret")
        return []
    if st["Sending Status"].strip().upper() != "ACTIVE":
        print("Sending is PAUSED in the Email Sending tab. Nothing sent.")
        return []
    now_ny = ny_now()
    if mode == "send" and not _yes(st.get("Automatic Sending", "On")):
        print("Automatic Sending is Off in the Email Sending tab: only 'Send now' sends.")
        return []
    if mode == "send":
        start_h, end_h = _int(st["Window Start Hour"], 9), _int(st["Window End Hour"], 17)
        if _yes(st.get("Morning Blast", "Off")):
            start_h = _int(st.get("Blast Start Hour"), 8)   # the day starts with the blast
        if not (start_h <= now_ny.hour < end_h):
            print(f"Outside the sending window ({start_h}:00-{end_h}:00 New York). Nothing sent.")
            return []
        if _yes(st["Weekdays Only"]) and now_ny.weekday() >= 5:
            print("Weekdays only: today is a weekend day. Nothing sent.")
            return []
    senders = [x for x in cfg["senders"] if x["active"] and x["password"]]
    if not senders:
        print("No active mailbox with a password. Nothing sent.")
        problem("No active sending mailbox (check the Email Sending tab and SMTP_PASSWORDS)")
        return []
    follow_on = _yes(st["Follow-ups"])
    follow_days = _int(st["Follow-up After Days"], FOLLOWUP_DAYS)
    final_days = max(follow_days + 3, _int(st.get("Final Email After Days"), 10))
    today = now_ny.strftime("%Y-%m-%d")

    # how much each mailbox already sent today (from the Outreach Log)
    by_sender = {}
    log_hdr = None
    if log_ws is not None:
        try:
            log_hdr = sheet_headers(log_ws, OUTREACH_LOG_HEADERS)
            for r in log_ws.get_all_values()[1:]:
                r = r + [""] * (len(log_hdr) - len(r))
                if r[log_hdr.index("Sent At")].startswith(today):
                    f = r[log_hdr.index("From")].strip().lower()
                    by_sender[f] = by_sender.get(f, 0) + 1
        except Exception as e:
            print(f"  Could not read Outreach Log: {e}")
    remaining = {x["email"].lower(): max(0, x["cap"] - by_sender.get(x["email"].lower(), 0))
                 for x in senders}
    failed = set()

    stop_words = ("replied", "unsubscribe", "bounced", "not interested", "do not")
    blocked, already = set(), set()
    sheets = []
    for tab, ws in tabs:
        values = ws.get_all_values()
        need = ("Email", "Contact Name", "Approve", "Sent On", "Follow-up Sent On",
                "Reply Status", "Email Subject", "Email Body")
        if len(values) < 2 or any(c not in values[0] for c in need):
            continue
        hdr = values[0]
        rows = [r + [""] * (len(hdr) - len(r)) for r in values[1:]]
        sheets.append((tab, ws, hdr, rows))
        for r in rows:
            em = r[hdr.index("Email")].strip().lower()
            if any(w in r[hdr.index("Reply Status")].lower() for w in stop_words):
                blocked.add(em)
            if r[hdr.index("Sent On")].strip():
                already.add(em)
    sent_today = sum(1 for _, _, hdr, rows in sheets for r in rows
                     for c in ("Sent On", "Follow-up Sent On")
                     if c in hdr and r[hdr.index(c)].startswith(today))
    total_cap = _int(st["Daily Total Cap"], 60)
    room = min(_int(st["Batch Size Per Run"], 10), max(0, total_cap - sent_today),
               sum(remaining.values()))
    if mode == "send" and _yes(st.get("Morning Blast", "Off")):
        room = min(room, blast_room(st, now_ny, total_cap, sent_today))
    print(f"Daily total cap {total_cap}: {sent_today} sent today; this run can send {room} "
          f"using {len(senders)} mailbox(es)")
    dmin = max(0, _int(st["Delay Min Seconds"], 45))
    dmax = max(dmin, _int(st["Delay Max Seconds"], 120))

    def pick(preferred=""):
        p = preferred.strip().lower()
        if p and p in remaining and remaining[p] > 0 and p not in failed:
            return next(x for x in senders if x["email"].lower() == p)
        ok = [x for x in senders if remaining[x["email"].lower()] > 0
              and x["email"].lower() not in failed]
        if not ok:
            return None
        # rotate: the mailbox that has sent the least today goes next
        return min(ok, key=lambda x: by_sender.get(x["email"].lower(), 0))

    mailer = Mailer(cfg)
    sent, sent_list = 0, []
    attempts, rejected = 0, 0
    try:
        for tab, ws, hdr, rows in sheets:
            col = lambda c: hdr.index(c)
            name_col = "Company" if "Company" in hdr else "Organizer"
            for n, r in enumerate(rows, start=2):
                if sent >= room:
                    break
                em = r[col("Email")].strip()
                key = em.lower()
                if not EMAIL_RE.match(em) or key in blocked:
                    continue
                approve = r[col("Approve")].strip().lower()
                fit = r[col("Fit Score")] if "Fit Score" in hdr else ""
                # Auto-approve: every drafted email sends by itself, unless you typed No/Hold
                # in Approve or its fit score is below "Auto-Approve Min Fit"
                min_fit = _int(st.get("Auto-Approve Min Fit"), 0)
                auto = (_yes(st.get("Auto-Approve Drafts", "Off"))
                        and approve not in ("no", "hold", "skip", "n")
                        and (min_fit <= 0 or (str(fit).isdigit() and int(fit) >= min_fit)))
                kind, preferred = None, ""
                if (approve in APPROVE_WORDS or auto) and not r[col("Sent On")].strip():
                    if key in already:   # same address approved twice: send once
                        continue
                    when = parse_send_at(r[col("Send At")]) if "Send At" in hdr else None
                    if when is False:
                        problem(f"Email Queue row {n}: 'Send At' not understood "
                                f"(use e.g. 10/6/2026 9:30 AM)")
                        continue
                    if when and when > ny_now():
                        continue   # scheduled for later
                    if not r[col("Email Body")].strip():
                        continue
                    kind, subject = "First email", r[col("Email Subject")].strip() or \
                        f"Event staffing for {r[col(name_col)]}"
                    body = r[col("Email Body")].strip() + signature()
                elif (follow_on and r[col("Sent On")].strip()
                      and not r[col("Follow-up Sent On")].strip()
                      and not r[col("Reply Status")].strip()
                      and r[col("Sent On")][:10] <= (TODAY - datetime.timedelta(
                          days=follow_days)).isoformat()):
                    kind = "Follow-up"
                    preferred = r[col("Sent From")] if "Sent From" in hdr else ""
                    subject = "Re: " + (r[col("Email Subject")].strip() or "Event staffing")
                    seg = r[col("Segment")] if "Segment" in hdr else "Other"
                    body = followup_body(r[col("Contact Name")], r[col(name_col)], seg) + signature()
                elif (follow_on and "Follow-up 2 Sent On" in hdr
                      and r[col("Follow-up Sent On")].strip()
                      and not r[col("Follow-up 2 Sent On")].strip()
                      and not r[col("Reply Status")].strip()
                      and r[col("Sent On")][:10] <= (TODAY - datetime.timedelta(
                          days=final_days)).isoformat()
                      and r[col("Follow-up Sent On")][:10] <= (TODAY - datetime.timedelta(
                          days=3)).isoformat()):
                    kind = "Final email"
                    preferred = r[col("Sent From")] if "Sent From" in hdr else ""
                    subject = "Re: " + (r[col("Email Subject")].strip() or "Event staffing")
                    body = final_body(r[col("Contact Name")], r[col(name_col)]) + signature()
                if not kind:
                    continue
                snd = pick(preferred)
                if snd is None:
                    print("All mailboxes reached their daily caps (or failed). Stopping.")
                    room = sent
                    break
                if sent > 0:
                    time.sleep(random.uniform(dmin, dmax))   # human-like pacing
                attempts += 1
                try:
                    mailer.send(snd, em, subject, body)
                except Exception as e:
                    print(f"  Could not email {em} from {snd['email']}: {e}")
                    err = str(e).lower()
                    if (isinstance(e, smtplib.SMTPRecipientsRefused)
                            or any(w in err for w in RECIPIENT_BAD)):
                        # bad address: mark it so it is never emailed or followed up again
                        rejected += 1
                        blocked.add(key)
                        try:
                            ws.update(range_name=gspread.utils.rowcol_to_a1(
                                n, col("Reply Status") + 1),
                                values=[[f"Bounced {TODAY.isoformat()} (address rejected)"]])
                        except Exception:
                            pass
                        if rejected >= BOUNCE_STOP_MIN and rejected / attempts > BOUNCE_STOP_RATE:
                            problem(f"Sending STOPPED: {rejected} of {attempts} addresses were "
                                    f"rejected in one run. Clean the list (many dead addresses) "
                                    f"before sending more; it protects privenstaff.net.")
                            room = sent
                            break
                        continue
                    if any(sig.lower() in str(e).lower() for sig in STOP_SIGNALS):
                        failed.add(snd["email"].lower())
                        stamp = ny_now().strftime("%Y-%m-%d %H:%M")
                        sender_note(cfg, snd, "Last Error", f"{stamp}: {str(e)[:150]}")
                        problem(f"Mailbox {snd['email']} STOPPED for today: the mail server "
                                f"pushed back (limit, block or login). Other mailboxes continue.")
                        if len(failed) >= len(senders):
                            problem("All mailboxes stopped. Do not resend today; check the accounts.")
                            break
                    else:
                        problem(f"Could not email {em}")
                    continue
                sent += 1
                already.add(key)
                k = snd["email"].lower()
                remaining[k] -= 1
                by_sender[k] = by_sender.get(k, 0) + 1
                now = ny_now().strftime("%Y-%m-%d %H:%M")   # New York time
                cells = ([("Sent On", now)] if kind == "First email"
                         else [("Follow-up 2 Sent On", now)] if kind == "Final email"
                         else [("Follow-up Sent On", now)])
                if kind == "First email" and "Sent From" in hdr:
                    cells.append(("Sent From", snd["email"]))
                ws.batch_update([{"range": gspread.utils.rowcol_to_a1(n, col(c) + 1),
                                  "values": [[v]]} for c, v in cells])
                if log_ws is not None and log_hdr:
                    entry = {"Sent At": now, "Type": kind, "To": em, "Company": r[col(name_col)],
                             "Subject": subject, "Tab": tab, "Row": n, "From": snd["email"]}
                    log_ws.append_row([entry.get(h, "") for h in log_hdr])
                print(f"  Sent {kind.lower()} to {em} from {snd['email']}")
                sent_list.append({"type": kind, "to": em, "company": r[col(name_col)],
                                  "subject": subject, "from": snd["email"]})
    finally:
        mailer.close()
    print(f"Outreach: {sent} emails sent this run"
          + (f", {rejected} addresses rejected (marked Bounced)" if rejected else ""))
    return sent_list


def blast_room(st, now_ny, total_cap, sent_today):
    """Morning Blast pacing. During the blast hours, send fast until Blast Share Percent of
    the Daily Total Cap is out. After that, trickle the rest evenly until Window End Hour."""
    b_start = _int(st.get("Blast Start Hour"), 8)
    b_end = max(b_start + 1, _int(st.get("Blast End Hour"), 10))
    end_h = _int(st.get("Window End Hour"), 17)
    share = min(100, max(0, _int(st.get("Blast Share Percent"), 80)))
    every = max(5, _int(st.get("Check Every Minutes"), 15))
    blast_target = (total_cap * share + 99) // 100
    if b_start <= now_ny.hour < b_end and sent_today < blast_target:
        allowed = blast_target - sent_today
        print(f"Morning Blast: {sent_today} of {blast_target} blast emails sent; "
              f"this run may send {allowed}")
        return allowed
    end_dt = now_ny.replace(hour=min(end_h, 23), minute=59 if end_h >= 24 else 0,
                            second=0, microsecond=0)
    minutes_left = max(1, (end_dt - now_ny).total_seconds() / 60)
    runs_left = max(1, int(minutes_left // every) + 1)
    left = max(0, total_cap - sent_today)
    allowed = (left + runs_left - 1) // runs_left
    print(f"Trickle: {left} left for today over about {runs_left} more runs; "
          f"this run may send {allowed}")
    return allowed


def reply_part(text):
    """Only the person's own words, not our quoted email below it."""
    cut = re.split(r"\n\s*On .{0,200}wrote:|-----Original Message-----|\n\s*From:\s|"
                   r"\n\s*Sent from my|\n_{5,}", text, maxsplit=1)[0]
    return "\n".join(l for l in cut.splitlines() if not l.strip().startswith(">")).strip()


REPLIES_TAB = "Replies"
REPLIES_HEADERS = ["Received", "Status", "Company", "Contact", "Email", "Subject", "Message",
                   "Mailbox", "Handled", "Full Email"]


AUTO_SUBJECT = ("automatic reply", "auto reply", "auto-reply", "autoreply", "out of office",
                "out of the office", "away from the office", "on vacation", "we received your",
                "we have received your", "thank you for contacting", "thanks for contacting",
                "thank you for reaching out", "thanks for reaching out", "ticket", "request received",
                "your request", "case #", "do not reply", "delivery status", "undeliverable")
AUTO_BODY = ("i am out of the office", "i'm out of the office", "i am currently out", "i'm currently out",
             "i will be out of the office", "limited access to email", "this is an automated",
             "this is an automatic", "do not reply to this", "we have received your", "we received your",
             "a member of our team will", "someone will get back to you", "your ticket", "ticket number",
             "support request", "has been received")


def is_auto_reply(head, own):
    """Out-of-office messages, ticket confirmations and other robot replies."""
    if str(head.get("Auto-Submitted", "")).lower() not in ("", "no"):
        return True
    if head.get("X-Autoreply") or head.get("X-Autorespond"):
        return True
    if str(head.get("Precedence", "")).lower() in ("auto_reply", "bulk", "junk"):
        return True
    subj = str(head.get("Subject", "")).lower()
    body = (own or "")[:800].lower()
    return any(w in subj for w in AUTO_SUBJECT) or any(w in body for w in AUTO_BODY)


def _received(date_raw):
    try:
        return emaillib.utils.parsedate_to_datetime(date_raw).astimezone(NY_TZ).strftime("%Y-%m-%d %H:%M")
    except Exception:
        return ny_now().strftime("%Y-%m-%d %H:%M")


def log_replies(book, results, details, backfill=None, earlier=None):
    """Replies tab: one row per lead who replied (or unsubscribed), with their message and the
    full email. Rows saved earlier without the full text are filled in. Bounces not logged."""
    backfill, earlier = backfill or {}, earlier or {}
    new = []
    for x in results:
        if x["status"] == "Bounced":
            continue
        d = details.get(x["email"], ("", "", "", x.get("snippet", ""), x.get("snippet", "")))
        new.append({"Received": _received(d[0]), "Status": x["status"], "Company": x.get("company", ""),
                    "Contact": x.get("contact", ""), "Email": x["email"], "Subject": d[1],
                    "Message": (d[3] or "")[:20000], "Mailbox": d[2], "Full Email": (d[4] or "")[:45000]})
    for em, d in backfill.items():
        st, company, contact = earlier.get(em, ("Replied", "", ""))
        new.append({"Received": _received(d[0]), "Status": st, "Company": company, "Contact": contact,
                    "Email": em, "Subject": d[1], "Message": (d[3] or "")[:20000], "Mailbox": d[2],
                    "Full Email": (d[4] or "")[:45000]})
    if not new or book is None:
        return
    try:
        ws = book.worksheet(REPLIES_TAB)
    except Exception:
        ws = book.add_worksheet(title=REPLIES_TAB, rows=1000, cols=len(REPLIES_HEADERS))
        ws.append_row(REPLIES_HEADERS)
    hdr = sheet_headers(ws, REPLIES_HEADERS)
    rows = ws.get_all_values()[1:]
    where = {}
    for n, r in enumerate(rows, start=2):
        r = r + [""] * (len(hdr) - len(r))
        where.setdefault(r[hdr.index("Email")].strip().lower(), (n, r))
    updates, appends = [], []
    for x in new:
        hit = where.get(x["Email"].lower())
        if hit and not hit[1][hdr.index("Full Email")].strip():
            n = hit[0]                                       # fill in the missing text
            for c in ("Message", "Full Email", "Subject", "Mailbox"):
                if x.get(c):
                    updates.append({"range": gspread.utils.rowcol_to_a1(n, hdr.index(c) + 1),
                                    "values": [[safe_cell(x[c])]]})
        elif not hit:
            appends.append([safe_cell(x.get(h, "")) for h in hdr])
    if updates:
        ws.batch_update(updates, value_input_option="RAW")
    if appends:
        ws.append_rows(appends, value_input_option="RAW")
    print(f"Replies tab: {len(appends)} new, {len(updates)} cells filled in on earlier replies")


def send_hot_alert(cfg, replies):
    """Email you right away when a lead replies (to REPORT_TO)."""
    hot = [x for x in replies if x["status"] == "Replied"]
    to = os.getenv("REPORT_TO", "").strip()
    boxes = [x for x in cfg["senders"] if x["active"] and x["password"]]
    if not hot or not to or not boxes:
        return
    rows = "".join(f"<tr><td><b>{x['company']}</b><br>{x['email']}</td>"
                   f"<td>{(x.get('snippet') or '').replace('<', '&lt;')[:600]}</td></tr>" for x in hot)
    html = (f"<h2>🔥 {len(hot)} new {'reply' if len(hot) == 1 else 'replies'} from leads</h2>"
            f"<p>Answer fast: the first hour is when deals are won.</p>"
            f"<table border='1' cellpadding='8' style='border-collapse:collapse;font-family:Arial;"
            f"font-size:14px'><tr style='background:#3205a8;color:#fff'><th>Lead</th>"
            f"<th>What they said</th></tr>{rows}</table>")
    mailer = Mailer(cfg)
    try:
        mailer.send(boxes[0], to, f"🔥 Hot lead: {hot[0]['company'] or hot[0]['email']} replied"
                    + (f" (+{len(hot) - 1} more)" if len(hot) > 1 else ""), html, html=True)
        print(f"Hot-lead alert sent for {len(hot)} replies")
    except Exception as e:
        print(f"  Hot-lead alert failed: {e}")
    finally:
        mailer.close()


def _html_to_text(html):
    import html as htmllib
    t = re.sub(r"(?is)<(script|style|head)[^>]*>.*?</\1>", " ", html)
    t = re.sub(r"(?i)<br\s*/?>|</p>|</div>|</tr>|</li>|</h\d>", "\n", t)
    t = re.sub(r"(?i)<blockquote", "\n> <blockquote", t)
    t = re.sub(r"<[^>]+>", " ", t)
    t = htmllib.unescape(t)
    t = re.sub(r"[ \t\xa0]+", " ", t)
    return re.sub(r"\n\s*\n\s*\n+", "\n\n", t).strip()


def _text_of(msg, limit=30000):
    """The readable text of an email: the plain-text part, or the HTML part converted."""
    parts = list(msg.walk()) if msg.is_multipart() else [msg]
    plain, html = [], []
    for part in parts:
        ctype = part.get_content_type()
        if ctype not in ("text/plain", "text/html") or part.get_filename():
            continue
        try:
            txt = part.get_payload(decode=True).decode(part.get_content_charset() or "utf-8", "ignore")
        except Exception:
            continue
        (plain if ctype == "text/plain" else html).append(txt)
    text = "\n".join(plain).strip() or _html_to_text("\n".join(html))
    return text.replace("\r\n", "\n")[:limit]


def check_replies(tabs, cfg=None):
    """Read every active mailbox's inbox: mark Replied / Unsubscribed / Bounced automatically,
    save each reply's full text to the Replies tab, and fill in the text of earlier replies."""
    cfg = cfg or {"settings": dict(SENDING_DEFAULTS), "senders": []}
    st = cfg["settings"]
    contacted, earlier = {}, {}
    for tab, ws in tabs:
        values = ws.get_all_values()
        if len(values) < 2 or any(c not in values[0] for c in ("Email", "Sent On", "Reply Status")):
            continue
        hdr = values[0]
        for n, r in enumerate(values[1:], start=2):
            r = r + [""] * (len(hdr) - len(r))
            em = r[hdr.index("Email")].strip().lower()
            rs = r[hdr.index("Reply Status")].strip()
            name = r[hdr.index("Company")] if "Company" in hdr else r[hdr.index("Organizer")]
            contact = r[hdr.index("Contact Name")] if "Contact Name" in hdr else ""
            if em and r[hdr.index("Sent On")].strip() and not rs:
                contacted.setdefault(em, []).append((ws, hdr, n, name, contact))
            elif em and re.match(r"(?i)(replied|unsubscribed|booked)", rs):
                earlier.setdefault(em, (rs.split(" ")[0], name, contact))
    # replies already saved: only re-read the ones still missing their full text
    book = tabs[0][1].spreadsheet if tabs else None
    saved = {}
    try:
        rws = book.worksheet(REPLIES_TAB)
        rv = rws.get_all_values()
        rh = rv[0] if rv else []
        for r in rv[1:]:
            r = r + [""] * (len(rh) - len(r))
            if "Email" in rh:
                saved[r[rh.index("Email")].strip().lower()] = bool(
                    "Full Email" in rh and r[rh.index("Full Email")].strip())
    except Exception:
        pass
    want = {em for em in earlier if not saved.get(em)}
    boxes = [x for x in cfg["senders"] if x["active"] and x["password"]]
    if (not contacted and not want) or not boxes:
        return []
    found, details, backfill = {}, {}, {}
    since = (TODAY - datetime.timedelta(days=REPLY_CHECK_DAYS)).strftime("%d-%b-%Y")
    for snd in boxes:
        try:
            M = imaplib.IMAP4_SSL(st["IMAP Host"], _int(st["IMAP Port"], 993))
            M.login(snd["email"], snd["password"])
            M.select("INBOX", readonly=True)
            _, data = M.search(None, f"(SINCE {since})")
            ids = data[0].split()[-600:]
            # ONE request for all the headers (fast), then full text only for real matches
            heads = []
            if ids:
                _, resp = M.fetch(b",".join(ids), "(BODY.PEEK[HEADER.FIELDS (FROM SUBJECT DATE "
                                                  "AUTO-SUBMITTED X-AUTOREPLY X-AUTORESPOND PRECEDENCE)])")
                for part in resp or []:
                    if isinstance(part, tuple) and len(part) > 1:
                        heads.append((part[0].split()[0], emaillib.message_from_bytes(part[1])))
            print(f"  Reply check {snd['email']}: {len(heads)} recent messages")
            for mid, head in heads:
                frm = parseaddr(head.get("From", ""))[1].lower()
                bounce = "mailer-daemon" in frm or "postmaster" in frm
                if frm not in contacted and frm not in want and not bounce:
                    continue
                _, b = M.fetch(mid, "(BODY.PEEK[])")
                msg = emaillib.message_from_bytes(b[0][1])
                body = _text_of(msg)
                own = reply_part(body) or body                 # their words only
                info = (head.get("Date", ""), head.get("Subject", ""), snd["email"], own, body)
                if frm in want and frm not in contacted:
                    backfill[frm] = info                        # newest message wins
                    continue
                text = f"{head.get('Subject', '')} {own}".lower()
                if not bounce and is_auto_reply(head, own):
                    continue          # out-of-office / ticket robots are not real replies
                if bounce:
                    for em in contacted:
                        if em in f"{head.get('Subject', '')} {body}".lower():
                            found[em] = ("Bounced", "")
                elif any(w in text for w in ("unsubscribe", "remove me", "stop emailing",
                                             "take me off", "do not contact")):
                    found[frm] = ("Unsubscribed", own[:500])
                    details[frm] = info
                elif frm not in found:
                    found[frm] = ("Replied", own[:500])
                    details[frm] = info
            M.logout()
        except Exception as e:
            problem(f"Inbox check failed for {snd['email']}: {str(e)[:80]}")
            print(f"  Reply check skipped for {snd['email']}: {e}")
    results = []
    for em, (status, snippet) in found.items():
        rows = contacted.get(em, [])
        for ws, hdr, n, name, contact in rows:
            ws.update(range_name=gspread.utils.rowcol_to_a1(n, hdr.index("Reply Status") + 1),
                      values=[[f"{status} {TODAY.isoformat()}"]])
        if rows:
            results.append({"status": status, "email": em, "company": rows[0][3],
                            "contact": rows[0][4], "snippet": snippet})
    print(f"Replies found: {len(results)}")
    try:
        log_replies(book, results, details, backfill, earlier)
    except Exception as e:
        print(f"  Replies tab not updated: {e}")
    try:
        send_hot_alert(cfg, results)
    except Exception as e:
        print(f"  Hot-lead alert skipped: {e}")
    return results


RESULTS_TAB = "Outreach Results"
EMAIL_FINDER_DONE = {"yes": False}


def write_results(queue_ws):
    """Outreach Results tab: sent, replies, reply rate and bookings by business type and
    subject style (last 7 days and all time). Values only: your formatting stays."""
    values = queue_ws.get_all_values()
    if len(values) < 2:
        return []
    hdr = values[0]
    g = lambda r, c: r[hdr.index(c)].strip() if c in hdr and hdr.index(c) < len(r) else ""
    week = (TODAY - datetime.timedelta(days=7)).isoformat()
    groups = {}
    for r in values[1:]:
        if not g(r, "Sent On"):
            continue
        rs = g(r, "Reply Status").lower()
        for key in (("Type", g(r, "Segment") or "Other"), ("Subject style", g(r, "Variant") or "-"),
                    ("All", "Total")):
            for period in ("All time", "Last 7 days"):
                if period == "Last 7 days" and g(r, "Sent On")[:10] < week:
                    continue
                k = (period,) + key
                s = groups.setdefault(k, [0, 0, 0, 0, 0])
                s[0] += 1
                s[1] += rs.startswith("replied") or "book" in rs
                s[2] += "book" in rs
                s[3] += rs.startswith("bounced")
                s[4] += rs.startswith("unsub")
    order = {"All": 0, "Type": 1, "Subject style": 2}
    rows = [["Period", "Group", "Name", "Sent", "Replies", "Reply rate", "Booked", "Bounced",
             "Unsubscribed"]]
    for k in sorted(groups, key=lambda k: (k[0] != "Last 7 days", order[k[1]], -groups[k][0])):
        s = groups[k]
        rows.append([k[0], k[1], k[2], s[0], s[1], f"{100 * s[1] / s[0]:.1f}%" if s[0] else "",
                     s[2], s[3], s[4]])
    rows.append([])
    rows.append(["Updated", TODAY.isoformat(), "Subject styles: A = specific subject, "
                 "B = question subject. The better one is used more once each has 40+ sends."])
    book = queue_ws.spreadsheet
    try:
        ws = book.worksheet(RESULTS_TAB)
    except Exception:
        ws = book.add_worksheet(title=RESULTS_TAB, rows=200, cols=9)
    ws.batch_clear(["A1:I200"])                                   # values only
    ws.update(range_name="A1", values=rows)
    print(f"Outreach Results updated ({len(rows) - 3} lines)")
    return [r for r in rows[1:] if r and r[0] == "Last 7 days"]


def pending_approvals(tabs):
    """Drafts waiting for your OK, best fit first."""
    out = []
    for tab, ws in tabs:
        values = ws.get_all_values()
        if len(values) < 2 or "Approve" not in values[0]:
            continue
        hdr = values[0]
        g = lambda r, c: r[hdr.index(c)] if c in hdr and hdr.index(c) < len(r) else ""
        for r in values[1:]:
            if (g(r, "Email Body").strip() and not g(r, "Sent On").strip()
                    and g(r, "Approve").strip().lower() not in APPROVE_WORDS
                    and not g(r, "Reply Status").strip()):
                out.append({"tab": tab, "company": g(r, "Company") or g(r, "Organizer"),
                            "contact": g(r, "Contact Name"), "email": g(r, "Email"),
                            "subject": g(r, "Email Subject"), "fit": g(r, "Fit Score")})
    out.sort(key=lambda x: -int(x["fit"]) if str(x["fit"]).isdigit() else 0)
    return out


def main():
    client = anthropic.Anthropic(max_retries=6)   # wait and retry when busy/rate-limited
    companies_ws, signals_ws, log_ws, inbox_ws, outreach_ws, texts_ws, queue_ws, drop_ws = open_tabs()
    try:
        ensure_send_at_column(queue_ws)
    except Exception as e:
        print(f"  Could not add Send At column: {e}")
    cfg = load_sending_config(queue_ws.spreadsheet)
    print(f"Sending setup: {cfg['source']}, {sum(1 for x in cfg['senders'] if x['active'])} active "
          f"mailbox(es), status {cfg['settings']['Sending Status']}")
    if os.getenv("SEND_ONLY") == "1":
        # Sending run (no research). MODE: send (scheduled), send_now (button), test, replies
        mode = (os.getenv("MODE") or "send").strip().lower()
        tabs = [("Email Queue", queue_ws)]
        try:
            sheet_headers(queue_ws, QUEUE_HEADERS)       # makes sure "Sent From" exists
        except Exception as e:
            print(f"  Could not check Email Queue columns: {e}")
        if mode == "test":
            run_sender_test(cfg)
        elif mode == "replies":
            check_replies(tabs, cfg)
        else:
            try:
                process_email_drop(anthropic.Anthropic(max_retries=6), drop_ws, queue_ws)
            except Exception as e:
                print(f"  Email Drop skipped: {e}")
            check_replies(tabs, cfg)
            sent = run_outreach(tabs, outreach_ws, cfg, mode=mode)
            print(f"Send-only run done: {len(sent)} emails sent.")
        if PROBLEMS:
            print("Problems: " + " | ".join(PROBLEMS))
            raise SystemExit(1)
        return
    try:
        signals = run_signals(client, signals_ws, log_ws, inbox_ws)
        companies = run_companies(client, companies_ws)
        for ws, name, ctx, web in ((companies_ws, "Company", ["Category", "Area", "Address"], "Website"),
                                   (signals_ws, "Organizer", ["Headline", "Venue", "Signal Type"], None)):
            try:
                refresh_empty_contacts(client, ws, name, ctx, web)
            except OutOfCredits:
                raise
            except Exception as e:
                print(f"  Re-research skipped: {e}")
        for ws, fields in ((signals_ws, SIGNAL_PITCH_FIELDS), (companies_ws, COMPANY_PITCH_FIELDS)):
            try:
                backfill_pitches(client, ws, fields)
            except OutOfCredits:
                raise
            except Exception as e:
                print(f"  Backfill skipped: {e}")
        try:
            find_emails([(companies_ws, "Company", ["Website"], COMPANY_HEADERS),
                         (signals_ws, "Organizer", ["Contact Source", "Signal URL"], SIGNAL_HEADERS)],
                        EMAIL_LOOKUPS_PER_DAY)
            EMAIL_FINDER_DONE["yes"] = True
        except Exception as e:
            print(f"  Email finder skipped: {e}")
        try:
            queue_emails(client, [(signals_ws, "Signals"), (companies_ws, "Companies")], queue_ws)
            process_email_drop(client, drop_ws, queue_ws)
        except OutOfCredits:
            raise
        except Exception as e:
            print(f"  Email Queue skipped: {e}")
    except OutOfCredits:
        print("STOPPED: Anthropic credit balance is too low. Leads that were fully researched "
              "were saved; the rest continue next run. Add credits at console.anthropic.com "
              "(Settings > Billing), ideally with auto-reload on.")
        problem("Anthropic credits ran out mid-run: finished leads were saved; add credits "
                "(turn on auto-reload) and the rest continue next run.")
        signals = locals().get("signals", [])
        companies = locals().get("companies", [])
    if CREDITS["out"] and not any("credits ran out" in p for p in PROBLEMS):
        problem("Anthropic credits ran out mid-run: finished leads were saved; add credits "
                "(turn on auto-reload) and the rest continue next run.")
    print(f"Saved to sheet: {len(signals)} signals, {len(companies)} companies.")
    if not EMAIL_FINDER_DONE["yes"]:          # free: runs even when AI credits ran out
        try:
            find_emails([(companies_ws, "Company", ["Website"], COMPANY_HEADERS),
                         (signals_ws, "Organizer", ["Contact Source", "Signal URL"], SIGNAL_HEADERS)],
                        EMAIL_LOOKUPS_PER_DAY)
        except Exception as e:
            print(f"  Email finder skipped: {e}")
    tabs = [("Email Queue", queue_ws)]   # sending, follow-ups and reply tracking happen here
    panel = {}
    try:
        enrich_phones([(signals_ws, "Organizer", "Venue"), (companies_ws, "Company", "Address")],
                      PHONE_LOOKUPS_PER_DAY)
    except Exception as e:
        print(f"  Phone finder skipped: {e}")
    try:
        dnt_ws = None
        try:
            dnt_ws = companies_ws.spreadsheet.worksheet("Do Not Text")
        except Exception:
            dnt_ws = companies_ws.spreadsheet.add_worksheet(title="Do Not Text", rows=500, cols=4)
            dnt_ws.append_row(DNT_HEADERS)
        panel["texts"] = build_texts(client, [(signals_ws, "Organizer"), (companies_ws, "Company")],
                                     texts_ws, dnt_ws, queue_ws)
    except Exception as e:
        print(f"  Text batch skipped: {e}")
        panel["texts"] = []
    for key, fn in (("replies", lambda: check_replies(tabs, cfg)),
                    # emails go out from the sending runs (send-emails.yml), not during research
                    ("sent", lambda: run_outreach(tabs, outreach_ws, cfg)
                     if os.getenv("SEND_IN_DAILY") == "1" else []),
                    ("pending", lambda: pending_approvals(tabs))):
        try:
            panel[key] = fn()
        except Exception as e:
            print(f"  {key} step error: {e}")
            problem(f"{key} step error: {str(e)[:100]}")
            panel[key] = []
    try:
        panel["results"] = write_results(queue_ws)
    except Exception as e:
        print(f"  Outreach Results skipped: {e}")
        panel["results"] = []
    panel["problems"] = PROBLEMS
    panel["cfg"] = cfg
    try:
        send_email(signals, companies, panel)
    except Exception as e:
        print(f"EMAIL FAILED (leads are still saved in the sheet): {e}")
        raise SystemExit(1)   # makes GitHub flag the run so you notice
    print("Done. Morning brief emailed.")
    if any("credits ran out" in p for p in PROBLEMS):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
