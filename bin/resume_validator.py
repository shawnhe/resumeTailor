#!/usr/bin/env python3
"""
Resume Validator - Mechanical enforcement of resume rules + ATS hard rules.

CONTENT RULES (hard failures — exit 1):
- Rule 6:   NO metrics (25+, 4,300+, commit counts, repo counts, etc.)
- Rule 6a:  NO PR review bullets ("Reviewed and approved PRs")
- Rule 10:  ALL bullets must be sourced from comprehensive resume
- Internal: WCNP/DARPA/OneOps/Strati/CCM banned from tailored resumes

ATS HARD RULES (warnings — non-blocking, but must fix before portal submission):
- ATS-H1: Standard section headings only ("Experience"/"Work Experience", "Education", "Skills", "Summary")
- ATS-H2: Single-column layout (manual check — documented, not auto-detectable)
- ATS-H3: Contact info in body text only — NOT in header/footer margins
- ATS-H4: Acronyms spelled out alongside abbreviations ("Kubernetes (K8s)", "CI/CD")
- ATS-H5: No tables or text boxes in DOCX generation
- ATS-H6: Work dates must include months (e.g., "June 2022 - May 2026"), not year-only
"""

import re
import sys
from pathlib import Path


# ──────────────────────────────────────────────────────────────────────────────
# ATS configuration
# ──────────────────────────────────────────────────────────────────────────────

# ATS-H1: Accepted standard section names.
# Required sections: experience, education, skills.
# Optional but allowed: summary, certificates, awards, patents, publications, projects.
# Creative/non-standard names (e.g., "My Journey", "Superpowers") are flagged.
ATS_STANDARD_SECTIONS = {
    "summary":      ["Summary", "Professional Summary", "Profile", "About"],
    "skills":       ["Skills", "Technical Skills", "Core Skills", "Core Competencies",
                     "Technologies", "Expertise"],
    "experience":   ["Experience", "Work Experience", "Professional Experience",
                     "Employment", "Career History"],
    "education":    ["Education", "Academic Background"],
    "certificates": ["Certificates", "Certifications", "Credentials", "Training",
                     "Licenses & Certifications"],
    "awards":       ["Awards", "Awards & Recognition", "Honors", "Achievements"],
    "patents":      ["Patents", "Publications", "Research"],
    "projects":     ["Projects", "Key Projects", "Side Projects"],
}
# Flatten to a set of all accepted names (lowercase)
ATS_ALL_ACCEPTED_HEADINGS = {
    name.lower()
    for names in ATS_STANDARD_SECTIONS.values()
    for name in names
}
ATS_REQUIRED_SECTION_KEYS = ["experience", "education", "skills"]  # Summary optional but recommended

# ATS-H4: Abbreviation → required full-form substring.
# Both forms must appear in the resume (abbreviation in context of full form or vice versa).
# Entries marked exempt are universally understood and don't need expansion.
ATS_ACRONYM_PAIRS = [
    # (abbreviation, full_form_substring, exempt_from_expansion)
    ("K8s",    "Kubernetes",                          False),
    ("CI/CD",  "Continuous Integration",              False),
    ("MCP",    "Model Context Protocol",              False),
    ("CDC",    "Change Data Capture",                 False),
    ("OTel",   "OpenTelemetry",                       False),
    ("SCA",    "Strong Customer Authentication",      False),
    ("PSD2",   "Payment Services Directive",          False),
    ("SOX",    "Sarbanes",                            True),   # universally known in finance
    ("LDAP",   "Lightweight Directory",               True),   # universally known in tech
    ("API",    "Application Programming Interface",   True),   # universally known
    ("ML",     "Machine Learning",                    True),   # universally known
    ("AWS",    "Amazon Web Services",                 True),   # universally known
    ("GCP",    "Google Cloud Platform",               True),   # universally known
]

# ATS-H6: Pattern for year-only date ranges (e.g., "2009 - 2019", "1999 - 2001")
# These lack months, which can cause ATS parsing errors for total experience calculation.
ATS_YEAR_ONLY_DATE_PATTERN = r'"dates":\s*"(\d{4})\s*[-–]\s*(\d{4})"'


