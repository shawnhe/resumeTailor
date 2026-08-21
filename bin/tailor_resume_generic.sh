#!/bin/bash
# tailor_resume_generic.sh — Invoke the resume-tailor agent for any candidate and target company
#
# Usage:
#   ./tailor_resume_generic.sh <job-url> [CompanyName] [--base-resume <path>] [--candidate-name <name>] [--output-dir <dir>] [--force]
#   ./tailor_resume_generic.sh https://jobs.lever.co/acme/abc123 Acme --base-resume ~/resume-comprehensive.md
#   ./tailor_resume_generic.sh https://jobs.lever.co/acme/abc123 Acme --candidate-name "Jane Doe" --output-dir ./companies
#
# Required:
#   <job-url>              Job posting URL
#   --base-resume <path>   Path to comprehensive resume markdown file
#
# Optional:
#   [CompanyName]          Company name (auto-detected from JD if omitted)
#   --candidate-name <name> Candidate name (extracted from resume if omitted)
#   --output-dir <dir>     Output directory (defaults to ./companies)
#   --force                Skip JD match score gate and generate resume anyway
#
# Output layout:
#   <output-dir>/<Company>/
#       <Company>_jd.md            ← raw job description
#       <Company>_resume.pdf       ← tailored PDF
#       <Company>_interview_prep.pdf ← research document (optional)
#   <base-resume-dir>/
#       generate_resume_<company>.py   ← generator script (kept for re-runs)
#       <CandidateName>_Resume_<Company>.docx ← DOCX for portal uploads

set -euo pipefail

_SCRIPT_START=$SECONDS
_START_TIME="$(date '+%Y-%m-%d %H:%M:%S')"
_SPINNER_PID=""   # populated by _spinner_start; read by trap

# ── Ctrl+C / SIGTERM — clean exit ─────────────────────────────────────────────
_cleanup() {
    # Stop spinner if one is running (kills background process + clears line)
    if [ -n "$_SPINNER_PID" ]; then
        kill "$_SPINNER_PID" 2>/dev/null
        wait "$_SPINNER_PID" 2>/dev/null || true
        printf "\r\033[2K" >&2
    fi
    echo "" >&2
    echo "🛑  Interrupted." >&2
    exit 130
}
trap _cleanup INT TERM

# ── Safety check: prevent running from within companies directory ────────────
CURRENT_DIR="$(pwd)"
if [ "$CURRENT_DIR" = "$(pwd)/companies" ] || echo "$CURRENT_DIR" | grep -q "/companies$"; then
    echo "❌  Error: Run this script from the repository root, not from the companies folder."
    echo "   Current: $CURRENT_DIR"
    echo "   Run from: $(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
    exit 1
fi

# ── Parse arguments ───────────────────────────────────────────────────────────
if [ -z "${1:-}" ]; then
    echo "❌  Usage: $(basename "$0") <job-url> [CompanyName] [--base-resume <path>] [--candidate-name <name>] [--output-dir <dir>] [--force]"
    echo ""
    echo "  Required:"
    echo "    <job-url>              Job posting URL"
    echo "    --base-resume <path>   Path to comprehensive resume markdown"
    echo ""
    echo "  Optional:"
    echo "    [CompanyName]          Company name (auto-detected if omitted)"
    echo "    --candidate-name <name> Candidate name (extracted from resume if omitted)"
    echo "    --output-dir <dir>     Output directory (default: ./companies)"
    echo "    --force                Skip JD match score gate and generate anyway"
    exit 1
fi

# ── Default values ────────────────────────────────────────────────────────────
OUTPUT_DIR="./companies"
BASE_RESUME_PATH=""
CANDIDATE_NAME=""
BIN_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VALIDATOR_PATH="$BIN_DIR/resume_validator.py"  # Use repo copy by default
FORCE=false
JOB_URL=""
COMPANY_NAME=""

# ── Parse flags and positional arguments ────────────────────────────────────────
while [ $# -gt 0 ]; do
    case "$1" in
        --force)
            FORCE=true
            shift
            ;;
        --base-resume)
            BASE_RESUME_PATH="$2"
            shift 2
            ;;
        --candidate-name)
            CANDIDATE_NAME="$2"
            shift 2
            ;;
        --output-dir)
            OUTPUT_DIR="$2"
            shift 2
            ;;
        *)
            # Positional argument (job URL or company name)
            if [ -z "$JOB_URL" ]; then
                JOB_URL="$1"
            elif [ -z "$COMPANY_NAME" ]; then
                COMPANY_NAME="$1"
            fi
            shift
            ;;
    esac
