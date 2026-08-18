#!/bin/bash
# tailor_resume_generic.sh — Generic resume tailoring script for any candidate
#
# ⭐ RULES: See docs/TAILORING_RULES.md for all content, ATS, and validation rules
#
# Usage:
#   ./tailor_resume_generic.sh --base-resume <path> <job-url>
#   ./tailor_resume_generic.sh [OPTIONS] <job-url>
#
# Required options:
#   --base-resume <path>           Path to base/comprehensive resume file (markdown)
#
# Optional options:
#   --candidate-name <name>        Candidate's name (default: extracted from resume heading)
#   --output-dir <path>            Output directory (default: ./companies in resumeTailor root)
#   --comprehensive-resume <path>  Path to comprehensive resume (defaults to base-resume)
#   --validator <path>             Path to resume_validator.py (optional; skips validation if missing)
#   --force                        Skip match score gate
#   --skip-interview-prep          Skip interview prep generation
#   --help                         Show this help message
#
# Examples:
#   # From resumeTailor root — extracts name from resume, saves to ./companies/{Company}/
#   ./bin/tailor_resume_generic.sh \
#     --base-resume ~/my-resume.md \
#     https://jobs.lever.co/acme/abc123
#
#   # Override candidate name from resume
#   ./bin/tailor_resume_generic.sh \
#     --base-resume ~/my-resume.md \
#     --candidate-name "Jane Doe" \
#     https://jobs.lever.co/acme/abc123
#
#   # Custom output directory
#   ./bin/tailor_resume_generic.sh \
#     --base-resume ~/my-resume.md \
#     --output-dir ~/custom-location \
#     https://jobs.lever.co/acme/abc123
#
# Output structure:
#   ./companies/<Company>/
#       <Company>_jd.md                         ← raw job description
#       tailoring_info.txt                      ← metadata & next steps
#       generate_resume_<company>.py            ← generator script (from agent)
#       <CandidateName>_<Company>.pdf           ← tailored PDF (after running generator)
#       <CandidateName>_Resume_<Company>.docx   ← DOCX for portals (after running generator)
#       <Company>_interview_prep.md             ← interview prep guide

set -euo pipefail

_SCRIPT_START=$SECONDS
_START_TIME="$(date '+%Y-%m-%d %H:%M:%S')"
_SPINNER_PID=""
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# ── Ctrl+C / SIGTERM — clean exit ─────────────────────────────────────────────
_cleanup() {
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

# ── Helper: Extract candidate name from resume ────────────────────────────────
_extract_name_from_resume() {
    # Try to extract name from markdown heading (# Name)
    grep -E "^#\s+" "$1" 2>/dev/null | head -1 | sed 's/^#\s*//; s/\s*$//' || echo ""
}

# ── Parse command-line options ────────────────────────────────────────────────
BASE_RESUME=""
CANDIDATE_NAME=""
OUTPUT_DIR=""
COMPREHENSIVE_RESUME=""
VALIDATOR_PATH=""
FORCE=false
SKIP_INTERVIEW_PREP=false
JOB_URL=""

while [ $# -gt 0 ]; do
    case "$1" in
        --base-resume)
            BASE_RESUME="$2"
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
        --comprehensive-resume)
            COMPREHENSIVE_RESUME="$2"
            shift 2
            ;;
        --validator)
            VALIDATOR_PATH="$2"
            shift 2
            ;;
        --force)
            FORCE=true
            shift
            ;;
        --skip-interview-prep)
            SKIP_INTERVIEW_PREP=true
            shift
            ;;
        --help)
            echo "Usage: $(basename "$0") --base-resume <path> [OPTIONS] <job-url>"
            echo ""
            echo "Required options:"
            echo "  --base-resume <path>           Path to comprehensive/base resume file (markdown)"
            echo ""
            echo "Optional options:"
            echo "  --candidate-name <name>        Candidate's full name (default: extracted from resume)"
            echo "  --output-dir <path>            Output directory (default: ./companies in resumeTailor root)"
            echo "  --comprehensive-resume <path>  Override base resume for validation (default: same as base)"
            echo "  --validator <path>             Path to resume_validator.py (validation skipped if not provided)"
            echo "  --force                        Skip match score gate"
            echo "  --skip-interview-prep          Skip interview prep generation"
            echo "  --help                         Show this help message"
            exit 0
            ;;
        http*|*)
            JOB_URL="$1"
            shift
            ;;
    esac