# ──────────────────────────────────────────────────────────────────────────────
# Summary banned patterns (Option A — hard failures)
# These are JD-injection phrases that have been found in tailored summaries but
# are NOT grounded in resume-comprehensive.md.  Add new entries as discovered.
# Format: (regex_pattern, human_label_with_suggested_fix)
# ──────────────────────────────────────────────────────────────────────────────
SUMMARY_BANNED_PATTERNS = [
    (r'\bfull[- ]?stack\b',
     "full-stack (not in comprehensive — use 'backend platform engineering' or 'distributed systems')"),
    (r'\bcross[- ]?functional\b',
     "cross-functional (not in comprehensive — describe coordination specifically, e.g. 'coordinated 15+ downstream teams')"),
    (r'\bvisionarY\b',
     "visionary (buzzword not in comprehensive)"),
    (r'\bthought leader\b',
     "thought leader (buzzword not in comprehensive)"),
    (r'\bend[- ]to[- ]end\b',
     "end-to-end (not in comprehensive summary — use specific ownership language)"),
]


# ──────────────────────────────────────────────────────────────────────────────
# Core helper functions
# ──────────────────────────────────────────────────────────────────────────────

def load_comprehensive():
    """Load comprehensive resume as single source of truth."""
    comp_path = Path(__file__).parent / "resume-comprehensive.md"
    if not comp_path.exists():
        print(f"ERROR: Comprehensive resume not found at {comp_path}")
        sys.exit(1)
    with open(comp_path, 'r') as f:
        return f.read()


def read_script(script_path):
    """Read entire script content."""
    with open(script_path, 'r') as f:
        return f.read()


def extract_all_quoted_text(content):
    """Extract all double-quoted string content from a Python script."""
    return ' '.join(re.findall(r'"([^"]*)"', content))


def extract_bullets_from_script(script_path):
    """Extract bullet strings (those containing trigger verbs) from the script.

    Only searches AFTER the SKILLS dict so that SUMMARY sentences are excluded.
    The SUMMARY is a synthesized narrative, not bullet content — it should not be
    checked against the comprehensive resume line-by-line.

    Guard against cross-boundary matches: [^"]* can span newlines, so a closing "
    from one string is reused as an opening " for the next match when a trigger verb
    appears in a comment between two string literals.  Two extra guards prevent this:
      1. The bullet must start with an alphabetic character (rejects captures like
         '),\\n}\\n\\n# comment...' that begin with code punctuation).
      2. The bullet length is capped at 500 chars (real bullets are < 300 chars).
    """
    content = read_script(script_path)

    # Skip SUMMARY: only validate bullets that appear after SKILLS = {
    skills_start = content.find("SKILLS = {")
    if skills_start != -1:
        content = content[skills_start:]

    bullets = []
    pattern = (r'"([^"]*(?:Led|Built|Designed|Implemented|Architected|Managed|Created|'
               r'Developed|Resolved|Drove|Mentored|Championed|Established|Standardized|'
               r'Democratized|Addressed)[^"]*)"')
    for match in re.finditer(pattern, content):
        bullet = match.group(1).strip()
        if bullet and len(bullet) > 20 and len(bullet) <= 500 and bullet[0].isalpha():
            bullets.append(bullet)
    return bullets


def normalize_for_search(text):
    """Normalize text for fuzzy matching."""
    text = text.lower().strip()
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'[—–‐]', '-', text)
    text = re.sub(r'[""\'\'`]', '"', text)
    return text


def extract_skills_from_script(content):
    """
    Extract {category_name: combined_skills_text} from SKILLS = {...} block.
    Handles multi-line string concatenation (adjacent string literals joined by +).
    Returns empty dict if no SKILLS block found.
    """
    skills_match = re.search(r'\bSKILLS\s*=\s*\{(.*?)\n\}', content, re.DOTALL)
    if not skills_match:
        return {}

    block = skills_match.group(1)

    # Find category key positions: "CategoryName": ...
    key_re = re.compile(r'"([^"]{2,60})":\s*')
    key_positions = [(m.start(), m.end(), m.group(1)) for m in key_re.finditer(block)]

    result = {}
    for i, (key_start, key_end, key_name) in enumerate(key_positions):
        val_end = key_positions[i + 1][0] if i + 1 < len(key_positions) else len(block)
        val_section = block[key_end:val_end]
        # Collect all quoted strings from value section (handles string concatenation)
        val_strings = re.findall(r'"([^"]*)"', val_section)
        result[key_name] = ' '.join(val_strings)

    return result


