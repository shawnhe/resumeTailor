#!/usr/bin/env python3
"""
generate_prep_pdf.py — Render interview prep content as a formatted PDF.

Usage:
    python3 generate_prep_pdf.py <content-file> <output-pdf> <company-name>

The content file should contain labeled sections in this format:
    TAGLINE: ...
    OVERVIEW: ...
    PRODUCTS: ...
    TECH_STACK: ...
    RECENT_NEWS: ...
    ENGINEERING_CULTURE: ...
    INTERVIEW_FOCUS: ...
    ALIGNMENT: ...
    QUESTIONS_TO_ASK: ...
"""

import sys
import re
import unicodedata

try:
    from fpdf import FPDF
except ImportError:
    print("ERROR: fpdf2 not installed. Run: pip install fpdf2", file=sys.stderr)
    sys.exit(1)


# ── Section display config ─────────────────────────────────────────────────────
SECTIONS = [
    ("TAGLINE",            "Company Tagline"),
    ("OVERVIEW",           "Company Overview"),
    ("PRODUCTS",           "Key Products & Services"),
    ("TECH_STACK",         "Technology Stack"),
    ("RECENT_NEWS",        "Recent News & Updates"),
    ("ENGINEERING_CULTURE","Engineering Culture & Values"),
    ("INTERVIEW_FOCUS",    "Interview Focus Areas"),
    ("ALIGNMENT",          "Your Background Alignment"),
    ("QUESTIONS_TO_ASK",   "Questions to Ask the Interviewer"),
]

SECTION_KEYS = {k for k, _ in SECTIONS}

# Header colors: dark navy for title bar, light grey for section bars
COLOR_TITLE_BG  = (30,  50,  90)   # dark navy
COLOR_TITLE_FG  = (255, 255, 255)  # white
COLOR_SECTION_BG= (235, 238, 245)  # light blue-grey
COLOR_SECTION_FG= (30,  50,  90)   # dark navy
COLOR_BODY      = (40,  40,  40)   # near-black


def sanitize(text: str) -> str:
    """Replace non-latin1 characters with ASCII equivalents for fpdf."""
    replacements = {
        "\u2014": "-", "\u2013": "-", "\u2012": "-",  # dashes
        "\u2018": "'", "\u2019": "'",                  # curly singles
        "\u201c": '"', "\u201d": '"',                  # curly doubles
        "\u2022": "*", "\u2023": "*", "\u25cf": "*",   # bullets
        "\u2026": "...",                               # ellipsis
        "\u00a0": " ",                                 # non-breaking space
    }
    for src, dst in replacements.items():
        text = text.replace(src, dst)
    # Drop any remaining non-latin1 chars
    return text.encode("latin-1", errors="replace").decode("latin-1")


def parse_sections(content: str) -> dict:
    """Parse labeled sections from content string.

    Handles both strict 'KEY: value' and loose output from LLMs that may
    include markdown formatting or extra whitespace.
    """
    result = {}
    current_key = None
    current_lines = []

    for line in content.splitlines():
        # Strip markdown bold/italic markers
        line = re.sub(r'\*{1,3}', '', line).strip()

        # Match section key at start of line
        m = re.match(r'^([A-Z_]{4,25}):\s*(.*)', line)
        if m and m.group(1) in SECTION_KEYS:
            if current_key:
                result[current_key] = "\n".join(current_lines).strip()
            current_key = m.group(1)
            current_lines = [m.group(2)] if m.group(2).strip() else []
        elif current_key is not None:
            current_lines.append(line)

    if current_key:
        result[current_key] = "\n".join(current_lines).strip()

    return result