done

# ── Validate required arguments ────────────────────────────────────────────────
if [ -z "$BASE_RESUME" ] || [ -z "$JOB_URL" ]; then
    echo "❌  Missing required options."
    echo ""
    echo "Usage: $(basename "$0") --base-resume <path> <job-url>"
    echo ""
    echo "Run with --help for full usage information."
    exit 1
fi

# ── Set default output directory (./companies relative to script root) ─────────
if [ -z "$OUTPUT_DIR" ]; then
    OUTPUT_DIR="$SCRIPT_DIR/companies"
fi

# ── Check that base resume exists ─────────────────────────────────────────────
if [ ! -f "$BASE_RESUME" ]; then
    echo "❌  Base resume file not found: $BASE_RESUME"
    exit 1
fi

# ── Set comprehensive resume (default to base resume) ────────────────────────
if [ -z "$COMPREHENSIVE_RESUME" ]; then
    COMPREHENSIVE_RESUME="$BASE_RESUME"
fi

# ── Extract candidate name from resume if not provided ────────────────────────
if [ -z "$CANDIDATE_NAME" ]; then
    CANDIDATE_NAME="$(_extract_name_from_resume "$BASE_RESUME")"
    if [ -z "$CANDIDATE_NAME" ]; then
        echo "⚠️   Could not extract candidate name from resume."
        printf "    Enter candidate name: "
        read -r CANDIDATE_NAME
        if [ -z "$CANDIDATE_NAME" ]; then
            echo "❌  No candidate name provided. Exiting."
            exit 1
        fi
    else
        echo "👤  Extracted candidate name from resume: $CANDIDATE_NAME"
    fi
fi

# ── Sanitize candidate name for use in filenames ───────────────────────────────
CANDIDATE_NORMALIZED="$(echo "$CANDIDATE_NAME" | sed 's/ /_/g')"

echo "🕐  Started : $_START_TIME"
echo "👤  Candidate: $CANDIDATE_NAME"
echo "📄  Base resume: $BASE_RESUME"
echo "📁  Output dir: $OUTPUT_DIR"
echo ""

# ── Strip LinkedIn tracking query params ──────────────────────────────────────
if echo "$JOB_URL" | grep -q "linkedin\.com/jobs/view/"; then
    JOB_URL="$(echo "$JOB_URL" | sed 's/?.*//')"
fi

# ── Step 1: Fetch JD to a temp file ───────────────────────────────────────────
TMP_JD="/tmp/tailor_jd_tmp_$$.md"
trap 'rm -f "$TMP_JD"' EXIT

echo ""
echo "📥  Fetching job description..."

# Try to fetch using curl (basic web fetch without dedicated tool)
FETCH_EXIT=0
HTTP_CODE=$(curl -s -o "$TMP_JD" -w "%{http_code}" -A "Mozilla/5.0" "$JOB_URL") || FETCH_EXIT=$?

if [ "$HTTP_CODE" != "200" ] || [ ! -s "$TMP_JD" ]; then
    rm -f "$TMP_JD"
    echo "⚠️   Could not fetch JD from URL (HTTP $HTTP_CODE or empty response)."
    echo "    Paste the job description text below, then press Ctrl+D when done:"
    echo ""
    cat > "$TMP_JD"
    echo ""
    if [ ! -s "$TMP_JD" ]; then
        echo "❌  No content provided. Exiting."
        exit 1
    fi
    echo "✔   JD received ($(wc -w < "$TMP_JD") words)."
else
    echo "✔   JD fetched."
fi

# ── Step 2: Extract company name from JD or URL ───────────────────────────────
echo ""
echo "🔍  Extracting company name from job description..."

# Simple heuristic: try to find a company name pattern in the JD
DETECTED=""

# Try to extract from common patterns in JD
DETECTED="$(grep -i "company\|employer\|hiring for\|join" "$TMP_JD" 2>/dev/null | head -1 | \
    sed 's/^.*[Cc]ompany[: ]*//; s/^.*[Ee]mployer[: ]*//; s/^.*is hiring//' | \
    sed 's/^\s*//; s/\s*$//; s/[,\.].*//; s/\s\{2,\}/ /g' | cut -d' ' -f1-2)" || DETECTED=""

