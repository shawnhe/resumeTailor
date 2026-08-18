#!/usr/bin/env python3
"""
extract_company.py — Extract company name from a job posting URL or saved JD text file.

Usage:
    extract_company.py <job-url>           # from URL (pattern match + HTML fetch)
    extract_company.py --from-file <path>  # from saved JD text (most reliable)

Priority when using --from-file:
  1. Explicit "Company: X" or "About X" header lines in the text
  2. "at X" / "join X" / "© X" patterns in the first 3000 chars
  3. URL from the "Source:" header line (if present), then URL pattern match

Prints the detected company name to stdout, exits 0 on success, 1 on failure.
"""

import sys
import re
import urllib.request

def titlecase_slug(s: str) -> str:
    """Convert a slug like 'acme-corp' → 'AcmeCorp'."""
    return "".join(word.capitalize() for word in re.split(r"[-_]+", s))


def extract_from_url(url: str) -> str | None:
    """Fast pattern matching — no network required."""
    patterns = [
        # Lever: jobs.lever.co/{company}/...
        (r"jobs\.lever\.co/([^/?#]+)", 1),
        # Greenhouse: boards.greenhouse.io/{company}/
        (r"boards\.greenhouse\.io/([^/?#]+)", 1),
        # Greenhouse embed: {company}.greenhouse.io
        (r"([^./?#]+)\.greenhouse\.io", 1),
        # Workday: {company}.wd1.myworkdayjobs.com (or wd2, wd3, wd5)
        (r"(?:https?://)?([^.]+)\.wd\d+\.myworkdayjobs\.com", 1),
        # Workday no subdomain: {company}.myworkdayjobs.com
        (r"(?:https?://)?([^.]+)\.myworkdayjobs\.com", 1),
        # SmartRecruiters: jobs.smartrecruiters.com/{company}
        (r"jobs\.smartrecruiters\.com/([^/?#]+)", 1),
        # BambooHR: {company}.bamboohr.com
        (r"([^./?#]+)\.bamboohr\.com", 1),
        # Jobvite: jobs.jobvite.com/{company}
        (r"jobs\.jobvite\.com/([^/?#]+)", 1),
        # Ashby: jobs.ashbyhq.com/{company}
        (r"jobs\.ashbyhq\.com/([^/?#]+)", 1),
        # Rippling: ats.rippling.com/{company}
        (r"ats\.rippling\.com/([^/?#]+)", 1),
        # ICIMS: {company}.icims.com
        (r"([^./?#]+)\.icims\.com", 1),
        # Taleo: {company}.taleo.net
        (r"([^./?#]+)\.taleo\.net", 1),
        # Replit-style careers subdomain: careers.{company}.com
        (r"careers\.([^./?#]+)\.", 1),
        # Generic: direct company careers page — pull subdomain before .com/.io/.ai
        # e.g. stripe.com/jobs → "stripe"
        (r"(?:https?://)?(?:www\.)?([^./?#]+)\.", 1),
    ]

    for pattern, group in patterns:
        m = re.search(pattern, url, re.IGNORECASE)
        if m:
            slug = m.group(group).strip()
            # Skip generic job-board domains being caught by the fallback pattern
            skip = {"jobs", "careers", "apply", "hire", "lever", "greenhouse",
                    "workday", "myworkdayjobs", "smartrecruiters", "bamboohr",
                    "jobvite", "ashbyhq", "rippling", "icims", "taleo",
                    "linkedin", "indeed", "glassdoor", "monster", "ziprecruiter"}
            if slug.lower() not in skip:
                return titlecase_slug(slug)
    return None


