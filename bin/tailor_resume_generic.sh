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
#   # With API key (for others without Wibey)
#   ./bin/tailor_resume_generic.sh \
#     --base-resume ~/my-resume.md \
#     --api-key sk-... \
#     --model claude-opus \
#     https://jobs.lever.co/acme/abc123
#
#   # With OpenAI API
#   ./bin/tailor_resume_generic.sh \
#     --base-resume ~/my-resume.md \
#     --api-key sk-... \
#     --model gpt-4o \
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
    # Try to extract name from markdown heading (# Name), stopping at special chars
    # Handles: "# Jane Smith" or "# Jane Smith — Staff Engineer" → "Jane Smith"
    grep -E "^#\s+" "$1" 2>/dev/null | head -1 | sed 's/^#\s*//; s/\s*$//' | sed 's/\s*[—|].*//' || echo ""
}

# ── Parse command-line options ────────────────────────────────────────────────
BASE_RESUME=""
CANDIDATE_NAME=""
OUTPUT_DIR=""
COMPREHENSIVE_RESUME=""
VALIDATOR_PATH=""
API_KEY=""
MODEL="claude-opus"
FORCE=false
SKIP_INTERVIEW_PREP=false
SKIP_GENERATION=false
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
        --api-key)
            API_KEY="$2"
            shift 2
            ;;
        --model)
            MODEL="$2"
            shift 2
            ;;
        --skip-generation)
            SKIP_GENERATION=true
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
            echo "  --api-key <key>                Claude API key (default: auto-detect Wibey context)"
            echo "  --model <model>                Claude model (default: claude-opus)"
            echo "  --force                        Skip match score gate"
            echo "  --skip-interview-prep          Skip interview prep generation"
            echo "  --skip-generation              Stop after prep (don't generate resume PDF)"
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

# Use Python fetcher (handles LinkedIn, auth requirements, etc.)
FETCH_EXIT=0
python3 "$SCRIPT_DIR/bin/fetch_jd.py" "$JOB_URL" "$TMP_JD" 2>/tmp/fetch_jd_err || FETCH_EXIT=$?

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
    echo "✔   JD received ($(wc -w < "$TMP_JD") words)."
else
    echo "✔   JD fetched."
fi

# ── Step 2: Extract company name from JD or URL ───────────────────────────────
echo ""
echo "🔍  Extracting company name from job description..."

# Use Python helper for robust company extraction
DETECTED="$(python3 "$SCRIPT_DIR/bin/extract_company.py" --from-file "$TMP_JD" 2>/dev/null || true)"

# Fallback to URL pattern if JD text extraction failed
if [ -z "$DETECTED" ]; then
    DETECTED="$(python3 "$SCRIPT_DIR/bin/extract_company.py" "$JOB_URL" 2>/dev/null || true)"
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

if [ -z "$COMPANY_NAME" ]; then
    echo "❌  No company name provided. Exiting."
    exit 1
fi

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

# ── Step 5: Generate tailored resume script (if not skipped) ──────────────────
if [ "$SKIP_GENERATION" = false ]; then
    echo ""
    echo "🤖  Generating tailored resume script..."

    GENERATOR_SCRIPT="$COMPANY_DIR/generate_resume_${COMPANY_LOWER}.py"

    if [ -z "$API_KEY" ]; then
        # ── Use Wibey CLI (requires `wibey` command available) ──────────────────
        echo "   Using Wibey agent..."

        # Authenticate with Wibey (suppress all output)
        echo "   🔐 Authenticating..." >&2
        wibey --auth >/dev/null 2>&1 || true
        echo "   ✓ Auth done" >&2

        WIBEY_PROMPT="Tailor my resume for $COMPANY_NAME.

The job description is at: $JD_FILE
The comprehensive resume is at: $COMPREHENSIVE_RESUME

DO NOT fetch URLs. Read from the local files above.

Write a complete Python generator script (use python-docx + reportlab).
Save to: $GENERATOR_SCRIPT

Include the validator call in __main__:
  from resume_validator import validate_resume_bullets
  validate_resume_bullets(script_path)

