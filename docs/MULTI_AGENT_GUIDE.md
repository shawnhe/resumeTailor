# Multi-Agent Resume Generator Guide

Choose your preferred AI agent to generate tailored resume scripts. Supports **Wibey**, **OpenAI**, **Claude API**, **OpenRouter**, and **Manual** modes.

---

## Quick Comparison

| Agent | Setup | Speed | Cost | Best For |
|-------|-------|-------|------|----------|
| **Wibey** | ✅ Built-in | ⚡ Fast | Free (CLI) | JetBrains / Claude Code users |
| **OpenAI** | API key | ⚡ Fast | ~$0.05-0.10/use | ChatGPT users, flexible |
| **Claude API** | API key | ⚡ Fast | ~$0.05-0.15/use | Anthropic Claude users |
| **OpenRouter** | API key | ⚡ Fast | ~$0.01-0.10/use | Access 100+ models, cheapest option |
| **Manual** | ✅ No setup | 🐢 Slow | Free | No API access needed |

---

## Prerequisites

### Virtual Environment Setup (Required)

```bash
cd resumeTailor
python3 -m venv .venv
source .venv/bin/activate

# Core dependencies (required for ALL agents)
pip install pdfplumber python-docx pypdf fpdf2
```

> **Note:** `tailor_resume_generic.sh` auto-detects `.venv/` in the repo root. You don't need to activate the venv before running the script.

### Agent-Specific Dependencies

```bash
# OpenAI
pip install openai

# Claude (Anthropic)
pip install anthropic

# OpenRouter
pip install requests
```

---

## Usage: End-to-End Pipeline (Recommended)

The main script `tailor_resume_generic.sh` handles everything end-to-end: fetch JD → score match → generate script → validate → build PDF/DOCX → interview prep.

### Wibey (Default)

```bash
./bin/tailor_resume_generic.sh \
  --base-resume ~/my-resume.md \
  https://linkedin.com/jobs/view/1234567
```

### OpenAI

```bash
./bin/tailor_resume_generic.sh \
  --base-resume ~/my-resume.md \
  --agent openai \
  --api-key sk-xxxxxxxxxxxx \
  --model gpt-4o \
  https://linkedin.com/jobs/view/1234567
```

> ⚠️ Use `gpt-4o` (not `gpt-4`). The original `gpt-4` has a 10K TPM rate limit that's too low for the prompt size.

### Claude API

```bash
./bin/tailor_resume_generic.sh \
  --base-resume ~/my-resume.md \
  --agent claude \
  --api-key sk-ant-xxxxxxxxxxxx \
  --model claude-sonnet-4-20250514 \
  https://linkedin.com/jobs/view/1234567
```

### OpenRouter

```bash
./bin/tailor_resume_generic.sh \
  --base-resume ~/my-resume.md \
  --agent openrouter \
  --api-key sk-or-xxxxxxxxxxxx \
  --model anthropic/claude-sonnet-4 \
  https://linkedin.com/jobs/view/1234567
```

---

## Usage: Standalone Script Generation

You can also call `generate_with_agent.py` directly if you've already fetched the JD and want to skip scoring/validation:

### OpenAI

```bash
python3 bin/generate_with_agent.py \
  --agent openai \
  --api-key sk-xxxxxxxxxxxx \
  --model gpt-4o \
  --jd companies/Acme/Acme_jd.md \
  --resume ~/my-resume.md \
  --company Acme \
  --candidate-name "Jane Doe" \
  --output-dir companies/Acme/
```

### Claude

```bash
python3 bin/generate_with_agent.py \
  --agent claude \
  --api-key sk-ant-xxxxxxxxxxxx \
  --jd companies/Acme/Acme_jd.md \
  --resume ~/my-resume.md \
  --company Acme \
  --candidate-name "Jane Doe" \
  --output-dir companies/Acme/
```

### OpenRouter

```bash
python3 bin/generate_with_agent.py \
  --agent openrouter \
  --api-key sk-or-xxxxxxxxxxxx \
  --model anthropic/claude-sonnet-4 \
  --jd companies/Acme/Acme_jd.md \
  --resume ~/my-resume.md \
  --company Acme \
  --candidate-name "Jane Doe" \
  --output-dir companies/Acme/
```

### Wibey

```bash
python3 bin/generate_with_agent.py \
  --agent wibey \
  --jd companies/Acme/Acme_jd.md \
  --resume ~/my-resume.md \
  --company Acme \
  --candidate-name "Jane Doe"
```

### Manual Copy-Paste

```bash
python3 bin/generate_with_agent.py \
  --agent manual \
  --jd companies/Acme/Acme_jd.md \
  --resume ~/my-resume.md \
  --company Acme \
  --candidate-name "Jane Doe"

# Follow on-screen instructions:
#   1. Copy the prompt
#   2. Paste into Claude/ChatGPT/any AI tool
#   3. Copy the Python code from the response
#   4. Save to the output path shown
```

