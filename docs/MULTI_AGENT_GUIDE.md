# Multi-Agent Resume Generator Guide

Choose your preferred AI agent to generate tailored resume scripts. Supports **Wibey**, **OpenAI**, **Claude API**, and **Manual** modes.

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

## Installation

### All Agents

```bash
cd resumeTailor

# Already have this from initial setup
pip install pdfplumber python-docx
```

### Wibey (Built-in)

```bash
# If you have Wibey installed
which wibey

# If not, install via Claude Code or JetBrains plugin
```

### OpenAI

```bash
pip install openai
# Set your API key:
export OPENAI_API_KEY="sk-..."
```

### Claude (Anthropic)

```bash
pip install anthropic
# Set your API key:
export ANTHROPIC_API_KEY="sk-ant-..."
```

### OpenRouter

```bash
pip install requests
# Set your API key:
export OPENROUTER_API_KEY="sk-or-..."
```

---

## Usage Patterns

### Pattern 1: Wibey (Recommended for JetBrains Users)

```bash
cd resumeTailor

# 1. Prep the workspace
./bin/tailor_resume_generic.sh \
  --base-resume ~/my-resume.md \
  --candidate-name "Jane Doe" \
  https://jobs.lever.co/acme/abc123

# 2. Generate with Wibey
python3 bin/generate_with_agent.py \
  --agent wibey \
  --jd companies/Acme/Acme_jd.md \
  --resume ~/my-resume.md \
  --company Acme \
  --candidate-name "Jane Doe"

# 3. Run the generated script
cd companies/Acme/
python3 generate_resume_acme.py
```

---

### Pattern 2: OpenAI (ChatGPT)

```bash
cd resumeTailor

# 1. Prep the workspace (same as above)
./bin/tailor_resume_generic.sh \
  --base-resume ~/my-resume.md \
  --candidate-name "Jane Doe" \
  https://jobs.lever.co/acme/abc123

# 2. Generate with OpenAI
python3 bin/generate_with_agent.py \
  --agent openai \
  --api-key sk-xxxxxxxxxxxx \
  --model gpt-4 \
  --jd companies/Acme/Acme_jd.md \
  --resume ~/my-resume.md \
  --company Acme \
  --candidate-name "Jane Doe"

# 3. Run the generated script
cd companies/Acme/
python3 generate_resume_acme.py
```

**Get OpenAI API Key:**
1. Visit https://platform.openai.com/api-keys
2. Create a new API key
3. Set environment variable: `export OPENAI_API_KEY="sk-..."`
4. Or pass with `--api-key sk-...`

---

### Pattern 3: Claude API (Anthropic)

```bash
cd resumeTailor

# 1. Prep the workspace
./bin/tailor_resume_generic.sh \
  --base-resume ~/my-resume.md \
  --candidate-name "Jane Doe" \
  https://jobs.lever.co/acme/abc123

# 2. Generate with Claude
python3 bin/generate_with_agent.py \
  --agent claude \
  --api-key sk-ant-xxxxxxxxxxxx \
  --jd companies/Acme/Acme_jd.md \
  --resume ~/my-resume.md \
  --company Acme \
  --candidate-name "Jane Doe"

# 3. Run the generated script
cd companies/Acme/
python3 generate_resume_acme.py
```

**Get Claude API Key:**
1. Visit https://console.anthropic.com/
2. Create API key in account settings
3. Set environment variable: `export ANTHROPIC_API_KEY="sk-ant-..."`
4. Or pass with `--api-key sk-ant-...`

---

### Pattern 4: OpenRouter (Best Value — 100+ Models)

```bash
cd resumeTailor

# 1. Prep the workspace
./bin/tailor_resume_generic.sh \
  --base-resume ~/my-resume.md \
  --candidate-name "Jane Doe" \
  https://jobs.lever.co/acme/abc123

# 2. Generate with OpenRouter (choose your model)
python3 bin/generate_with_agent.py \
  --agent openrouter \
  --api-key sk-or-xxxxxxxxxxxx \
  --model claude-3.5-sonnet \
  --jd companies/Acme/Acme_jd.md \
  --resume ~/my-resume.md \
  --company Acme \
  --candidate-name "Jane Doe"

# 3. Run the generated script
cd companies/Acme/
python3 generate_resume_acme.py
```