done

# ── Validate required arguments ───────────────────────────────────────────────
if [ -z "$BASE_RESUME_PATH" ]; then
    echo "❌  Error: --base-resume is required. Provide path to comprehensive resume markdown."
    exit 1
fi

if [ ! -f "$BASE_RESUME_PATH" ]; then
    echo "❌  Error: Base resume not found: $BASE_RESUME_PATH"
    exit 1
fi

# ── Extract candidate name from resume if not provided ────────────────────────
if [ -z "$CANDIDATE_NAME" ]; then
    # Try to extract from H1 title line (e.g., "# Shawn He — Staff Software Engineer")
    CANDIDATE_NAME="$(head -5 "$BASE_RESUME_PATH" | grep '^#' | head -1 | sed 's/^#[[:space:]]*//; s/[[:space:]]*—.*//')"

    if [ -z "$CANDIDATE_NAME" ]; then
        echo "❌  Error: Could not extract candidate name from resume. Use --candidate-name <name>"
        exit 1
    fi
fi

# ── Determine base resume directory (where generator script will be written) ──
BASE_RESUME_DIR="$(cd "$(dirname "$BASE_RESUME_PATH")" && pwd)"

# ── Validate positional arguments ──────────────────────────────────────────────
if [ -z "$JOB_URL" ]; then
    echo "❌  Error: job-url is required (pass as last positional argument)."
    exit 1
fi

# Strip LinkedIn tracking query params — only the job ID in the path matters.
# This prevents bash & splitting when users paste unquoted LinkedIn URLs.
if echo "$JOB_URL" | grep -q "linkedin\.com/jobs/view/"; then
    JOB_URL="$(echo "$JOB_URL" | sed 's/?.*//')"
fi

# ── Ensure output directory exists ────────────────────────────────────────────
mkdir -p "$OUTPUT_DIR"

# ── Paths ─────────────────────────────────────────────────────────────────────
BIN_DIR="$(cd "$(dirname "$0")" && pwd)"

# ── Sync validator to base resume directory (where generated script will be) ──
VALIDATION_ENABLED=false
if [ -n "$VALIDATOR_PATH" ] && [ -f "$VALIDATOR_PATH" ]; then
    cp "$VALIDATOR_PATH" "$BASE_RESUME_DIR/resume_validator.py"
    VALIDATION_ENABLED=true
fi

echo "🕐  Started : $_START_TIME"
echo ""

# ── Step 1: Fetch JD to a temp file FIRST ─────────────────────────────────────
# We fetch before asking for the company name so we can extract it from the
# JD content itself — same as the interactive Wibey flow.
TMP_JD="/tmp/tailor_jd_tmp_$$.md"
trap 'rm -f "$TMP_JD"' EXIT

echo ""
echo "📥  Fetching job description..."
FETCH_EXIT=0
python3 "$BIN_DIR/fetch_jd.py" "$JOB_URL" "$TMP_JD" 2>/tmp/fetch_jd_err || FETCH_EXIT=$?

if [ "$FETCH_EXIT" -eq 2 ]; then
    echo "⚠️   $(cat /tmp/fetch_jd_err)"
    echo ""
    echo "    This site requires login. Please paste the job description text below."
    echo "    Paste all content, then press Ctrl+D when done:"
    echo ""
    cat > "$TMP_JD"
    echo ""
    if [ ! -s "$TMP_JD" ]; then
        echo "❌  No content provided. Exiting."
        exit 1
    fi
    echo "✔   JD received ($(wc -w < "$TMP_JD") words)."
elif [ "$FETCH_EXIT" -ne 0 ]; then
    echo "⚠️   Fetch failed: $(cat /tmp/fetch_jd_err)"
    echo "    Paste the job description, then Ctrl+D when done:"
    cat > "$TMP_JD"
    if [ ! -s "$TMP_JD" ]; then
        echo "❌  No content provided. Exiting."
        exit 1
    fi
else
    echo "✔   JD fetched."
fi