---

## Recommended Models

| Agent | Model | Notes |
|-------|-------|-------|
| openai | `gpt-4o` | Fast, high rate limits, cost-effective. **Avoid `gpt-4`** (10K TPM limit too low). |
| claude | `claude-sonnet-4-20250514` | Strong code generation |
| openrouter | `anthropic/claude-sonnet-4` | Access Claude without Anthropic API key |

---

## Full CLI Reference

### tailor_resume_generic.sh (End-to-End)

```
Usage: tailor_resume_generic.sh <job-url> [CompanyName] [options]

Required:
  <job-url>                Job posting URL
  --base-resume <path>     Path to comprehensive resume markdown

Optional:
  [CompanyName]            Company name (auto-detected if omitted)
  --candidate-name <name>  Candidate name (extracted from resume H1 if omitted)
  --output-dir <dir>       Output directory (default: ./companies)
  --force                  Skip JD match score gate and generate anyway
  --agent <type>           wibey (default), openai, claude, openrouter
  --api-key <key>          API key (required for openai, claude, openrouter)
  --model <model>          Model name (required for openai, claude, openrouter)
```

### generate_with_agent.py (Standalone)

```
Usage: python3 bin/generate_with_agent.py [options]

Required:
  --agent <type>           wibey, openai, claude, openrouter, manual
  --jd <path>              Path to job description
  --resume <path>          Path to comprehensive resume
  --company <name>         Company name

Optional:
  --candidate-name <name>  Candidate name (default: "Candidate")
  --output-dir <path>      Where to save generated script (default: JD parent dir)
  --api-key <key>          API key for openai, claude, openrouter
  --model <model>          Model name (default: gpt-4o for openai)
```

---

## Environment Variables (Optional)

Set these once so you don't need `--api-key` every time:

```bash
# OpenAI
export OPENAI_API_KEY="sk-..."

# Claude (Anthropic)
export ANTHROPIC_API_KEY="sk-ant-..."

# OpenRouter
export OPENROUTER_API_KEY="sk-or-..."
```

---

## Workflow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│ tailor_resume_generic.sh (end-to-end pipeline)                  │
├─────────────────────────────────────────────────────────────────┤
│ 1. Fetch JD (fetch_jd.py) → companies/<Company>/<Company>_jd.md│
│ 2. Detect company name (extract_company.py)                     │
│ 3. Score JD match (AI-powered, with match table)                │
│    ├── ≥80: auto-proceed                                        │
│    ├── 60-79: confirm with user                                 │
│    └── <60: skip (or --force to override)                       │
│ 4. Generate script (generate_with_agent.py)                     │
│ 5. Validate (resume_validator.py) → auto-fix if needed          │
│ 6. Build PDF + DOCX                                             │
│ 7. Page check → auto-trim if >2 pages                          │
│ 8. Interview prep PDF (generate_prep_pdf.py)                    │
└─────────────────────────────────────────────────────────────────┘
```

---

## Cost Comparison

Approximate cost per resume generation:

| Agent | Cost | Setup Time |
|-------|------|-----------|
| Wibey | Free | < 5 min |
| OpenRouter (Claude) | $0.03-0.08 | 5-10 min |
| OpenAI (GPT-4o) | $0.05-0.10 | 10-15 min |
| Claude (Sonnet) | $0.05-0.10 | 10-15 min |
| Manual | Free | 5-10 min (slower) |

---

## Troubleshooting

### "No module named 'fpdf'" or "No module named 'docx'"

All core packages must be installed in the venv:
```bash
cd resumeTailor
source .venv/bin/activate
pip install pdfplumber python-docx pypdf fpdf2
```

> The pipeline script auto-detects `.venv/` — you don't need to activate it before running `tailor_resume_generic.sh`.

### "Request too large" (OpenAI 429 error)

Use `gpt-4o` instead of `gpt-4`:
```bash
--model gpt-4o   # Higher rate limits (30K-800K TPM vs 10K)
```

### "validate_resume_bullets" TypeError

If the generated script calls `validate_resume_bullets(some_list)` instead of `validate_resume_bullets(script_path)`, regenerate the script. The validator takes a **file path string**, not a list of bullets.

### "wibey: command not found"

Wibey not installed. Use `--agent openai` or `--agent claude` instead.

### API Key not working

1. Check key is copied correctly (no extra spaces)
2. Verify it hasn't expired (check service dashboard)
3. Regenerate if needed
4. Check billing is set up (add payment method)

### Match score can't be generated

Check `/tmp/last_score_output.txt` for the raw API response. Common causes:
- Invalid API key
- Wrong model name
- Network issues

---

## Questions?

See the main **README.md** for general workflow help, or **AGENT_SETUP.md** for detailed API key setup instructions.