**Available Models on OpenRouter:**
- Claude: `claude-3.5-sonnet`, `claude-3-opus`, `claude-3-sonnet`
- OpenAI: `gpt-4-turbo`, `gpt-4`, `gpt-3.5-turbo`
- Meta: `llama-2-70b`, `llama-3.1-405b`
- Mistral: `mistral-large`, `mistral-medium`
- And 100+ more...

**Get OpenRouter API Key:**
1. Visit https://openrouter.ai/
2. Sign up (free account)
3. Create API key in dashboard
4. Set environment variable: `export OPENROUTER_API_KEY="sk-or-..."`
5. Or pass with `--api-key sk-or-...`

**Cost:** ~$0.01-0.10 per generation (usually cheaper than direct APIs)

---

### Pattern 5: Manual Copy-Paste (No API Needed)

```bash
cd resumeTailor

# 1. Prep the workspace
./bin/tailor_resume_generic.sh \
  --base-resume ~/my-resume.md \
  --candidate-name "Jane Doe" \
  https://jobs.lever.co/acme/abc123

# 2. Generate prompt (no API call — just shows instructions)
python3 bin/generate_with_agent.py \
  --agent manual \
  --jd companies/Acme/Acme_jd.md \
  --resume ~/my-resume.md \
  --company Acme \
  --candidate-name "Jane Doe"

# 3. Follow on-screen instructions:
#    - Copy the prompt
#    - Go to Claude Code, ChatGPT, or any AI tool
#    - Paste prompt
#    - Copy the Python code from response
#    - Save to: companies/Acme/generate_resume_acme.py

# 4. Run the generated script
cd companies/Acme/
python3 generate_resume_acme.py
```

---

## Environment Variables (Optional)

Set these once, then scripts will use them automatically:

```bash
# OpenAI
export OPENAI_API_KEY="sk-..."

# Claude (Anthropic)
export ANTHROPIC_API_KEY="sk-ant-..."

# OpenRouter
export OPENROUTER_API_KEY="sk-or-..."

# Wibey (usually auto-detected)
export WIBEY_CMD="wibey"
```

Then you can simplify calls:

```bash
# OpenAI (uses $OPENAI_API_KEY)
python3 bin/generate_with_agent.py \
  --agent openai \
  --jd companies/Acme/Acme_jd.md \
  --resume ~/my-resume.md \
  --company Acme

# Claude (uses $ANTHROPIC_API_KEY)
python3 bin/generate_with_agent.py \
  --agent claude \
  --jd companies/Acme/Acme_jd.md \
  --resume ~/my-resume.md \
  --company Acme
```

---

## Full CLI Reference

```bash
python3 bin/generate_with_agent.py \
  --agent {wibey|openai|claude|openrouter|manual} \
  --jd <path-to-jd> \
  --resume <path-to-resume> \
  --company <company-name> \
  [--candidate-name <name>] \
  [--output-dir <path>] \
  [--api-key <key>] \
  [--model <model>]
```

### Required Arguments

| Argument | Description | Example |
|----------|-------------|---------|
| `--agent` | Which AI to use | `wibey`, `openai`, `claude`, `manual` |
| `--jd` | Path to job description | `companies/Acme/Acme_jd.md` |
| `--resume` | Path to your resume | `~/my-resume.md` |
| `--company` | Company name | `Acme` |

### Optional Arguments

| Argument | Description | Default |
|----------|-------------|---------|
| `--candidate-name` | Your full name | "Candidate" |
| `--output-dir` | Where to save script | JD directory |
| `--api-key` | API key (or use env var) | — |
| `--model` | OpenAI model (GPT-4, GPT-3.5, etc) | `gpt-4` |
| `--wibey-cmd` | Wibey command path | `wibey` |

---