def extract_summary_from_script(content):
    """
    Extract the SUMMARY string value from the generator script.
    Handles both single-line and parenthesized multi-part concatenation.
    Tries parenthesized form first (more specific), then single-string fallback.
    Returns the full summary string, or None if not found.
    """
    # Parenthesized concatenation first: SUMMARY = ("..." "..." ...)
    # Use a greedy match up to the closing ) that follows a quote
    paren = re.search(r'SUMMARY\s*=\s*\((.*?)\n\)', content, re.DOTALL)
    if paren:
        parts = re.findall(r'"([^"]+)"', paren.group(1))
        if parts:
            return ' '.join(parts)
    # Single string fallback: SUMMARY = "..."
    single = re.search(r'SUMMARY\s*=\s*"([^"]{20,})"', content)
    if single:
        return single.group(1)
    return None


def check_summary_content(content):
    """
    Option A: Scan the SUMMARY string for JD-injected terms not grounded in the
    comprehensive resume.  Uses SUMMARY_BANNED_PATTERNS — a targeted list of
    phrases that have been found in tailored summaries but should never appear.

    Hard failures (exit 1) — same severity as Rule 10 bullet violations.
    Add new entries to SUMMARY_BANNED_PATTERNS as new JD-injection patterns are discovered.
    """
    summary = extract_summary_from_script(content)
    if not summary:
        return []  # No SUMMARY found — nothing to check

    failures = []
    for pattern, label in SUMMARY_BANNED_PATTERNS:
        if re.search(pattern, summary, re.IGNORECASE):
            failures.append(
                f"Rule 10 (Summary): JD-injected term detected — {label}"
            )
    return failures


def check_rule_10_skills(content, comprehensive):
    """
    Rule 10 (Skills): Every individual skill item must be traceable to the
    comprehensive resume. Fabricated skills added to match a JD — not present
    anywhere in the comprehensive — are hard failures.

    Exemptions:
      - ATS full-form expansions: 'Model Context Protocol' is allowed because
        its abbreviation 'MCP' appears in the comprehensive experience section
      - Parenthetical qualifiers stripped before matching:
        'PHP (working knowledge)' → match 'PHP'
      - Multi-word items: pass if ALL significant words (len > 3) appear in comp

    Returns list of (category, raw_item, clean_item) failure tuples.
    """
    skills_dict = extract_skills_from_script(content)
    if not skills_dict:
        return []

    comp_lower = normalize_for_search(comprehensive)

    # ATS full-form → abbreviation that suffices as evidence in comprehensive
    ats_full_forms = {
        "model context protocol":         "mcp",
        "kubernetes":                     "k8s",
        "continuous integration":         "ci/cd",
        "continuous delivery":            "ci/cd",
        "change data capture":            "cdc",
        "strong customer authentication": "sca",
        "payment services directive":     "psd2",
    }

    failures = []

    for category, skills_text in skills_dict.items():
        raw_items = [item.strip() for item in skills_text.split(',')]

        for raw_item in raw_items:
            if not raw_item or len(raw_item) < 3:
                continue

            # Strip parenthetical qualifiers for matching
            clean = re.sub(r'\s*\([^)]*\)', '', raw_item).strip()
            if not clean or len(clean) < 3:
                continue

            clean_lower = clean.lower()

            # Exemption: ATS full-form expansion of a known abbreviation in comp
            if any(full in clean_lower and abbrev in comp_lower
                   for full, abbrev in ats_full_forms.items()):
                continue

            # Exact substring match anywhere in comprehensive
            if clean_lower in comp_lower:
                continue

            # Multi-word fallback: all significant words (len > 3) appear in comp
            # Use word boundaries to prevent 'rest' matching inside 'restoring', etc.
            words = clean_lower.split()
            significant = [w for w in words if len(w) > 3]
            if significant and all(
                re.search(r'\b' + re.escape(w) + r'\b', comp_lower)
                for w in significant
            ):
                continue

            failures.append((category, raw_item, clean))

    return failures


# ──────────────────────────────────────────────────────────────────────────────
# Content rules (hard failures)
# ──────────────────────────────────────────────────────────────────────────────