# ── Step 2: Extract company name from JD content ──────────────────────────────
if [ -z "$COMPANY_NAME" ]; then
    echo "🔍  Detecting company name from job description..."
    DETECTED="$(python3 "$BIN_DIR/extract_company.py" --from-file "$TMP_JD" 2>/dev/null || true)"

    # Fallback to URL pattern if JD text extraction failed
    if [ -z "$DETECTED" ]; then
        DETECTED="$(python3 "$BIN_DIR/extract_company.py" "$JOB_URL" 2>/dev/null || true)"
    fi

    if [ -z "$DETECTED" ]; then
        echo "⚠️   Could not detect company name automatically."
        printf "    Enter company name manually: "
        read -r COMPANY_NAME
        if [ -z "$COMPANY_NAME" ]; then
            echo "❌  No company name provided. Exiting."
            exit 1
        fi
    else
        echo "🏢  Detected company: $DETECTED"
        printf "    Press Enter to confirm, or type a different name: "
        read -r OVERRIDE
        COMPANY_NAME="${OVERRIDE:-$DETECTED}"
    fi
fi

COMPANY_LOWER="$(echo "$COMPANY_NAME" | tr '[:upper:]' '[:lower:]')"
COMPANY_DIR="$OUTPUT_DIR/$COMPANY_NAME"
mkdir -p "$COMPANY_DIR"

# ── Step 3: Move temp JD to final location ────────────────────────────────────
JD_FILE="$COMPANY_DIR/${COMPANY_NAME}_jd.md"
cp "$TMP_JD" "$JD_FILE"
echo "✔   JD saved: $JD_FILE"

# ── Spinner helper (used for captured wibey calls that produce no visible output) ─
_spinner_start() {
    local msg="${1:-Working...}"
    printf "\n   %s " "$msg" >&2
    (
        chars='⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏'
        while true; do
            for i in 0 1 2 3 4 5 6 7 8 9; do
                printf "\r   %s %s " "$msg" "${chars:$i:1}" >&2
                sleep 0.12
            done
        done
    ) &
    _SPINNER_PID=$!
}
_spinner_stop() {
    kill "$_SPINNER_PID" 2>/dev/null
    wait "$_SPINNER_PID" 2>/dev/null || true   # wait returns 143 (SIGTERM) — suppress with set -e
    printf "\r\033[2K" >&2   # clear the spinner line
}

# ── Match score gate — AI-powered (reads local JD file) ───────────────────────
COMP_RESUME="$BASE_RESUME_PATH"
echo ""
echo "📊  Scoring JD match (AI analysis)..."

# Primary: ask wibey to score — same intelligence as interactive scoring.
# Output format is strict so bash can parse it reliably.
SCORE_PROMPT="You are scoring a job description against a candidate's resume.

Read both files:
  JD:     $JD_FILE
  Resume: $COMP_RESUME

Output ONLY the following lines — no other text, no markdown, no explanations:
SCORE=<integer 0-100>
MATCHED=<matched_count>/<total_rows>
VERDICT=<AUTO_PROCEED if score>=80, CONFIRM if 60-79, SKIP if <60>
ROW: <JD requirement> | <evidence from resume, or 'Not found'> | <MATCH or GAP>
ROW: <JD requirement> | <evidence from resume, or 'Not found'> | <MATCH or GAP>
... (8-14 rows total covering key JD requirements)

Rules:
- You MUST output 8-14 ROW lines. Do not skip them. They are required.
- ROW column 1: specific requirement from the JD (skill, experience, domain, seniority)
- ROW column 2: specific evidence from the resume that satisfies it, or 'Not found'
- ROW column 3: MATCH if the resume satisfies it, GAP if it does not
- Cover both technical and non-technical requirements
- Score 80+: strong fit (auto-proceed). 60-79: moderate (ask). <60: poor (skip)
- Be honest and specific — a score above 90 should be rare
- Do not add any text outside the specified format"

_spinner_start "Analyzing JD and resume..."
SCORE_EXIT=0
SCORE_RAW="$(wibey -p "$SCORE_PROMPT" --response-style verbose 2>&1)" || SCORE_EXIT=$?
_spinner_stop