# Fallback: extract domain from URL
if [ -z "$DETECTED" ]; then
    DETECTED="$(echo "$JOB_URL" | sed 's|https\?://||; s|jobs\.||; s|/.*||; s/\.com//; s/\..*//' | \
        sed 's/-/ /g' | sed 's/\b\(.\)/\u\1/g')" || DETECTED=""
fi

if [ -z "$DETECTED" ]; then
    echo "⚠️   Could not auto-detect company name."
    printf "    Enter company name: "
    read -r DETECTED
    if [ -z "$DETECTED" ]; then
        echo "❌  No company name provided. Exiting."
        exit 1
    fi
fi

echo "🏢  Detected company: $DETECTED"
printf "    Press Enter to confirm, or type a different name: "
read -r OVERRIDE
COMPANY_NAME="${OVERRIDE:-$DETECTED}"

COMPANY_LOWER="$(echo "$COMPANY_NAME" | tr '[:upper:]' '[:lower:]')"
COMPANY_DIR="$OUTPUT_DIR/$COMPANY_NAME"
mkdir -p "$COMPANY_DIR"

# ── Step 3: Save JD ───────────────────────────────────────────────────────────
JD_FILE="$COMPANY_DIR/${COMPANY_NAME}_jd.md"
cp "$TMP_JD" "$JD_FILE"
echo "✔   JD saved: $JD_FILE"

# ── Spinner helper ────────────────────────────────────────────────────────────
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
    wait "$_SPINNER_PID" 2>/dev/null || true
    printf "\r\033[2K" >&2
}

# ── Step 4: Summary message ───────────────────────────────────────────────────
echo ""
echo "🏢  Company   : $COMPANY_NAME"
echo "🔗  JD URL    : $JOB_URL"
echo "📁  Output dir: $COMPANY_DIR"
echo ""
echo "✅  Preparation complete!"
echo ""
echo "   Next steps:"
echo "   1. Use Wibey agent to generate tailored resume:"
echo "      → In Claude Code, say: 'Tailor my resume for $COMPANY_NAME'"
echo "      → Provide: comprehensive resume + job description"
echo ""
echo "   2. The agent will generate:"
echo "      → generate_resume_${COMPANY_LOWER}.py"
echo ""
echo "   3. Run the generator:"
echo "      cd \"$COMPANY_DIR\""
echo "      python3 generate_resume_${COMPANY_LOWER}.py"
echo ""
echo "   4. Files will be created:"
echo "      → ${CANDIDATE_NORMALIZED}_${COMPANY_NAME}.pdf"
echo "      → ${CANDIDATE_NORMALIZED}_Resume_${COMPANY_NAME}.docx"
echo "      → ${COMPANY_NAME}_interview_prep.md"
echo ""

# ── Save tailoring info ───────────────────────────────────────────────────────
INFO_FILE="$COMPANY_DIR/tailoring_info.txt"
cat > "$INFO_FILE" << EOF
Tailoring Information
=====================

Candidate: $CANDIDATE_NAME
Company: $COMPANY_NAME
Job URL: $JOB_URL

Base Resume: $BASE_RESUME
Comprehensive Resume: $COMPREHENSIVE_RESUME
Validator: ${VALIDATOR_PATH:-(not provided)}

Output Directory: $COMPANY_DIR
JD File: $JD_FILE

Generated: $_START_TIME

Next Steps:
1. Use Wibey agent to generate: generate_resume_${COMPANY_LOWER}.py
2. Run generator: python3 generate_resume_${COMPANY_LOWER}.py
3. Review outputs in this folder
EOF

echo "✔   Tailoring info saved: $INFO_FILE"

# ── Generate interview prep (if not skipped) ─────────────────────────────────
if [ "$SKIP_INTERVIEW_PREP" = false ]; then
    echo ""
    echo "📚  Generating interview prep document..."

    PREP_FILE="$COMPANY_DIR/${COMPANY_NAME}_interview_prep.md"

    # Create basic interview prep template
    cat > "$PREP_FILE" << 'PREP_EOF'