def extract_from_html(url: str) -> str | None:
    """Fetch the page and parse meta tags / title."""
    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0 (compatible; resume-tailor/1.0)"},
        )
        with urllib.request.urlopen(req, timeout=12) as resp:
            html = resp.read(200_000).decode("utf-8", errors="replace")
    except Exception as e:
        print(f"[extract_company] HTTP error: {e}", file=sys.stderr)
        return None

    # 1. og:site_name  (most reliable)
    m = re.search(
        r'<meta[^>]+property=["\']og:site_name["\'][^>]+content=["\']([^"\']+)["\']',
        html, re.IGNORECASE,
    )
    if m:
        name = m.group(1).strip()
        if name and len(name) < 60:
            return name.replace(" ", "")

    # 2. og:site_name with reversed attribute order
    m = re.search(
        r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:site_name["\']',
        html, re.IGNORECASE,
    )
    if m:
        name = m.group(1).strip()
        if name and len(name) < 60:
            return name.replace(" ", "")

    # 3. Page <title> — common patterns:
    #    "Senior Engineer at Acme" → "Acme"
    #    "Acme | Careers"          → "Acme"
    #    "Careers - Acme Corp"     → "AcmeCorp"
    m = re.search(r"<title[^>]*>([^<]+)</title>", html, re.IGNORECASE)
    if m:
        title = m.group(1).strip()

        # "... at CompanyName" pattern
        at_m = re.search(
            r"\bat\s+([A-Z][A-Za-z0-9&.' -]{1,40})(?:\s*[|–\-,]|$)", title
        )
        if at_m:
            return at_m.group(1).strip().replace(" ", "")

        # "CompanyName | ..." pattern
        pipe_m = re.match(r"^([^|–\-]{2,40})[|–\-]", title)
        if pipe_m:
            candidate = pipe_m.group(1).strip()
            if candidate.lower() not in ("careers", "jobs", "apply", "join us"):
                return candidate.replace(" ", "")

    return None


def extract_from_text(text: str) -> str | None:
    """Extract company name from saved JD plain text."""
    head = text[:3000]

    # 1. Explicit "Company: Acme" or "Company Name: Acme" line
    m = re.search(r"^company(?:\s+name)?:\s*(.+)$", head, re.IGNORECASE | re.MULTILINE)
    if m:
        return m.group(1).strip().replace(" ", "")

    # 2. "About Acme" / "About Acme Corp" section header (standalone line)
    m = re.search(r"^about\s+([A-Z][A-Za-z0-9&.,' -]{1,40})\s*$", head, re.IGNORECASE | re.MULTILINE)
    if m:
        candidate = m.group(1).strip()
        if candidate.lower() not in ("us", "the role", "the job", "the team", "the company"):
            return candidate.replace(" ", "")

    # 3. "at Acme" in the first sentence / job title line
    m = re.search(r"\bat\s+([A-Z][A-Za-z0-9&.,' -]{2,35})(?:\s*[,|–\-\n]|$)", head)
    if m:
        candidate = m.group(1).strip()
        if candidate.lower() not in ("least", "most", "all", "a", "the", "this", "our"):
            return candidate.replace(" ", "")

    # 4. "Join Acme" / "Join us at Acme"
    m = re.search(r"\bjoin\s+(?:us\s+at\s+)?([A-Z][A-Za-z0-9&.,' -]{2,35})(?:\s*[,!.\n]|$)", head)
    if m:
        return m.group(1).strip().replace(" ", "")

    # 5. Copyright line: "© 2024 Acme Inc" or "Copyright Acme"
    m = re.search(r"(?:©|\(c\)|copyright)\s*\d*\s*([A-Z][A-Za-z0-9&.,' -]{2,35})", head, re.IGNORECASE)
    if m:
        return m.group(1).strip().replace(" ", "")

    # 6. "Source: <url>" header written by fetch_jd.py — fall back to URL extraction
    m = re.match(r"^Source:\s*(https?://\S+)", text, re.IGNORECASE)
    if m:
        return extract_from_url(m.group(1))

    return None


def main():
    if len(sys.argv) < 2:
        print("Usage: extract_company.py <job-url>", file=sys.stderr)
        print("       extract_company.py --from-file <path>", file=sys.stderr)
        sys.exit(1)

    # ── Mode: extract from saved JD file ──────────────────────────────────────
    if sys.argv[1] == "--from-file":
        if len(sys.argv) < 3:
            print("Usage: extract_company.py --from-file <path>", file=sys.stderr)
            sys.exit(1)
        try:
            with open(sys.argv[2], "r", encoding="utf-8") as f:
                text = f.read()
        except Exception as e:
            print(f"[extract_company] Cannot read file: {e}", file=sys.stderr)
            sys.exit(1)

        name = extract_from_text(text)
        if name:
            print(name)
            sys.exit(0)

        print("[extract_company] Could not detect company name from JD text.", file=sys.stderr)
        sys.exit(1)

    # ── Mode: extract from URL ─────────────────────────────────────────────────
    url = sys.argv[1]

    # Try URL patterns first (fast, no network)
    name = extract_from_url(url)
    if name:
        print(name)
        sys.exit(0)

    # Fall back to HTML parsing
    print("[extract_company] URL pattern match failed — fetching page...", file=sys.stderr)
    name = extract_from_html(url)
    if name:
        print(name)
        sys.exit(0)

    print("[extract_company] Could not detect company name from URL or page.", file=sys.stderr)
    sys.exit(1)


if __name__ == "__main__":
    main()