# Strip ANSI/TUI escape sequences (wibey outputs terminal codes even in headless mode)
SCORE_OUTPUT="$(printf '%s' "$SCORE_RAW" | python3 -c "
import sys, re
raw = sys.stdin.read()
clean = re.sub(r'\x1b\[[0-9;?]*[a-zA-Z]', '', raw)
clean = re.sub(r'\x1b\][^\x07\x1b]*(?:\x07|\x1b\\\\)', '', clean)
clean = re.sub(r'\x1b.', '', clean)
print(clean, end='')
")"

# Save cleaned output for debugging
echo "$SCORE_OUTPUT" > "/tmp/last_score_output.txt"

if [ "$SCORE_EXIT" -ne 0 ] || ! echo "$SCORE_OUTPUT" | grep -q '^SCORE='; then
    echo "❌  Match score could not be generated (system error)."
    echo "    Raw output saved to: /tmp/last_score_output.txt"
    echo "    Please check that wibey is running correctly and try again."
    exit 1
fi

MATCH_SCORE="$(echo "$SCORE_OUTPUT" | grep '^SCORE=' | cut -d= -f2)"
MATCHED_FRAC="$(echo "$SCORE_OUTPUT" | grep '^MATCHED=' | cut -d= -f2)"
VERDICT="$(echo "$SCORE_OUTPUT" | grep '^VERDICT=' | cut -d= -f2)"

# ── Render three-column match table ───────────────────────────────────────────
# Write score output to a temp file to avoid heredoc variable-substitution issues
SCORE_TMP="/tmp/score_output_$$.txt"
printf '%s' "$SCORE_OUTPUT" > "$SCORE_TMP"

# render_table.py prints the table and also outputs ACTUAL_FRAC=x/y to stdout
# so bash can use the row-derived count (consistent with what was displayed)
TABLE_OUT="$(python3 "$BIN_DIR/render_table.py" "$SCORE_TMP" "$MATCH_SCORE" "$MATCHED_FRAC" "$VERDICT")"
printf '%s\n' "$TABLE_OUT"
ACTUAL_FRAC="$(printf '%s\n' "$TABLE_OUT" | grep '^ACTUAL_FRAC=' | cut -d= -f2)"
[ -n "$ACTUAL_FRAC" ] && MATCHED_FRAC="$ACTUAL_FRAC"
rm -f "$SCORE_TMP"

# ── Decision logic based on score ─────────────────────────────────────────────
if [ "$FORCE" = true ]; then
    echo "⚡  --force flag set — bypassing score gate (score: $MATCH_SCORE/100)."
elif [ "$VERDICT" = "SKIP" ]; then
    echo "🚫  Score $MATCH_SCORE/100 is below 60 — skipping resume generation."
    echo "    This JD is not a strong match for the candidate's background."
    echo "    To override and generate anyway, re-run with --force:"
    echo "    $(basename "$0") --force \"$JOB_URL\" \"$COMPANY_NAME\""
    exit 0
elif [ "$VERDICT" = "AUTO_PROCEED" ]; then
    echo "✅  Score $MATCH_SCORE/100 ≥ 80 — proceeding automatically."
elif [ "$VERDICT" = "CONFIRM" ]; then
    echo "⚠️   Score $MATCH_SCORE/100 is between 60–79 — moderate match."
    printf "    Generate resume anyway? [y/N]: "
    read -r CONFIRM
    case "$(echo "$CONFIRM" | tr '[:upper:]' '[:lower:]')" in
        y|yes) echo "▶   Confirmed. Proceeding with generation." ;;
        *)     echo "🚫  Skipped. No files generated."
               exit 0 ;;
    esac
fi

# ── Summary ───────────────────────────────────────────────────────────────────
echo ""
echo "🏢  Company   : $COMPANY_NAME"
echo "🔗  JD URL    : $JOB_URL"
echo "📁  Output dir: $COMPANY_DIR"
echo "👤  Candidate : $CANDIDATE_NAME"
echo ""
echo "🚀  Invoking resume-tailor agent (Phase 1 of 2: writing generator script)..."
echo "    Steps: read JD → read comprehensive resume → select bullets → write script"
echo "    Expected time: 45–90 seconds."
echo "──────────────────────────────────────────────"

# ── Build prompt ───────────────────────────────────────────────────────────────
# The phrase "tailor my resume for" triggers the .wibey:resume-tailor agent.
# All path instructions are passed explicitly so the agent saves to the right places.
SCRIPT_PATH="$BASE_RESUME_DIR/generate_resume_${COMPANY_LOWER}.py"

