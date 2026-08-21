# Detailed Agent Setup Guide

Complete, step-by-step instructions for setting up each AI agent.

---

## Table of Contents

1. [Wibey (JetBrains/Claude Code)](#wibey)
2. [OpenAI (ChatGPT)](#openai)
3. [Claude API (Anthropic)](#claude)
4. [OpenRouter](#openrouter)
5. [Manual (No Setup)](#manual)
6. [Quick Reference](#quick-reference)

---

## Wibey

### What It Is
Wibey is Walmart's intelligent coding assistant integrated into JetBrains IDEs and Claude Code. Free to use if you already have JetBrains or Claude Code installed.

### Setup Steps

#### Option A: Using Claude Code (Web or IDE)

1. **Ensure Claude Code is running**
   - If using web: https://claude.com/claude-code
   - If using IDE plugin: Verify plugin is installed

2. **No additional setup needed**
   - Wibey is built into Claude Code
   - Just use it when asked to invoke an agent

#### Option B: Using Wibey CLI (Local)

```bash
# 1. Install Wibey (if not already installed)
# This may require Walmart internal tools
which wibey

# 2. Verify installation
wibey --version

# 3. Set up authentication (if prompted)
wibey login
# Follow the prompts to authenticate

# 4. Test it works
wibey -p "Say hello"
```

### Usage with resumeTailor

```bash
python3 bin/generate_with_agent.py \
  --agent wibey \
  --jd companies/Acme/Acme_jd.md \
  --resume ~/my-resume.md \
  --company Acme
```

### Troubleshooting

| Issue | Solution |
|-------|----------|
| "wibey: command not found" | Wibey not installed. Check Claude Code setup. |
| Auth errors | Run `wibey login` to re-authenticate |
| Timeout errors | Increase timeout or try another agent |

---

## OpenAI

### What It Is
ChatGPT's API. Access to GPT-4, GPT-3.5-turbo, and other models. Requires paid account.

### Setup Steps

#### Step 1: Create OpenAI Account

1. **Go to OpenAI Platform**
   - Visit: https://platform.openai.com/

2. **Sign Up**
   - Click "Sign up" in top right
   - Use email, Google, or Microsoft account
   - Complete verification (email + phone)

3. **Add Payment Method**
   - Click your account → "Billing" → "Overview"
   - Add credit card for API charges
   - Set up usage limits (recommended: $10/month for safety)

#### Step 2: Create API Key

1. **Navigate to API Keys**
   - Go to: https://platform.openai.com/api-keys
   - Or click: Account → API Keys (in left sidebar)

2. **Create New Secret Key**
   - Click "+ Create new secret key"
   - Name it: "resumeTailor" (optional)
   - Click "Create secret key"

3. **Copy & Store Safely**
   - Copy the key (it looks like: `sk-...`)
   - ⚠️  Save it somewhere secure (password manager)
   - You won't see it again after closing

#### Step 3: Set Environment Variable

```bash
# Copy your API key and run:
export OPENAI_API_KEY="sk-xxxxxxxxxxxx"

# Verify it works:
echo $OPENAI_API_KEY
```

#### Step 4: Make It Permanent (Optional)

Add to your shell config file (`~/.bashrc` or `~/.zshrc`):

```bash
# Add this line at the end:
export OPENAI_API_KEY="sk-xxxxxxxxxxxx"

# Then reload:
source ~/.bashrc  # or source ~/.zshrc
```

#### Step 5: Test Setup

```bash
python3 -c "import openai; print('✅ OpenAI ready')"

# If error: "No module named openai"
# Install: pip install openai
```

### Pricing

- GPT-4: ~$0.03-0.06 per 1K tokens
- GPT-3.5: ~$0.0005-0.002 per 1K tokens
- Typical resume generation: ~$0.05-0.10

**Set Usage Limits:**
1. Go to: https://platform.openai.com/account/billing/limits
2. Set "Hard limit" to a safe amount (e.g., $5/month)

### Usage with resumeTailor

**End-to-end pipeline (recommended):**

```bash
./bin/tailor_resume_generic.sh \
  --base-resume ~/my-resume.md \
  --agent openai \
  --api-key sk-xxxxxxxxxxxx \
  --model gpt-4o \
  https://linkedin.com/jobs/view/1234567
```

**Standalone script generation:**

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

> ⚠️ Use `gpt-4o` (not `gpt-4`). The original `gpt-4` has a 10K TPM rate limit that's too low for the prompt size.

### Troubleshooting

| Issue | Solution |
|-------|----------|
| "Invalid API key" | Check: https://platform.openai.com/api-keys (key may have expired) |
| "Rate limit exceeded" / 429 error | Use `--model gpt-4o` instead of `gpt-4` (higher rate limits) |
| "Quota exceeded" | Add payment method or increase spending limit |
| "openai package not found" | Run: `pip install openai` (inside the `.venv`) |
| "401 Unauthorized" | API key is invalid or expired |
| "No module named 'fpdf'" | Run: `pip install fpdf2` (inside the `.venv`) |

---

## Claude

### What It Is
Anthropic's Claude API. Access to Claude 3 models (Opus, Sonnet, Haiku). Requires paid account.

### Setup Steps

#### Step 1: Create Anthropic Account

1. **Go to Anthropic Console**
   - Visit: https://console.anthropic.com/

2. **Sign Up**
   - Click "Get started" or "Sign up"
   - Use email or Google account
   - Complete email verification

3. **Add Payment Method**
   - Click "Plans" → "API"
   - Add credit card
   - Set budget/limit (recommended: $10/month)

#### Step 2: Create API Key

1. **Navigate to API Keys**
   - Click "Account" (top right)
   - Select "API Keys" from menu
   - Or go directly: https://console.anthropic.com/account/keys

2. **Generate New API Key**
   - Click "+ Generate API Key"
   - Name it: "resumeTailor" (optional)
   - Click "Generate Key"

3. **Copy & Store Safely**
   - Copy the key (it looks like: `sk-ant-...`)
   - Save in password manager
   - You won't see it again

#### Step 3: Set Environment Variable

```bash
# Copy your API key and run:
export ANTHROPIC_API_KEY="sk-ant-xxxxxxxxxxxx"

# Verify:
echo $ANTHROPIC_API_KEY
```

#### Step 4: Make It Permanent (Optional)

Add to `~/.bashrc` or `~/.zshrc`:

```bash
export ANTHROPIC_API_KEY="sk-ant-xxxxxxxxxxxx"
```

Then reload:
```bash
source ~/.bashrc  # or source ~/.zshrc
```

#### Step 5: Test Setup

```bash
pip install anthropic
python3 -c "import anthropic; print('✅ Anthropic ready')"
```

### Pricing

- Claude 3.5 Sonnet: ~$0.003-0.015 per 1K tokens
- Claude 3 Opus: ~$0.015-0.075 per 1K tokens
- Claude 3 Haiku: ~$0.00025-0.00125 per 1K tokens
- Typical resume: ~$0.05-0.15 (depending on model)

**View Usage:**
1. Go to: https://console.anthropic.com/account/usage
2. Check your current spending and limits

### Usage with resumeTailor

**End-to-end pipeline (recommended):**

```bash
./bin/tailor_resume_generic.sh \
  --base-resume ~/my-resume.md \
  --agent claude \
  --api-key sk-ant-xxxxxxxxxxxx \
  --model claude-sonnet-4-20250514 \
  https://linkedin.com/jobs/view/1234567
```

**Standalone script generation:**

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

### Troubleshooting

| Issue | Solution |
|-------|----------|
| "Invalid API key" | Check: https://console.anthropic.com/account/keys |
| "Authentication failed" | API key may have been revoked; generate new one |
| "anthropic package not found" | Run: `pip install anthropic` |
| "429 Too Many Requests" | Rate limited; wait a minute then retry |
| "400 Bad Request" | Check model name is valid (default: claude-sonnet-4-20250514) |
| "No module named 'fpdf'" | Run: `pip install fpdf2` (inside the `.venv`) |

---

## OpenRouter

### What It Is
Unified API for 100+ models (Claude, GPT, Llama, Mistral, etc.). Usually cheaper than direct APIs. Free account.

### Setup Steps

#### Step 1: Create OpenRouter Account

1. **Go to OpenRouter**
   - Visit: https://openrouter.ai/

2. **Sign Up**
   - Click "Sign in" (top right)
   - Choose: "Create an account"
   - Use email, Google, or GitHub
   - Verify email

3. **No Payment Required (Yet)**
   - Free account to explore
   - Optional: Add payment method if you want to use premium models

#### Step 2: Create API Key

1. **Navigate to Settings**
   - Click your avatar (top right)
   - Select "Settings" or go to: https://openrouter.ai/account/api-keys

2. **Create New API Key**
   - Click "+ Create Key"
   - Name it: "resumeTailor" (optional)
   - Click "Create"

3. **Copy & Store**
   - Copy the key (looks like: `sk-or-...`)
   - Save securely
   - Can regenerate anytime

#### Step 3: Set Environment Variable

```bash
# Copy your API key and run:
export OPENROUTER_API_KEY="sk-or-xxxxxxxxxxxx"

# Verify:
echo $OPENROUTER_API_KEY
```

#### Step 4: Make It Permanent (Optional)

Add to `~/.bashrc` or `~/.zshrc`:

```bash
export OPENROUTER_API_KEY="sk-or-xxxxxxxxxxxx"
```

Then reload:
```bash
source ~/.bashrc  # or source ~/.zshrc
```

#### Step 5: Test Setup

```bash
pip install requests
python3 -c "import requests; print('✅ OpenRouter ready')"
```

### Pricing

Cheapest per model:
- Llama 3.1: ~$0.001-0.003 per 1K tokens ⭐ CHEAPEST
- Mistral: ~$0.002-0.007 per 1K tokens
- Claude (via OpenRouter): ~$0.003-0.015 per 1K tokens
- GPT-4 (via OpenRouter): ~$0.01-0.03 per 1K tokens

Typical resume: **$0.01-0.10** (usually 30-50% cheaper than direct APIs)

**View Usage:**
1. Go to: https://openrouter.ai/account/limits
2. See current month's usage

### Available Models

Full list at: https://openrouter.ai/models

Popular choices:
```
--model anthropic/claude-sonnet-4  # Best quality
--model mistral/mistral-large      # Good balance
--model meta-llama/llama-3.1-405b  # Cheapest, still good
--model openai/gpt-4o              # OpenAI quality
```

### Usage with resumeTailor

**End-to-end pipeline (recommended):**

```bash
./bin/tailor_resume_generic.sh \
  --base-resume ~/my-resume.md \
  --agent openrouter \
  --api-key sk-or-xxxxxxxxxxxx \
  --model anthropic/claude-sonnet-4 \
  https://linkedin.com/jobs/view/1234567
```

**Standalone script generation:**

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

### Troubleshooting

| Issue | Solution |
|-------|----------|
| "Invalid API key" | Check: https://openrouter.ai/account/api-keys |
| "Model not found" | Use `--model claude-3.5-sonnet` (default) or check https://openrouter.ai/models |
| "requests package not found" | Run: `pip install requests` |
| "429 Too Many Requests" | Rate limited; wait 1 minute then retry |
| "Free account limit reached" | Add payment method to continue |

---

## Manual

### What It Is
Copy-paste mode. No API setup needed. Works with any AI tool (Claude.com, ChatGPT, Perplexity, etc.).

### Setup Steps

No setup required! Just:

1. **Run the generator**
   ```bash
   python3 bin/generate_with_agent.py \
     --agent manual \
     --jd companies/Acme/Acme_jd.md \
     --resume ~/my-resume.md \
     --company Acme
   ```

2. **Copy the prompt displayed**

3. **Go to your AI tool**
   - Claude.com, ChatGPT, Perplexity, or any LLM

4. **Paste the prompt**

5. **Copy the Python code from the response**

6. **Save to file**
   ```bash
   # macOS
   pbpaste > companies/Acme/generate_resume_acme.py
   
   # Linux
   xclip -o > companies/Acme/generate_resume_acme.py
   
   # Windows (PowerShell)
   Get-Clipboard > companies/Acme/generate_resume_acme.py
   ```

### Pricing
Free!

### Usage with resumeTailor

```bash
python3 bin/generate_with_agent.py \
  --agent manual \
  --jd companies/Acme/Acme_jd.md \
  --resume ~/my-resume.md \
  --company Acme

# Then follow on-screen instructions
```

---

## Quick Reference

### API Key Format

| Agent | Key Format | Example |
|-------|-----------|---------|
| OpenAI | `sk-...` | `sk-proj-1a2b3c...` |
| Claude | `sk-ant-...` | `sk-ant-1a2b3c...` |
| OpenRouter | `sk-or-...` | `sk-or-1a2b3c...` |
| Wibey | (CLI only) | N/A |
| Manual | (no API) | N/A |

### Environment Variable Names

```bash
# OpenAI
export OPENAI_API_KEY="..."

# Claude
export ANTHROPIC_API_KEY="..."

# OpenRouter
export OPENROUTER_API_KEY="..."
```

### Setup Checklist

- [ ] **Venv created**: `python3 -m venv .venv` in repo root
- [ ] **Core packages**: `pip install pdfplumber python-docx pypdf fpdf2` (inside `.venv`)
- [ ] **Wibey**: Claude Code installed ✓
- [ ] **OpenAI**: Account created, API key generated, `pip install openai`
- [ ] **Claude**: Account created, API key generated, `pip install anthropic`
- [ ] **OpenRouter**: Account created, API key generated, `pip install requests`
- [ ] **Manual**: No setup needed ✓

### Command Templates (End-to-End Pipeline)

```bash
# Wibey (default — no extra flags needed)
./bin/tailor_resume_generic.sh --base-resume ~/resume.md <job-url>

# OpenAI
./bin/tailor_resume_generic.sh --base-resume ~/resume.md --agent openai --api-key sk-... --model gpt-4o <job-url>

# Claude
./bin/tailor_resume_generic.sh --base-resume ~/resume.md --agent claude --api-key sk-ant-... --model claude-sonnet-4-20250514 <job-url>

# OpenRouter
./bin/tailor_resume_generic.sh --base-resume ~/resume.md --agent openrouter --api-key sk-or-... --model anthropic/claude-sonnet-4 <job-url>
```

---

## Cost Summary

For one resume generation:

| Agent | Cost | Setup Time |
|-------|------|-----------|
| Wibey | Free | < 5 min |
| OpenRouter (Llama) | $0.01-0.03 | 5-10 min |
| OpenAI (GPT-3.5) | $0.05 | 10-15 min |
| Claude (Sonnet) | $0.05-0.10 | 10-15 min |
| OpenAI (GPT-4) | $0.10+ | 10-15 min |
| Manual | Free | 5-10 min (slower) |

---

## Recommended Setups

### Budget-Conscious
Use **OpenRouter** with `llama-3.1-405b` (~$0.01-0.03 per resume)

### Quality-First
Use **Claude** or **OpenRouter** with `claude-3.5-sonnet` (~$0.05-0.10)

### Best Value
Use **OpenRouter** with `claude-3.5-sonnet` (~$0.03-0.08, cheaper than direct)

### Fastest Setup
Use **Wibey** (already in JetBrains/Claude Code, free)

### No API/Cost
Use **Manual** mode (free, just copy-paste)

---

## Troubleshooting General Issues

### "module not found" errors

```bash
# OpenAI
pip install openai

# Claude
pip install anthropic

# OpenRouter
pip install requests
```

### API Key not working

1. **Check key is copied correctly** (no extra spaces)
2. **Verify it hasn't expired** (check service dashboard)
3. **Regenerate if needed** (create new key on service)
4. **Check billing is set up** (add payment method)

### Still having issues?

See the **Troubleshooting** section in MULTI_AGENT_GUIDE.md for more help.

---

**Ready to choose an agent and get started? Pick one and follow its setup guide!** 🚀