def check_rule_6_metrics(bullet):
    """Rule 6: NO metrics in tailored resumes."""
    metric_patterns = [
        r'\d+\+\s+(?:repositories|repos|commits|files)',
        r'(?:across|led)\s+\d+\+\s+repositories',
        r'\d+,\d+\+\s+commits',
        r'\d+\+\s+engineers',
        r'\d+\s+(?:commits|contributions)',
    ]
    for pattern in metric_patterns:
        m = re.search(pattern, bullet, re.IGNORECASE)
        if m:
            return False, f"Rule 6 violation: Contains metric '{m.group()}'"
    return True, None


def check_rule_6a_pr_reviews(bullet):
    """Rule 6a: NO PR review bullets."""
    pr_patterns = [
        r'reviewed.*approved.*pr',
        r'code review.*pr',
        r'all prs as technical lead',
    ]
    for pattern in pr_patterns:
        if re.search(pattern, bullet, re.IGNORECASE):
            return False, "Rule 6a violation: PR review bullet (internal/Walmart-specific)"
    return True, None


def check_internal_terms(bullet):
    """Check for Walmart-internal terms banned from tailored resumes."""
    internal_terms = [
        (r'WCNP\b',           "WCNP"),
        (r'\bDARPA\b(?!\s*\()', "DARPA (unexplained)"),
        (r'OneOps\b',         "OneOps"),
        (r'Strati\b',         "Strati"),
        (r'CCM\b',            "CCM"),
    ]
    for pattern, label in internal_terms:
        if re.search(pattern, bullet):
            return False, f"Internal term violation: '{label}' (remove or explain)"
    return True, None