## Workflow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. Prep Workspace                                               │
│    ./bin/tailor_resume_generic.sh --base-resume ... <job-url> │
│    ↓ Creates: companies/Company/{jd.md, prep.md, ...}         │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 2. Generate with Agent (CHOOSE ONE)                             │
├─────────────────────────────────────────────────────────────────┤
│ ┌────────────────────────────────────────────────────────────┐  │
│ │ Wibey:  python3 generate_with_agent.py --agent wibey ...  │  │
│ └────────────────────────────────────────────────────────────┘  │
│ ┌────────────────────────────────────────────────────────────┐  │
│ │ OpenAI: python3 generate_with_agent.py --agent openai ...  │  │
│ └────────────────────────────────────────────────────────────┘  │
│ ┌────────────────────────────────────────────────────────────┐  │
│ │ Claude: python3 generate_with_agent.py --agent claude ...  │  │
│ └────────────────────────────────────────────────────────────┘  │
│ ┌────────────────────────────────────────────────────────────┐  │
│ │ Manual: python3 generate_with_agent.py --agent manual ...  │  │
│ └────────────────────────────────────────────────────────────┘  │
│                              ↓ Creates: generate_resume_company.py
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 3. Run Generator                                                │
│    python3 companies/Company/generate_resume_company.py        │
│    ↓ Creates: PDF + DOCX                                       │
└─────────────────────────────────────────────────────────────────┘
```

---

## Cost Comparison

Approximate cost per resume generation:

- **Wibey**: Free (if CLI is free) or included in JetBrains
- **OpenAI (GPT-4)**: ~$0.05-0.10 per use
- **Claude**: ~$0.05-0.15 per use
- **OpenRouter**: ~$0.01-0.10 per use (cheapest option, access 100+ models)
- **Manual**: Free (but slower, requires manual copy-paste)

---

## Troubleshooting

### "Wibey not found"

```bash
# Check if Wibey is installed
which wibey

# Install via Claude Code or JetBrains plugin
# Then try again
```

### "OpenAI API key invalid"

```bash
# Check your key format
echo $OPENAI_API_KEY
# Should start with: sk-

# Verify at: https://platform.openai.com/api-keys
```

### "Claude API key invalid"

```bash
# Check your key format
echo $ANTHROPIC_API_KEY
# Should start with: sk-ant-

# Verify at: https://console.anthropic.com/
```

### "Generated script is too small"

This might mean the AI output was truncated. Try:
1. Use `--agent manual` to see full output
2. Try a different model (if OpenAI): `--model gpt-3.5-turbo`
3. Check API rate limits and quotas

### "Script won't run"

```bash
# Check for syntax errors
python3 -m py_compile companies/Company/generate_resume_company.py

# If errors, regenerate with a different agent
python3 bin/generate_with_agent.py --agent manual ...
```

---

## Best Practices

### 1. Start with Manual if Unsure

```bash
# Try manual first to see the actual prompt and response
python3 bin/generate_with_agent.py \
  --agent manual \
  --jd companies/Acme/Acme_jd.md \
  --resume ~/my-resume.md \
  --company Acme
```

### 2. Use the Same Agent Consistently

Pick one and stick with it for a single candidate's tailoring job. Switching agents mid-job can lead to style inconsistencies.

### 3. Review Generated Scripts

Always check the Python script before running:

```bash
cat companies/Company/generate_resume_company.py
# Look for:
# - Correct candidate name
# - All sections present (Summary, Skills, Experience, etc)
# - Realistic bullet count
```

### 4. Keep JD Files

Never delete `Company_jd.md` — you might need to regenerate the script if something goes wrong.

---

## Advanced: Custom Prompts

If you want to customize the prompt, modify `agents/resume-tailor-generic.md` or create your own agent file:

```bash
cp agents/resume-tailor-generic.md agents/resume-tailor-custom.md
vim agents/resume-tailor-custom.md
```

Then the wrapper will automatically use your custom agent instructions.

---

## Questions?

See the main **README.md** for general troubleshooting and workflow help.

For AI-specific issues:
- **OpenAI**: https://platform.openai.com/docs/guides/error-handling
- **Claude**: https://docs.anthropic.com/guides/api-overview
- **Wibey**: Check Claude Code documentation
