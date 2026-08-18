#!/usr/bin/env python3
"""
fetch_jd.py — Fetch a job description URL and save clean text to a file.

For LinkedIn: reads li_at session cookie from ~/.wibey/linkedin_cookies.txt
  Format:  li_at=AQEDATxxxxxxxxxxxxxxxx

Usage:
    python3 fetch_jd.py <url> <output-file>

Exit codes:
    0 — success, file written
    2 — auth-blocked (no cookie available) — needs manual paste
    1 — other error
"""

import sys
import re
import os
import time
import random
import urllib.request
import urllib.error


LINKEDIN_COOKIE_FILE = os.path.expanduser("~/.wibey/linkedin_cookies.txt")

# Sites that need session cookies (not pre-blocked anymore if cookie exists)
LINKEDIN_PATTERN = re.compile(r"linkedin\.com", re.IGNORECASE)

# Sites that are always blocked regardless
ALWAYS_BLOCKED_PATTERNS = [
    r"workday\.com",
    r"myworkdayjobs\.com",
    r"taleo\.net",
    r"successfactors",
]


def load_linkedin_cookie() -> str | None:
    """Read li_at value from ~/.wibey/linkedin_cookies.txt."""
    if not os.path.exists(LINKEDIN_COOKIE_FILE):
        return None
    with open(LINKEDIN_COOKIE_FILE, "r") as f:
        for line in f:
            line = line.strip()
            if line.startswith("li_at="):
                return line[len("li_at="):]
    return None


def is_always_blocked(url: str) -> bool:
    return any(re.search(p, url, re.IGNORECASE) for p in ALWAYS_BLOCKED_PATTERNS)


def strip_html(html: str) -> str:
    html = re.sub(r"<(script|style)[^>]*>.*?</(script|style)>", " ", html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r"<[^>]+>", " ", html)
    html = html.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
    html = html.replace("&nbsp;", " ").replace("&#39;", "'").replace("&quot;", '"')
    html = re.sub(r"&#\d+;", " ", html)
    html = re.sub(r"&[a-z]+;", " ", html)
    html = re.sub(r"\n{3,}", "\n\n", html)
    html = re.sub(r"[ \t]{2,}", " ", html)
    return html.strip()


def fetch(url: str) -> tuple[str, str]:
    """Returns (content, final_url_after_redirects)."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,*/*",
        "Accept-Language": "en-US,en;q=0.9",
    }

    # LinkedIn: inject session cookie
    if LINKEDIN_PATTERN.search(url):
        li_at = load_linkedin_cookie()
        if not li_at:
            print("AUTH_BLOCKED: LinkedIn requires li_at cookie — "
                  "add it to ~/.wibey/linkedin_cookies.txt", file=sys.stderr)
            sys.exit(2)
        headers["Cookie"] = f"li_at={li_at}; JSESSIONID=\"ajax:0\""
        headers["Csrf-Token"] = "ajax:0"
        # Use the mobile API endpoint for cleaner text output
        job_id_match = re.search(r"/jobs/view/(\d+)", url)
        if job_id_match:
            job_id = job_id_match.group(1)
            url = (
                f"https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/{job_id}"
            )

    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=15) as resp:
        final_url = resp.url          # URL after any redirects
        data = resp.read(600_000)
    return data.decode("utf-8", errors="replace"), final_url


def main():
    if len(sys.argv) < 3:
        print("Usage: fetch_jd.py <url> <output-file>", file=sys.stderr)
        sys.exit(1)

    url = sys.argv[1]
    output_path = sys.argv[2]

    if is_always_blocked(url):
        print(f"AUTH_BLOCKED: {url} requires login — paste JD manually.", file=sys.stderr)
        sys.exit(2)

    # Retry loop — LinkedIn rate-limits the same li_at cookie under concurrent
    # requests; a short backoff (3 s, 7 s) clears the throttle in most cases.
    # Jitter (0–2 s random) prevents concurrent processes from retrying simultaneously.
    MAX_ATTEMPTS = 3
    BACKOFF = [0, 3, 7]   # base seconds to wait before each attempt

    # Wall indicators for content sniffing (fallback only).
    # NOTE: "linkedin.com/login" intentionally excluded — it appears in nav links
    # on legitimate job pages and causes false positives.
    # Primary detection: final URL after redirects (most reliable).
    content_wall_indicators = [
        "/checkpoint/lg/login",
        "authwall",
    ]

    raw = None
    final_url = url
    for attempt in range(MAX_ATTEMPTS):
        base_delay = BACKOFF[attempt]
        jitter = random.uniform(0, 2.0) if attempt > 0 else 0
        delay = base_delay + jitter
        if delay:
            print(f"⏳  LinkedIn rate-limit — retrying in {delay:.1f}s "
                  f"(attempt {attempt + 1}/{MAX_ATTEMPTS})...", file=sys.stderr)
            time.sleep(delay)

        try:
            raw, final_url = fetch(url)
        except urllib.error.HTTPError as e:
            if e.code in (401, 403, 999):
                if attempt < MAX_ATTEMPTS - 1:
                    continue   # retry
                print(f"AUTH_BLOCKED: HTTP {e.code} — session may have expired. "
                      f"Refresh li_at in ~/.wibey/linkedin_cookies.txt", file=sys.stderr)
                sys.exit(2)
            print(f"HTTP error {e.code}: {e}", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f"Fetch error: {e}", file=sys.stderr)
            sys.exit(1)

        # Primary wall check: did urllib redirect us to a login/checkpoint page?
        wall_by_redirect = bool(re.search(r"/(login|checkpoint/)", final_url))

        # Fallback content sniff: look for specific wall-only phrases
        raw_head = raw[:3000].lower()
        wall_by_content = any(phrase in raw_head for phrase in content_wall_indicators)

        if wall_by_redirect or wall_by_content:
            reason = f"redirected to {final_url}" if wall_by_redirect else "wall content detected"
            print(f"DEBUG: wall triggered ({reason}); response[0:200]: {raw[:200]!r}",
                  file=sys.stderr)
            if attempt < MAX_ATTEMPTS - 1:
                raw = None
                continue   # retry after backoff
            print("AUTH_BLOCKED: Login wall detected — li_at cookie may have expired. "
                  "Refresh it in ~/.wibey/linkedin_cookies.txt", file=sys.stderr)
            sys.exit(2)

        break   # success

    if raw is None:
        print("AUTH_BLOCKED: All retry attempts exhausted.", file=sys.stderr)
        sys.exit(2)

    clean = strip_html(raw)

    if len(clean) < 200:
        print("ERROR: Content too short — blocked or empty page.", file=sys.stderr)
        sys.exit(1)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(f"Source: {url}\n\n")
        f.write(clean)

    print(f"OK: Saved {len(clean)} chars to {output_path}")
    sys.exit(0)


if __name__ == "__main__":
    main()