Output filenames:
  PDF:  ${CANDIDATE_NORMALIZED}_${COMPANY_NAME}.pdf
  DOCX: ${CANDIDATE_NORMALIZED}_Resume_${COMPANY_NAME}.docx

Rules:
  - 2 pages maximum (hard constraint)
  - 18-22 bullets total
  - Core Accomplishments first
  - No metrics (25+, 4,300+, counts)
  - All bullets from comprehensive resume

Write only the script. Do not run it."

        echo "   🤖 Calling Wibey agent (this may take 60-90 seconds)..." >&2
        GEN_EXIT=0
        wibey -p "$WIBEY_PROMPT" --response-style verbose 2>&1 || GEN_EXIT=$?
        echo "   ✓ Agent complete (exit code: $GEN_EXIT)" >&2

        if [ $GEN_EXIT -ne 0 ]; then
            echo "⚠️   Wibey agent failed (exit code: $GEN_EXIT)"
            echo "    You can generate manually via: wibey 'Tailor my resume for $COMPANY_NAME'"
            SKIP_GENERATION=true
        fi
    else
        # ── Use API directly (Claude/OpenAI) ──────────────────────────────────
        echo "   Using API directly ($MODEL)..."

        GEN_EXIT=0
        python3 "$SCRIPT_DIR/bin/generate_resume_script.py" \
            --comprehensive "$COMPREHENSIVE_RESUME" \
            --jd "$JD_FILE" \
            --candidate "$CANDIDATE_NAME" \
            --company "$COMPANY_NAME" \
            --output "$GENERATOR_SCRIPT" \
            --api-key "$API_KEY" \
            --model "$MODEL" \
            2>&1 | grep -v "^ℹ️" || GEN_EXIT=$?
    fi

    # ── Run the generator if script was created ──────────────────────────────
    if [ -f "$GENERATOR_SCRIPT" ]; then
        echo "✔   Generator script created: $GENERATOR_SCRIPT"

        # ── Step 6: Run the generator to create PDF/DOCX ──────────────────────
        echo ""
        echo "📄  Generating PDF and DOCX..."

        RUN_EXIT=0
        cd "$COMPANY_DIR"
        python3 "$(basename "$GENERATOR_SCRIPT")" 2>&1 || RUN_EXIT=$?
        cd "$SCRIPT_DIR"

        if [ $RUN_EXIT -eq 0 ]; then
            echo "✔   Resume generation complete."
        else
            echo "⚠️   Resume generation failed. Check the output above."
        fi
    elif [ "$SKIP_GENERATION" = false ]; then
        echo "⚠️   Failed to generate resume script."
        echo "    Generate manually: wibey 'Tailor my resume for $COMPANY_NAME'"
    fi
fi

# ── Final summary ──────────────────────────────────────────────────────────────
echo ""
echo "✅  Pipeline complete. All gates passed."
echo ""
echo "   Output files created:"
[ -f "$JD_FILE" ] && echo "   📋  JD         → $JD_FILE"
[ -f "$INFO_FILE" ] && echo "   📝  Info       → $INFO_FILE"
[ -f "$PREP_FILE" ] 2>/dev/null && echo "   📖  Prep       → $PREP_FILE"

# Check for generated resume files
if [ "$SKIP_GENERATION" = false ]; then
    PDF_FILE=$(find "$COMPANY_DIR" -name "*${CANDIDATE_NORMALIZED}*${COMPANY_NAME}*.pdf" 2>/dev/null | head -1)
    DOCX_FILE=$(find "$COMPANY_DIR" -name "*${CANDIDATE_NORMALIZED}*${COMPANY_NAME}*.docx" 2>/dev/null | head -1)
    [ -n "$PDF_FILE" ] && echo "   📄  PDF        → $PDF_FILE"
    [ -n "$DOCX_FILE" ] && echo "   📄  DOCX       → $DOCX_FILE"
fi
echo ""

_ELAPSED=$(( SECONDS - _SCRIPT_START ))
printf "   🕐  Started : %s\n" "$_START_TIME"
printf "   🕑  Finished: %s\n" "$(date '+%Y-%m-%d %H:%M:%S')"
printf "   ⏱️   Time Taken: %dm %02ds\n" $(( _ELAPSED / 60 )) $(( _ELAPSED % 60 ))