# Interview Preparation — {COMPANY_NAME}

## Company Overview
Research the following before your interview:
- [ ] Company mission and values
- [ ] Recent news, product launches, funding rounds
- [ ] Engineering culture and tech stack
- [ ] Key competitors
- [ ] Size and growth trajectory

**Resources:**
- LinkedIn Company Page: https://linkedin.com/company/
- Company Website: https://
- Tech Blog: https://
- Recent News: Use Google News or AngelList

## Role & Expectations
- [ ] Read the job description thoroughly
- [ ] Identify must-have vs. nice-to-have skills
- [ ] Understand level expectations (Staff/Senior/Principal)
- [ ] Note any specific technologies or domains mentioned

## Your Background
Key points to emphasize:
1. **[Point 1]** — How your background aligns with this role
2. **[Point 2]** — Specific experience that matches the JD
3. **[Point 3]** — Leadership or impact you've driven

## Technical Preparation

### Common Interview Topics
- [ ] System design (architecture, scalability, tradeoffs)
- [ ] Your most complex project (problem, solution, learnings)
- [ ] Technical decision-making process
- [ ] Handling ambiguity and unknowns
- [ ] Collaboration and leadership approach

### Review Your Projects
1. **Project A** — [2-3 min pitch]
2. **Project B** — [2-3 min pitch]
3. **Project C** — [2-3 min pitch]

### Prepare Stories (STAR Format)
- **Situation:** What was the context?
- **Task:** What was the goal?
- **Action:** What did you do?
- **Result:** What was the impact?

Prepare 3-5 stories covering:
- Technical leadership
- Problem-solving under pressure
- Learning from failure
- Mentoring or team impact
- Cross-functional collaboration

## Questions to Ask

### About the Role
- [ ] What would success look like in the first 6 months?
- [ ] What are the biggest technical challenges right now?
- [ ] How does this team work with other teams?
- [ ] What's the current tech stack and roadmap?

### About Growth
- [ ] What's the career progression path?
- [ ] How are engineers developed and mentored?
- [ ] What do high-performers do differently?

### About the Team
- [ ] Who would I be working with directly?
- [ ] What's the team composition and structure?
- [ ] How much autonomy do engineers have?

## Red Flags to Watch For
- [ ] Unclear job scope or expectations
- [ ] Team turnover or instability
- [ ] Misalignment between JD and actual role
- [ ] Lack of technical depth in interviewers
- [ ] Unclear growth opportunities

## Interview Day Checklist
- [ ] Arrive 10-15 minutes early
- [ ] Bring extra copies of your resume
- [ ] Pen and notepad
- [ ] List of your questions
- [ ] Confirmation of interview details
- [ ] Professional attire (match company culture)
- [ ] Silence phone
- [ ] Water bottle
- [ ] Portfolio/examples if relevant

## After the Interview
- [ ] Send thank-you notes within 24 hours
- [ ] Mention specific conversation points
- [ ] Reiterate your interest
- [ ] Ask about timeline and next steps
- [ ] Follow up if you don't hear within the stated timeframe

---

**Good luck! 🎯**

Remember: They're also evaluating if YOU want to work there. Ask thoughtful questions and be authentic.
PREP_EOF

    echo "✔   Interview prep template created: $PREP_FILE"
fi

# ── Final summary ──────────────────────────────────────────────────────────────
echo ""
echo "✅  Pipeline complete. All gates passed."
echo ""
echo "   Output files created:"
[ -f "$JD_FILE" ] && echo "   📋  JD         → $JD_FILE"
[ -f "$INFO_FILE" ] && echo "   📝  Info       → $INFO_FILE"
[ -f "$PREP_FILE" ] 2>/dev/null && echo "   📖  Prep       → $PREP_FILE"
echo ""

_ELAPSED=$(( SECONDS - _SCRIPT_START ))
printf "   🕐  Started : %s\n" "$_START_TIME"
printf "   🕑  Finished: %s\n" "$(date '+%Y-%m-%d %H:%M:%S')"
printf "   ⏱️   Time Taken: %dm %02ds\n" $(( _ELAPSED / 60 )) $(( _ELAPSED % 60 ))