# ── Phase 1: Agent writes the generator script (script only — no execution) ───
# Separating script-writing from execution keeps the session short enough
# to complete without hitting the headless turn limit.
PROMPT="Generate a tailored resume generator script for $COMPANY_NAME.

Files:
- Job description: $JD_FILE
- Comprehensive resume: $COMP_RESUME
- Output script: $SCRIPT_PATH
- Candidate: $CANDIDATE_NAME

Instructions:
1. Read both files
2. Select 18-22 most relevant bullets (2-page limit)
3. Reorder by JD relevance
4. Write Python script with:
   - Import: from resume_validator import validate_resume_bullets
   - Main: calls validate_resume_bullets(), generate_docx(), generate_pdf()
5. Output filenames:
   - PDF: $BASE_RESUME_DIR/${CANDIDATE_NAME// /}_${COMPANY_NAME}.pdf
   - DOCX: $BASE_RESUME_DIR/${CANDIDATE_NAME// /}_${COMPANY_NAME}.docx

Done. Report: 'Script written: $SCRIPT_PATH'"

# ── Invoke wibey headless (Phase 1) ───────────────────────────────────────────
# Retry logic for socket errors
WIBEY_ATTEMPTS=0
WIBEY_MAX_ATTEMPTS=2
PHASE1_OUTPUT=""
WIBEY_EXIT=1

while [ $WIBEY_ATTEMPTS -lt $WIBEY_MAX_ATTEMPTS ] && [ $WIBEY_EXIT -ne 0 ]; do
    WIBEY_ATTEMPTS=$((WIBEY_ATTEMPTS + 1))

    if [ $WIBEY_ATTEMPTS -gt 1 ]; then
        echo "⚠️   Retry attempt $WIBEY_ATTEMPTS/$WIBEY_MAX_ATTEMPTS..."
    fi

    _spinner_start "Agent working (reading JD + writing script)..."
    WIBEY_EXIT=0
    PHASE1_OUTPUT="$(wibey -p "$PROMPT" --response-style verbose 2>&1)" || WIBEY_EXIT=$?
    _spinner_stop
done

echo "──────────────────────────────────────────────"
echo "$PHASE1_OUTPUT"
echo "──────────────────────────────────────────────"

if [ "$WIBEY_EXIT" -ne 0 ]; then
    echo ""
    echo "❌  Agent (Phase 1) failed after $WIBEY_ATTEMPTS attempt(s)"
    echo "    Error output above ↑"
    exit 1
fi

# ── Safety gate 1: script must exist and contain validator call ────────────────
if [ ! -f "$SCRIPT_PATH" ]; then
    echo ""
    echo "❌  SAFETY FAIL: Generator script not found: $SCRIPT_PATH"
    echo "   The agent did not complete script generation."
    exit 1
fi

if [ "$VALIDATION_ENABLED" = true ] && ! grep -q "validate_resume_bullets" "$SCRIPT_PATH"; then
    echo ""
    echo "❌  SAFETY FAIL: Generator script missing validate_resume_bullets() call!"
    echo "   File: $SCRIPT_PATH"
    exit 1
fi

echo "✔   Generator script written."
if [ "$VALIDATION_ENABLED" = true ]; then
    echo "✔   Script contains validator call."
fi

# ── Phase 2: Validate → auto-fix loop → generate ─────────────────────────────
# Run the validator standalone first (no generation yet) — only if validation enabled.
# If it fails, call wibey to fix the script, then re-validate.
# Only generate after a clean validation pass.

if [ "$VALIDATION_ENABLED" = true ]; then

    MAX_FIX_ATTEMPTS=2
    FIX_ATTEMPT=0
    VALIDATION_PASSED=false

    while [ $FIX_ATTEMPT -le $MAX_FIX_ATTEMPTS ]; do
        echo ""
        if [ $FIX_ATTEMPT -eq 0 ]; then
            echo "🔍  Running validation (Phase 2)..."
        else
            echo "🔍  Re-validating after fix (attempt $FIX_ATTEMPT/$MAX_FIX_ATTEMPTS)..."
        fi

        VALIDATION_TMP="/tmp/validation_output_$$.txt"
        VALIDATE_EXIT=0
        # Stream live to terminal AND save to file for fix prompt.
        # pipefail: pipe exits with subshell exit code (tee always exits 0, so
        # rightmost-non-zero = subshell). || captures non-zero without set -e aborting.
        (
            cd "$BASE_RESUME_DIR"
            python3 -c "
import sys
sys.path.insert(0, '$BASE_RESUME_DIR')
from resume_validator import validate_resume_bullets
validate_resume_bullets('$SCRIPT_PATH')
"
        ) 2>&1 | tee "$VALIDATION_TMP" || VALIDATE_EXIT=$?

        if [ "$VALIDATE_EXIT" -eq 0 ]; then
            VALIDATION_PASSED=true
            echo "✔   Validation passed."
            break
        fi

        # Validation failed
        if [ $FIX_ATTEMPT -ge $MAX_FIX_ATTEMPTS ]; then
            echo ""
            echo "❌  Validation still failing after $MAX_FIX_ATTEMPTS fix attempt(s)."
            echo "   Manual fix needed: $SCRIPT_PATH"
            rm -f "$VALIDATION_TMP"
            exit 1
        fi

        FIX_ATTEMPT=$((FIX_ATTEMPT + 1))
        echo ""
        echo "🔧  Validation failed — invoking fix agent (attempt $FIX_ATTEMPT/$MAX_FIX_ATTEMPTS)..."

        FIX_PROMPT="Fix resume validation failures in the generator script.

Script: $SCRIPT_PATH

Validation failures:
$(cat "$VALIDATION_TMP")"

        _spinner_start "Fix agent working (replacing invalid bullets)..."
        WIBEY_FIX_EXIT=0
        FIX_OUTPUT="$(wibey -p "$FIX_PROMPT" --response-style verbose 2>&1)" || WIBEY_FIX_EXIT=$?
        _spinner_stop
        echo "$FIX_OUTPUT"

        if [ "$WIBEY_FIX_EXIT" -ne 0 ]; then
            echo "❌  Fix agent failed. Manual intervention needed."
            echo "   Script:   $SCRIPT_PATH"
            echo "   Failures: $VALIDATION_TMP"
            exit 1
        fi

        rm -f "$VALIDATION_TMP"
    done

fi

# ── Phase 2b: Generate after clean validation (or skip validation if disabled) ─
echo ""
echo "🏗️  Generating resume files..."
GENERATE_EXIT=0
(
    cd "$BASE_RESUME_DIR"
    python3 "$SCRIPT_PATH"
) || GENERATE_EXIT=$?

if [ "$GENERATE_EXIT" -eq 3 ]; then
    echo "📄  Generator reported page limit exceeded — entering trim loop..."
    # PDF was written before the exit; safety gate 4 will handle the trim below
elif [ "$GENERATE_EXIT" -ne 0 ]; then
    echo ""
    echo "❌  Generation failed (exit code: $GENERATE_EXIT)."
    echo "   Re-run manually: cd $BASE_RESUME_DIR && python3 generate_resume_${COMPANY_LOWER}.py"
    exit 1
fi

echo "✔   Resume files generated."

# ── Safety gate 3: verify PDF was actually generated ──────────────────────────
PDF_SRC="$BASE_RESUME_DIR/${CANDIDATE_NAME// /}_${COMPANY_NAME}.pdf"
PDF_DST="$COMPANY_DIR/${CANDIDATE_NAME// /}_${COMPANY_NAME}.pdf"

if [ ! -f "$PDF_SRC" ]; then
    echo ""
    echo "❌  SAFETY FAIL: PDF not generated: $PDF_SRC"
    echo "   Validation passed but generation did not complete."
    echo "   Run manually: cd $BASE_RESUME_DIR && python3 generate_resume_${COMPANY_LOWER}.py"
    exit 1
fi

echo "✔   PDF confirmed at: $PDF_SRC"

# ── Safety gate 4: page count — auto-trim loop ────────────────────────────────
_get_pdf_pages() {
    python3 -c "
from pypdf import PdfReader
print(len(PdfReader('$1').pages))
" 2>/dev/null
}

PDF_PAGES="$(_get_pdf_pages "$PDF_SRC")" || PDF_PAGES=""
MAX_PAGE_FIX=2
PAGE_FIX_ATTEMPT=0

if [ -z "$PDF_PAGES" ]; then
    echo "⚠️   Could not verify page count (pypdf unavailable) — skipping page check."
else
    while [ -n "$PDF_PAGES" ] && [ "$PDF_PAGES" -gt 2 ] 2>/dev/null; do
        PAGE_FIX_ATTEMPT=$((PAGE_FIX_ATTEMPT + 1))
        echo ""
        echo "📄  PDF is $PDF_PAGES pages — trimming to 2 (attempt $PAGE_FIX_ATTEMPT/$MAX_PAGE_FIX)..."

        if [ $PAGE_FIX_ATTEMPT -gt $MAX_PAGE_FIX ]; then
            echo "❌  Still $PDF_PAGES pages after $MAX_PAGE_FIX trim attempt(s). Manual fix needed."
            echo "   Script: $SCRIPT_PATH"
            exit 1
        fi

        PAGE_FIX_PROMPT="The resume generator script produced a PDF that is $PDF_PAGES pages. It must be exactly 2 pages.

Script: $SCRIPT_PATH
PDF: $PDF_SRC
Job description: $JD_FILE

Trim bullets to fit 2 pages. Remove the least relevant bullets based on the JD — relevance takes priority over which employer the bullet came from. Keep at least 1 bullet per employer. Edit the script and save it, then stop — do NOT run the script or check page count yourself."

        _spinner_start "Trim agent reducing bullet count..."
        PAGE_FIX_EXIT=0
        PAGE_FIX_OUTPUT="$(wibey -p "$PAGE_FIX_PROMPT" --response-style verbose 2>&1)" || PAGE_FIX_EXIT=$?
        _spinner_stop
        echo "$PAGE_FIX_OUTPUT"

        if [ "$PAGE_FIX_EXIT" -ne 0 ]; then
            echo "❌  Trim agent failed. Manual fix needed: $SCRIPT_PATH"
            exit 1
        fi

        # Regenerate after trim
        GENERATE_EXIT=0
        ( cd "$BASE_RESUME_DIR" && python3 "$SCRIPT_PATH" ) || GENERATE_EXIT=$?
        if [ "$GENERATE_EXIT" -ne 0 ]; then
            echo "❌  Regeneration after trim failed."
            exit 1
        fi

        PDF_PAGES="$(_get_pdf_pages "$PDF_SRC")" || PDF_PAGES=""
    done

    if [ -n "$PDF_PAGES" ]; then
        echo "✔   Page count: $PDF_PAGES/2"
    fi
fi

# ── Move PDF and DOCX to company dir (always overwrite — keeps output dir as the only copy) ──
cp "$PDF_SRC" "$PDF_DST"
rm -f "$PDF_SRC"

DOCX_SRC="$BASE_RESUME_DIR/${CANDIDATE_NAME// /}_${COMPANY_NAME}.docx"
DOCX_DST="$COMPANY_DIR/${CANDIDATE_NAME// /}_${COMPANY_NAME}.docx"
if [ -f "$DOCX_SRC" ]; then
    cp "$DOCX_SRC" "$DOCX_DST"
    rm -f "$DOCX_SRC"
    echo "✔   DOCX saved to: $DOCX_DST"
else
    echo "⚠️   DOCX not generated (check script output above)"
fi

# ── Phase 3: Interview prep PDF ───────────────────────────────────────────────
# Only run if the resume PDF was actually generated (now lives in company dir).
if [ ! -f "$PDF_DST" ]; then
    echo ""
    echo "ℹ️   Resume PDF not generated — skipping interview prep."
else
echo ""
echo "📚  Generating interview prep document (researching $COMPANY_NAME)..."

PREP_PROMPT="Research the company '$COMPANY_NAME' and generate a structured interview preparation guide for a Staff Software Engineer candidate.

Search the web for current information about $COMPANY_NAME:
- Company overview, mission, and business model
- Core products and services
- Known engineering tech stack and architecture
- Recent news, product launches, or strategic initiatives (last 6-12 months)
- Engineering culture, values, and what they look for in engineers
- Typical interview process and focus areas for Staff/Senior SWE roles

The candidate's background can be found at: $COMP_RESUME
The job description is at: $JD_FILE

Output ONLY these labeled sections (no markdown, no extra text):
TAGLINE: <one sentence describing the company>
OVERVIEW: <3-4 sentences: what they do, scale, business model>
PRODUCTS: <key products and services, one per line with brief description>
TECH_STACK: <known technologies, tools, languages used at this company>
RECENT_NEWS: <2-3 notable recent items with brief context>
ENGINEERING_CULTURE: <what they value in engineers, how they work>
INTERVIEW_FOCUS: <what Staff SWE interviews typically cover at this company>
ALIGNMENT: <5 specific points connecting the candidate's background to this company's needs>
QUESTIONS_TO_ASK: <5 thoughtful questions for the interviewer>"

PREP_PDF="$COMPANY_DIR/${COMPANY_NAME}_interview_prep.pdf"

_spinner_start "Researching $COMPANY_NAME..."
PREP_EXIT=0
PREP_RAW="$(wibey -p "$PREP_PROMPT" --response-style verbose 2>&1)" || PREP_EXIT=$?
_spinner_stop

# Strip ANSI/terminal escape sequences emitted by wibey's TUI
PREP_OUTPUT="$(printf '%s' "$PREP_RAW" | python3 -c "
import sys, re
raw = sys.stdin.read()
clean = re.sub(r'\x1b\[[0-9;?]*[a-zA-Z]', '', raw)
clean = re.sub(r'\x1b\][^\x07\x1b]*(?:\x07|\x1b\\\\\\\\)', '', clean)
clean = re.sub(r'\x1b.', '', clean)
print(clean, end='')
")"

# Treat wibey "incomplete" responses as failures
if printf '%s' "$PREP_OUTPUT" | grep -q "Processing incomplete\|no final result received"; then
    PREP_EXIT=1
fi

if [ "$PREP_EXIT" -ne 0 ] || [ -z "$PREP_OUTPUT" ]; then
    echo "⚠️   Interview prep research failed — skipping prep PDF."
else
    PREP_TMP="/tmp/prep_content_$$.txt"
    printf '%s' "$PREP_OUTPUT" > "$PREP_TMP"
    PREP_GEN_EXIT=0
    python3 "$BIN_DIR/generate_prep_pdf.py" "$PREP_TMP" "$PREP_PDF" "$COMPANY_NAME" \
        "$MATCH_SCORE" "$MATCHED_FRAC" "$VERDICT" || PREP_GEN_EXIT=$?
    rm -f "$PREP_TMP"
    if [ "$PREP_GEN_EXIT" -ne 0 ] || [ ! -f "$PREP_PDF" ]; then
        echo "⚠️   Interview prep PDF render failed."
    fi
fi
fi  # end: resume PDF exists check

# ── Final summary ──────────────────────────────────────────────────────────────
echo ""
echo "✅  Pipeline complete. All gates passed."
echo ""
echo "   Output files:"
[ -f "$COMPANY_DIR/${COMPANY_NAME}_jd.md" ] && \
    echo "   📋  JD     → $COMPANY_DIR/${COMPANY_NAME}_jd.md"
[ -f "$PDF_DST" ] && \
    echo "   📄  PDF    → $PDF_DST"
[ -f "$BASE_RESUME_DIR/${CANDIDATE_NAME// /}_${COMPANY_NAME}.docx" ] && \
    echo "   📝  DOCX   → $BASE_RESUME_DIR/${CANDIDATE_NAME// /}_${COMPANY_NAME}.docx"
[ -f "$SCRIPT_PATH" ] && \
    echo "   🐍  Script → $SCRIPT_PATH"
[ -n "${PREP_PDF:-}" ] && [ -f "$PREP_PDF" ] && \
    echo "   📖  Prep   → $PREP_PDF"
echo ""
echo "   To re-run generation without the agent:"
echo "   cd $BASE_RESUME_DIR && python3 generate_resume_${COMPANY_LOWER}.py"
echo ""
_ELAPSED=$(( SECONDS - _SCRIPT_START ))
printf "   🕐  Started : %s\n" "$_START_TIME"
printf "   🕑  Finished: %s\n" "$(date '+%Y-%m-%d %H:%M:%S')"
printf "   ⏱️   Time Taken: %dm %02ds\n" $(( _ELAPSED / 60 )) $(( _ELAPSED % 60 ))
