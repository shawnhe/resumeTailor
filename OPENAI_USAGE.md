# OpenAI Resume Tailoring — Quick Start

**One command.** That's it. No multiple steps, no complex setup.

The main script now supports OpenAI via the `--agent openai` parameter.

## Basic Command

```bash
cd /path/to/resumeTailor

./bin/tailor_resume_generic.sh \
  https://www.linkedin.com/jobs/view/4402191665/ \
  --base-resume ~/resume-comprehensive.md \
  --agent openai \
  --api-key sk-YOUR_OPENAI_KEY \
  --model gpt-4
```

**That's all.** The script handles everything:
- ✅ Fetches job description from URL
- ✅ Detects company name automatically
- ✅ Extracts your name from resume
- ✅ Generates tailored resume script
- ✅ Validates with built-in validator
- ✅ Creates PDF and DOCX files
- ✅ Saves to `companies/<CompanyName>/`

## What You Need

### 1. OpenAI API Key
```bash
# Get from: https://platform.openai.com/account/api-keys
# Format: sk-...

--api-key sk-YOUR_KEY
```

### 2. Model Choice
```
--model gpt-4              # Best quality, slower, more expensive
--model gpt-4-turbo        # Fast, good quality, cheaper
--model gpt-3.5-turbo      # Fastest, cheapest, acceptable quality
```

**Recommended**: `gpt-4` for best results

### 3. Resume File
Your comprehensive resume in Markdown format:
```bash
--base-resume ~/my-resume.md
```

### 4. Job URL
Any of these sources:
- LinkedIn: `https://www.linkedin.com/jobs/view/ABC/`
- Lever: `https://jobs.lever.co/company/xyz`
- Greenhouse: `https://boards.greenhouse.io/...`

Or paste manually when prompted.

## Complete Examples

### Example 1: Simple LinkedIn URL
```bash
./bin/tailor_resume_generic.sh \
  https://www.linkedin.com/jobs/view/4402191665/ \
  --base-resume ~/my-resume.md \
  --agent openai \
  --api-key sk-xxxxx \
  --model gpt-4-turbo
```

### Example 2: With custom candidate name
```bash
./bin/tailor_resume_generic.sh \
  https://jobs.lever.co/acme/abc123 \
  --base-resume ~/my-resume.md \
  --candidate-name "Jane Doe" \
  --agent openai \
  --api-key sk-xxxxx \
  --model gpt-4
```

### Example 3: With custom output directory
```bash
./bin/tailor_resume_generic.sh \
  https://greenhouse.io/jobs/123 \
  --base-resume ~/my-resume.md \
  --output-dir ~/Applications \
  --agent openai \
  --api-key sk-xxxxx \
  --model gpt-4
```

### Example 4: Default (Wibey)
```bash
# No --agent flag = uses wibey (default)
./bin/tailor_resume_generic.sh \
  https://www.linkedin.com/jobs/view/ABC/ \
  --base-resume ~/resume.md
```

## Cost Estimate

**Per Resume:**
- gpt-4: ~$0.10–0.30 (slowest, best quality)
- gpt-4-turbo: ~$0.03–0.10 (fast, good quality)
- gpt-3.5-turbo: ~$0.01–0.03 (fastest, cheapest)

**Bulk:** Tailor 10 resumes for ~$0.30–$3.00 total

## Supported Agents

All built into one script with `--agent` flag:

```bash
# Wibey (default, no flag needed)
./bin/tailor_resume_generic.sh <url> --base-resume ~/resume.md

# OpenAI
./bin/tailor_resume_generic.sh <url> --base-resume ~/resume.md \
  --agent openai --api-key sk-... --model gpt-4

# Claude (Anthropic)
./bin/tailor_resume_generic.sh <url> --base-resume ~/resume.md \
  --agent claude --api-key sk-ant-... --model claude-3-sonnet

# OpenRouter (multi-model)
./bin/tailor_resume_generic.sh <url> --base-resume ~/resume.md \
  --agent openrouter --api-key sk-or-... --model claude-3.5-sonnet
```

## Troubleshooting

### API Key Invalid
```
❌ --api-key required for agent: openai
```
**Fix**: Verify key starts with `sk-` and is valid at https://platform.openai.com/account/api-keys

### Model Not Found
```
❌ --model required for agent: openai
```
**Fix**: Use valid model: `gpt-4`, `gpt-4-turbo`, or `gpt-3.5-turbo`

## Next Steps

1. Get OpenAI API key: https://platform.openai.com/account/api-keys
2. Run the command (copy-paste from examples above)
3. Check output in `companies/<CompanyName>/`

Done!
