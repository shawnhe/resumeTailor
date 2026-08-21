#!/usr/bin/env python3
"""
render_table.py — Render the three-column match score table.

Usage:
    render_table.py <score-output-file> <score> <matched-frac> <verdict>
"""

import sys
import unicodedata

score_file   = sys.argv[1]
score        = sys.argv[2]
frac         = sys.argv[3]
verdict      = sys.argv[4]

with open(score_file, "r", encoding="utf-8") as f:
    raw = f.read()

import re

# Parse ROW lines — handles both pipe-separated and space-separated formats.
# Pipe:  ROW: JD req | Evidence | MATCH
# Space: ROW: JD req   Evidence   MATCH  (AI sometimes uses 2+ spaces)
rows = []
for line in raw.splitlines():
    line = line.strip()
    if not line.upper().startswith("ROW:"):
        continue
    content = line[4:].strip()

    # Try pipe separator first
    if "|" in content:
        parts = [p.strip() for p in content.split("|")]
        if len(parts) == 3:
            rows.append(parts)
        continue

    # Fallback: MATCH or GAP is always the last token
    m = re.search(r'\b(MATCH|GAP)\s*$', content, re.IGNORECASE)
    if not m:
        continue
    verdict_cell = m.group(1).upper()
    remainder = content[:m.start()].strip()

    # Split remainder on 2+ spaces to separate JD req from evidence
    parts = re.split(r' {2,}', remainder)
    if len(parts) >= 2:
        jd_req   = parts[0].strip()
        evidence = " ".join(parts[1:]).strip()
    else:
        jd_req   = remainder
        evidence = ""
    rows.append([jd_req, evidence, verdict_cell])

verdict_label = {
    "AUTO_PROCEED": "✅  AUTO-PROCEED",
    "CONFIRM":      "⚠️   CONFIRM",
    "SKIP":         "🚫  SKIP",
}.get(verdict, verdict)

C1, C2, C3 = 32, 38, 10


def vw(s):
    return sum(2 if unicodedata.east_asian_width(c) in ("W", "F") else 1 for c in s)


def pad(s, w):
    return s + " " * max(0, w - vw(s))


def trunc(s, w):
    out, total = "", 0
    for c in s:
        cw = 2 if unicodedata.east_asian_width(c) in ("W", "F") else 1
        if total + cw > w - 1:
            return out + "…"
        out += c
        total += cw
    return out


div = f"├{'─'*(C1+2)}┼{'─'*(C2+2)}┼{'─'*(C3+2)}┤"
top = f"┌{'─'*(C1+2)}┬{'─'*(C2+2)}┬{'─'*(C3+2)}┐"
bot = f"└{'─'*(C1+2)}┴{'─'*(C2+2)}┴{'─'*(C3+2)}┘"
total_w = C1 + C2 + C3 + 8  # inner width across all cols + separators

print()
print(top)
# Derive match count from actual ROW data — LLM-supplied MATCHED= is often inconsistent
matched_count = sum(1 for _, _, vc in rows if vc.upper() == "MATCH")
actual_frac = f"{matched_count}/{len(rows)}" if rows else frac
summary = f"  🎯  Score: {score}/100   ({actual_frac} requirements)   Verdict: {verdict_label}"
print(f"│ {pad(summary, total_w - 1)}│")
print(div)
print(f"│ {pad('JD Requirement', C1)} │ {pad('Resume Evidence', C2)} │ {pad('Verdict', C3)} │")
print(div)

if not rows:
    msg = "  (No ROW data returned by scorer — re-run to retry)"
    print(f"│ {pad(msg, total_w - 1)}│")
else:
    for jd, ev, vc in rows:
        icon = "✅ Match" if vc.upper() == "MATCH" else "❌ Gap  "
        print(f"│ {pad(trunc(jd, C1), C1)} │ {pad(trunc(ev, C2), C2)} │ {pad(icon, C3)} │")

print(bot)
print()
# Emit machine-readable line for bash to capture (printed to stdout, filtered from display)
print(f"ACTUAL_FRAC={actual_frac}")