def verify_bullet_in_comprehensive(bullet, comprehensive):
    """Check if bullet content exists in comprehensive resume (Rule 10).

    Three-tier matching (most strict → most lenient):
      1. Exact substring match (normalized).
      2. First-half key-phrase match — the opening clause must appear verbatim.
      3. Word-level match — all significant words (len > 3) appear in the
         comprehensive with word boundaries.  This handles Rule-6 compliant
         rewrites like removing '10+' from 'Mentored 10+ engineers through...'
         while keeping all the key terms that prove the bullet is real content.
    """
    normalized_bullet = normalize_for_search(bullet)
    normalized_comp = normalize_for_search(comprehensive)

    if normalized_bullet in normalized_comp:
        return True, "Exact match"

    words = normalized_bullet.split()
    if len(words) > 5:
        key_phrase = ' '.join(words[:len(words) // 2])
        if key_phrase in normalized_comp:
            return True, f"Partial match: '{key_phrase}'"

    # Tier 3: word-level — all significant words present with word boundaries
    significant = [w for w in words if len(w) > 3 and w.isalpha()]
    if len(significant) >= 5 and all(
        re.search(r'\b' + re.escape(w) + r'\b', normalized_comp)
        for w in significant
    ):
        return True, "Word-level match"

    return False, None


# ──────────────────────────────────────────────────────────────────────────────
# ATS hard rules (warnings — must fix before portal submission)
# ──────────────────────────────────────────────────────────────────────────────

def check_ats_h1_section_names(content):
    """
    ATS-H1: Only standard section headings allowed.
    Checks section_heading("Name") and add_heading_styled(doc, "Name", ...) calls.
    Uses line-safe regex to avoid matching across function call boundaries.
    Returns list of warning strings.
    """
    warnings = []

    # PDF: pdf.section_heading("SectionName") — string must be on same line, ≤50 chars
    pdf_pattern = r'\.section_heading\s*\(\s*"([^"\n]{1,50})"'
    # DOCX: add_heading_styled(doc, "SectionName", level=N) — same-line string arg
    docx_pattern = r'add_heading_styled\s*\(\s*\w+\s*,\s*"([^"\n]{1,50})"'

    found_headings = set()
    for pattern in [pdf_pattern, docx_pattern]:
        for match in re.finditer(pattern, content):
            heading = match.group(1).strip()
            # Skip headings that are clearly sub-headings (contain dates or parens — subsection titles)
            if heading and len(heading) > 0 and '(' not in heading and not re.search(r'\d{4}', heading):
                found_headings.add(heading)

    # Flag any heading not in the accepted whitelist
    for heading in found_headings:
        if heading.lower() not in ATS_ALL_ACCEPTED_HEADINGS:
            warnings.append(
                f"ATS-H1: Non-standard section heading '{heading}' — ATS may miscategorize it. "
                f"Use standard names: Experience/Work Experience, Skills, Education, Summary, "
                f"Certificates, Awards, Patents."
            )

    # Check that required sections are present
    found_lower = {h.lower() for h in found_headings}
    for key in ATS_REQUIRED_SECTION_KEYS:
        valid_names = [n.lower() for n in ATS_STANDARD_SECTIONS[key]]
        if not any(n in found_lower for n in valid_names):
            warnings.append(
                f"ATS-H1: Required section '{ATS_STANDARD_SECTIONS[key][0]}' not found — "
                f"ATS parsers need this standard heading to structure the resume correctly."
            )

    return warnings


def check_ats_h2_single_column(content):
    """
    ATS-H2: Single-column layout required.
    Cannot fully auto-detect layout from Python source, but we can warn
    if multi-column FPDF patterns are detected (e.g., set_x() with large offsets
    combined with parallel cell() calls that imply a column layout).
    Returns list of warning strings.
    """
    warnings = []
    # Heuristic: look for patterns that suggest parallel columns
    # (multiple full-width sections or large x-offset patterns suggesting sidebar)
    if re.search(r'set_x\s*\(\s*(?:self\.w|pdf\.w)\s*/\s*2', content):
        warnings.append(
            "ATS-H2: Possible multi-column layout detected (set_x at page midpoint). "
            "ATS scanners read top-to-bottom; multi-column causes text to parse out of order."
        )

    # Check for Word multi-column section formatting
    if re.search(r'add_section|WD_SECTION|CONTINUOUS', content):
        warnings.append(
            "ATS-H2: Possible multi-section/column Word layout. Use single-column throughout."
        )

    return warnings


def check_ats_h3_contact_not_in_footer(content):
    """
    ATS-H3: Contact info (name, phone, email) must be in body text, NOT in header/footer margins.
    Many ATS systems cannot parse text placed in Word/PDF header or footer margins.
    Checks that footer() method does not contain email/phone/name constants.
    """
    warnings = []

    # Extract the footer method body
    footer_match = re.search(r'def footer\(self\):(.*?)(?=\n    def |\Z)', content, re.DOTALL)
    if footer_match:
        footer_body = footer_match.group(1)

        # Check if contact constants appear in footer
        contact_vars = ["NAME", "PHONE", "EMAIL", "LINKEDIN"]
        for var in contact_vars:
            if re.search(rf'\b{var}\b', footer_body):
                warnings.append(
                    f"ATS-H3: '{var}' appears in PDF footer() method — ATS systems often cannot "
                    f"parse text in footer margins. Move contact info to main body text only."
                )

        # Check for email/phone patterns in footer literal strings
        if re.search(r'[\w.]+@[\w.]+\.\w+|\(\d{3}\)\s*\d{3}[-.\s]\d{4}|\d{3}[-.\s]\d{3}[-.\s]\d{4}',
                     footer_body):
            warnings.append(
                "ATS-H3: Email or phone number found in footer() method — move to body text."
            )

    # Check Word header/footer usage
    if re.search(r'doc\.sections\[.*?\]\.header|doc\.sections\[.*?\]\.footer', content):
        warnings.append(
            "ATS-H3: Word document header/footer used — do not place contact info there. "
            "ATS systems frequently block or fail to parse header/footer margin content."
        )

    return warnings


def check_ats_h4_acronym_pairs(content):
    """
    ATS-H4: Acronyms must appear alongside their full form.
    ATS keyword algorithms may only match one variant. Use both formats:
    e.g., 'Continuous Integration / Continuous Delivery (CI/CD)' or
    'Model Context Protocol (MCP)'.
    Returns list of warning strings.
    """
    warnings = []
    full_text = extract_all_quoted_text(content).lower()

    for abbrev, full_form, exempt in ATS_ACRONYM_PAIRS:
        if exempt:
            continue

        abbrev_present = abbrev.lower() in full_text
        full_form_present = full_form.lower() in full_text

        if abbrev_present and not full_form_present:
            warnings.append(
                f"ATS-H4: '{abbrev}' used without full form '{full_form}' — "
                f"ATS may only match one variant. Add full form at least once "
                f"(e.g., '{full_form} ({abbrev})' in Skills or Summary)."
            )
        elif full_form_present and not abbrev_present:
            # Full form present but no abbreviation — this is actually fine for ATS
            # but note it for completeness if the JD uses the abbreviation
            pass

    return warnings


def check_ats_h5_no_tables(content):
    """
    ATS-H5: No tables or text boxes in DOCX/PDF output.
    Tables (even invisible alignment grids) can cause ATS to strip content,
    leaving blank spaces where skills or job history used to be.
    """
    warnings = []

    # DOCX: check for add_table calls
    if re.search(r'\.add_table\s*\(', content):
        warnings.append(
            "ATS-H5: DOCX add_table() detected — ATS systems frequently strip table content, "
            "leaving blank spaces. Replace with plain paragraphs and bullet lists."
        )

    # DOCX: check for text box / drawing XML
    if re.search(r'txbx|textbox|WD_INLINE_SHAPE|add_picture.*wrap', content, re.IGNORECASE):
        warnings.append(
            "ATS-H5: Text box or inline shape detected in DOCX — ATS parsers cannot read "
            "text inside text boxes. Use body paragraphs only."
        )

    # PDF: check for cell() calls used as table-like grids
    # (multiple cell() calls with fixed widths on same line suggest table layout)
    table_like_pdf = re.findall(
        r'self\.cell\s*\(\s*(?:self\.w|pdf\.w)\s*-\s*[^,]+,', content
    )
    # This is an imperfect heuristic — don't warn on this unless it's clearly columnar

    return warnings


def check_ats_h6_date_format(content):
    """
    ATS-H6: Work dates must include months, not just years.
    Year-only ranges (e.g., "2009 - 2019") cause ATS to miscount total experience
    or flag the entry as potentially hiding employment gaps.
    Recommended format: 'Month YYYY - Month YYYY' or 'MM/YYYY - MM/YYYY'.
    """
    warnings = []

    # Find dates fields that are year-only (e.g., "dates": "2009 - 2019")
    year_only_matches = re.findall(ATS_YEAR_ONLY_DATE_PATTERN, content)

    for start_year, end_year in year_only_matches:
        warnings.append(
            f"ATS-H6: Year-only date '{start_year} - {end_year}' found — include months "
            f"(e.g., 'January {start_year} - December {end_year}') so ATS can accurately "
            f"calculate total years of experience. Year-only ranges can cause parsing errors."
        )

    return warnings


def run_ats_checks(script_path, bullets, content):
    """
    Run all ATS hard rule checks and report results.
    All findings are warnings (non-blocking) — but MUST be fixed before portal submission.
    Returns True always (non-blocking).
    """
    print("\n── ATS Hard Rules Check ────────────────────────────────────────────────────")
    print("   Rules: H1 (sections) | H2 (layout) | H3 (contact placement) |")
    print("          H4 (acronyms) | H5 (no tables) | H6 (dates with months)")

    all_warnings = []

    all_warnings.extend(check_ats_h1_section_names(content))
    all_warnings.extend(check_ats_h2_single_column(content))
    all_warnings.extend(check_ats_h3_contact_not_in_footer(content))
    all_warnings.extend(check_ats_h4_acronym_pairs(content))
    all_warnings.extend(check_ats_h5_no_tables(content))
    all_warnings.extend(check_ats_h6_date_format(content))

    # H2 layout is manual — always remind
    print("\n   ℹ  ATS-H2 (single-column layout): Verify visually — the generated DOCX/PDF")
    print("      must not use sidebars or multi-column sections. Current templates are single-column. ✓")

    if all_warnings:
        print(f"\n   ⚠️  {len(all_warnings)} ATS warning(s) — fix before portal submission:")
        for w in all_warnings:
            print(f"   ⚠  {w}")
    else:
        print("\n   ✅ All ATS hard rules passed")

    print("\n   📌 ATS submission tips:")
    print("      • Submit DOCX to online portals (better parsed than PDF)")
    print("      • Submit PDF when emailing directly to a human recruiter")
    print("      • Verify JD keywords appear verbatim in Skills or Summary (ATS-H4)")
    print("      • Contact info must be in body text at top — not in header/footer margins (ATS-H3)")

    return True


# ──────────────────────────────────────────────────────────────────────────────
# Main validation entry point
# ──────────────────────────────────────────────────────────────────────────────

def validate_resume_bullets(script_path):
    """
    Validate all bullets against content rules and run ATS hard rule checks.
    Content violations exit with code 1 (hard failures).
    ATS violations are warnings (non-blocking — must fix before portal submission).
    """
    print(f"📋 Validating resume script: {script_path}")
    print("=" * 80)
    print("Checking: Rule 6 (metrics) | Rule 6a (PR reviews) | Rule 10 (source) | Internal terms\n")

    comprehensive = load_comprehensive()
    content = read_script(script_path)
    bullets = extract_bullets_from_script(script_path)

    if not bullets:
        print("⚠️  No bullets found to validate. Check script format.")
        run_ats_checks(script_path, [], content)
        return True

    print(f"Found {len(bullets)} bullets to verify...\n")

    failed_bullets = []
    passed = 0

    for i, bullet in enumerate(bullets, 1):
        rule6_ok, rule6_msg = check_rule_6_metrics(bullet)
        if not rule6_ok:
            print(f"✗ [{i}/{len(bullets)}] {rule6_msg}")
            print(f"  {bullet}\n")
            failed_bullets.append((bullet, rule6_msg))
            continue

        rule6a_ok, rule6a_msg = check_rule_6a_pr_reviews(bullet)
        if not rule6a_ok:
            print(f"✗ [{i}/{len(bullets)}] {rule6a_msg}")
            print(f"  {bullet}\n")
            failed_bullets.append((bullet, rule6a_msg))
            continue

        internal_ok, internal_msg = check_internal_terms(bullet)
        if not internal_ok:
            print(f"✗ [{i}/{len(bullets)}] {internal_msg}")
            print(f"  {bullet}\n")
            failed_bullets.append((bullet, internal_msg))
            continue

        is_valid, match_type = verify_bullet_in_comprehensive(bullet, comprehensive)
        if is_valid:
            print(f"✓ [{i}/{len(bullets)}] {match_type}")
            print(f"  {bullet[:70]}...")
            passed += 1
        else:
            print(f"✗ [{i}/{len(bullets)}] NOT FOUND IN COMPREHENSIVE (Rule 10)")
            print(f"  {bullet}\n")
            failed_bullets.append((bullet, "Not in comprehensive resume"))

    print("\n" + "=" * 80)
    print(f"Results: {passed}/{len(bullets)} verified")

    if failed_bullets:
        print(f"\n❌ VALIDATION FAILED - {len(failed_bullets)} error(s) found:")
        for bullet, reason in failed_bullets:
            print(f"  ✗ {reason}")
            print(f"    {bullet}\n")
        print("Fix: Remove/reword bullets to pass all rule checks and exist in comprehensive.")
        sys.exit(1)
    else:
        print("✅ ALL BULLETS VERIFIED - All rules passed")

    # Summary content check (Option A — banned JD-injection patterns)
    print("\n── Summary Validation (Rule 10 — banned JD terms) ──────────────────────────")
    summary_failures = check_summary_content(content)
    if summary_failures:
        print(f"❌ SUMMARY VALIDATION FAILED - {len(summary_failures)} fabricated term(s):")
        for f in summary_failures:
            print(f"  ✗ {f}")
        print("\nFix: Remove JD-injected terms from SUMMARY. See SUMMARY_BANNED_PATTERNS in validator.")
        sys.exit(1)
    else:
        print("✅ SUMMARY VERIFIED - No banned JD-injection terms detected")

    # Rule 10 (Skills): Verify all skill items against comprehensive
    print("\n── Skills Validation (Rule 10) ─────────────────────────────────────────────")
    skill_failures = check_rule_10_skills(content, comprehensive)
    if skill_failures:
        print(f"❌ SKILLS VALIDATION FAILED - {len(skill_failures)} fabricated item(s):")
        for category, raw_item, clean in skill_failures:
            print(f"  ✗ [{category}] '{raw_item}' — not found in comprehensive resume")
        print("\nFix: Remove skill items not grounded in the comprehensive resume.")
        sys.exit(1)
    else:
        print("✅ ALL SKILLS VERIFIED - All skill items traced to comprehensive resume")

    # Run ATS hard rule checks (non-blocking)
    run_ats_checks(script_path, bullets, content)

    return True


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 resume_validator.py <script_path>")
        sys.exit(1)
    validate_resume_bullets(sys.argv[1])