class PrepPDF(FPDF):
    def __init__(self, company: str):
        super().__init__()
        self.company = company
        self.set_auto_page_break(auto=True, margin=18)
        self.set_margins(18, 18, 18)

    def header(self):
        # Title bar on first page only
        if self.page_no() == 1:
            self.set_fill_color(*COLOR_TITLE_BG)
            self.set_text_color(*COLOR_TITLE_FG)
            self.set_font("Helvetica", "B", 16)
            self.cell(0, 10, sanitize(f"Interview Prep: {self.company}"), align="C",
                      new_x="LMARGIN", new_y="NEXT", fill=True)
            self.set_font("Helvetica", "", 9)
            # Optional: candidate info can be passed here
            # self.cell(0, 6, candidate_info, align="C", new_x="LMARGIN", new_y="NEXT", fill=True)
            self.set_text_color(*COLOR_BODY)
            self.ln(4)

    def section_heading(self, title: str):
        self.set_fill_color(*COLOR_SECTION_BG)
        self.set_text_color(*COLOR_SECTION_FG)
        self.set_font("Helvetica", "B", 10)
        self.cell(0, 6, sanitize(f"  {title}"), new_x="LMARGIN", new_y="NEXT", fill=True)
        self.set_text_color(*COLOR_BODY)
        self.ln(1)

    def body_text(self, text: str):
        self.set_font("Helvetica", "", 9)
        for line in text.splitlines():
            line = line.strip()
            if not line:
                self.ln(2)
                continue
            # Convert dash-bullet variants to a clean bullet
            if re.match(r'^[-*\u2022\u2023]\s+', line):
                line = "\u2022 " + re.sub(r'^[-*\u2022\u2023]\s+', '', line)
            # Numbered list items — keep as-is
            self.set_x(self.l_margin + 3)
            self.multi_cell(0, 5, sanitize(line), new_x="LMARGIN", new_y="NEXT")
        self.ln(2)


def score_banner(pdf: "PrepPDF", score: str, matched_frac: str, verdict: str):
    """Render a match-score banner directly below the title bar."""
    # Pick background colour by verdict
    verdict_upper = verdict.upper()
    if verdict_upper == "AUTO_PROCEED":
        bg   = (34,  139, 34)   # green
        label = f"AUTO-PROCEED  ({score}/100  |  {matched_frac} requirements)"
    elif verdict_upper == "CONFIRM":
        bg   = (200, 120,  0)   # amber
        label = f"CONFIRM  ({score}/100  |  {matched_frac} requirements)"
    else:
        bg   = (180,  40,  40)  # red
        label = f"SKIP  ({score}/100  |  {matched_frac} requirements)"

    pdf.set_fill_color(*bg)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 7, sanitize(f"  JD Match Score:  {label}"),
             new_x="LMARGIN", new_y="NEXT", fill=True)
    pdf.set_text_color(*COLOR_BODY)
    pdf.ln(3)


def generate(content_file: str, output_path: str, company: str,
             score: str = "", matched_frac: str = "", verdict: str = ""):
    with open(content_file, "r", encoding="utf-8") as f:
        raw = f.read()

    sections = parse_sections(raw)

    # If structured parsing yielded nothing, render raw content as a single section
    if not sections:
        sections = {"OVERVIEW": raw}

    pdf = PrepPDF(company)
    pdf.add_page()

    # Score banner — shown only when score data was provided
    if score and verdict:
        score_banner(pdf, score, matched_frac, verdict)

    for key, display in SECTIONS:
        text = sections.get(key, "").strip()
        if not text:
            continue
        pdf.section_heading(display)
        pdf.body_text(text)

    pdf.output(output_path)
    print(f"OK: Prep PDF saved to {output_path}")


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: generate_prep_pdf.py <content-file> <output-pdf> <company-name> "
              "[score] [matched_frac] [verdict]",
              file=sys.stderr)
        sys.exit(1)

    generate(
        sys.argv[1], sys.argv[2], sys.argv[3],
        score       = sys.argv[4] if len(sys.argv) > 4 else "",
        matched_frac= sys.argv[5] if len(sys.argv) > 5 else "",
        verdict     = sys.argv[6] if len(sys.argv) > 6 else "",
    )
