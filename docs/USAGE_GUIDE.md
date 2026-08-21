# Generic Resume Tailoring Tools

This directory contains **generic, shareable** resume tailoring scripts and agents designed to work with **any candidate**.

You can use these tools to create tailored resumes for job applications, and share them with others who want to do the same.

---

## What's Included

### 1. **`bin/tailor_resume_generic.sh`** — Main Script

A bash script that:
- Fetches job descriptions from URLs (or accepts manual input)
- Extracts company name automatically
- Saves the JD for reference
- **Does NOT generate the resume automatically** (that's the agent's job)
- Prepares the workspace and metadata for resume generation

#### Usage

```bash
./tailor_resume_generic.sh \
  --base-resume /path/to/your/resume.md \
  --candidate-name "Jane Smith" \
  --output-dir ~/TailoredResumes/companies \
  https://jobs.lever.co/acme/abc123
```

#### Required Options

| Option | Example | Purpose |
|--------|---------|---------|
| `--base-resume` | `/path/to/resume.md` | Your comprehensive/base resume (markdown) |
| `--candidate-name` | `"Jane Smith"` | Your full name |
| `--output-dir` | `~/TailoredResumes/companies` | Where to save tailored resumes |

#### Optional Options

| Option | Purpose |
|--------|---------|
| `--comprehensive-resume <path>` | Override base resume for validation (default: same as base) |
| `--validator <path>` | Path to `resume_validator.py` (validation is skipped if not provided) |
| `--force` | Skip match score gate |
| `--skip-interview-prep` | Skip interview prep generation |
| `--help` | Show full help message |

#### What It Outputs

```
<output-dir>/<Company>/
    tailoring_info.txt       ← metadata for this tailoring
    <Company>_jd.md          ← fetched/pasted job description
```

After running the script, you'll get guidance on the next steps.

---

### 2. **`.wibey/agents/resume-tailor-generic.md`** — AI Agent

A Wibey agent that:
- Analyzes your comprehensive resume and the job description
- Selects and reorders bullets based on JD relevance
- Generates a Python script to produce tailored DOCX/PDF files
- Optionally validates against a custom rule set

#### How to Use

The agent is triggered when you say things like:

- "Tailor my resume for {Company}"
- "Create a tailored resume for {JD}"
- "Generate resume script for {role}"

#### What It Needs

Provide the agent with:

1. **Your comprehensive resume** (markdown file) — all your bullets, skills, experience
2. **Job description** (URL, pasted text, or file)
3. **Company name** (auto-detected or you specify it)
4. **Candidate name, location, email, etc.**

#### What It Produces

```
generate_resume_{company_lowercase}.py
```

A Python script that, when run, generates:
- `{CandidateName}_{Company}.pdf` — tailored PDF
- `{CandidateName}_{Company}.docx` — tailored DOCX

---

## Workflow

### Quick Start

1. **Prepare your base resume** (markdown file with all experience, skills, education)

```markdown
# Jane Smith
Email: jane@example.com | Phone: (555) 123-4567 | LinkedIn: linkedin.com/in/jane

## Summary
...

## Skills
...

## Experience

### Senior Engineer — Company A (January 2020 - Present)
- Bullet 1: ...
- Bullet 2: ...

### Engineer — Company B (2018 - 2020)
...

## Education
...
```

2. **Run the prep script**

```bash
~/TailoredResumes/bin/tailor_resume_generic.sh \
  --base-resume ~/my-resume.md \
  --candidate-name "Jane Smith" \
  --output-dir ~/tailored_resumes \
  https://jobs.lever.co/acme/abc123
```

3. **Use the agent to generate the tailored script**

Tell Wibey (or call the agent):
```
tailor my resume for Acme Corp

Here's my comprehensive resume: [paste or reference]
Here's the job description: [paste or reference]
```

4. **Run the generated Python script**

```bash
python3 ~/tailored_resumes/AcmeCorp/generate_resume_acmecorp.py
```

5. **Review and submit**

- Check both PDF and DOCX for correctness
- Verify the resume is exactly 2 pages
- Submit to the job application portal

---

## How to Share These Tools

### Step 1: Prepare Your Copy

Clone or copy this directory structure:

```
TailoredResumes/
├── bin/
│   ├── tailor_resume_generic.sh
│   └── ... (other utility scripts)
├── README_GENERIC.md           ← You are here
└── ... (other files)
```

### Step 2: Package for Sharing

Create a distributable archive:

```bash
cd ~/TailoredResumes
tar -czf tailored-resumes-generic.tar.gz \
  bin/tailor_resume_generic.sh \
  README_GENERIC.md \
  config/                        # if you have templates
```

Or:

```bash
zip -r tailored-resumes-generic.zip \
  bin/tailor_resume_generic.sh \
  README_GENERIC.md
```

### Step 3: Share

- Email the archive to colleagues
- Put it in a shared git repo
- Add it to your documentation/wiki

### Step 4: Recipients Use It

Each person should:

1. Extract the archive
2. Create their own `my-resume.md` (comprehensive version)
3. Run the prep script with their name and output directory
4. Use the agent to generate tailored scripts
5. Review and submit

---

## Advanced Usage

### Using a Custom Validator

If you have a `resume_validator.py` script (with custom rules), pass it to the script:

```bash
./tailor_resume_generic.sh \
  --base-resume ~/my-resume.md \
  --candidate-name "Jane Smith" \
  --output-dir ~/tailored_resumes \
  --validator ~/validator.py \
  https://jobs.lever.co/acme/abc123
```

The agent will then validate the generated script against your rules.

### Using a Template Generator

If you have an example generator script (`generate_resume_example.py`), share it alongside these tools. Recipients can use it as a pattern to understand what the agent should produce.

### Automating for Multiple Users

Create a wrapper that sets common defaults:

```bash
#!/bin/bash
# wrapper.sh — Custom defaults for your team

OUTPUT_DIR="$HOME/team-resumes"
VALIDATOR="/shared/resume_validator.py"

./tailor_resume_generic.sh \
  --validator "$VALIDATOR" \
  --output-dir "$OUTPUT_DIR" \
  "$@"
```

---

## Key Differences from the Original Version

| Feature | Original | Generic (`tailor_resume_generic.sh`) |
|---------|------|---------|
| Candidate | Hardcoded | Any candidate (via `--candidate-name`) |
| Base resume | Fixed path | Via `--base-resume` option |
| Output directory | Fixed path | Via `--output-dir` option |
| Validator | Always used (hardcoded) | Optional via `--validator` |
| Interview prep | Auto-generated | Skipped (not generic) |
| Agent | Person-specific | Generic for any candidate |

---

## Troubleshooting

### Q: Script says "No company name provided"

**A:** The script couldn't auto-detect the company name from the URL or pasted content. Make sure you:
- Provide a valid job URL (not a shortened/redirected URL)
- If pasting, include company name in the text

### Q: Agent won't generate the script

**A:** Make sure you:
- Provided both the comprehensive resume AND the job description
- Specified the candidate name
- Confirmed the output directory

### Q: Generated Python script has errors

**A:** The agent may have misunderstood your resume format. Help by:
- Providing a clearer example (structure bullets with hyphens: `- Bullet text`)
- Specifying date ranges clearly (`January 2020 - Present`)
- Confirming all skills/sections are included

### Q: Resume doesn't fit 2 pages

**A:** Reduce bullet count:
- Keep 8-10 bullets per recent role
- Reduce to 3-5 bullets for older roles (5+ years)
- Use shorter bullet text where possible
- Run the generator again

### Q: Validator fails on my custom rules

**A:** Check your validator script's output:
```bash
python3 ~/validator.py ~/tailored_resumes/Company/generate_resume_company.py
```

Look at the specific rule that failed and adjust the generated script accordingly.

---

## Examples

### Example 1: Basic Usage

```bash
./tailor_resume_generic.sh \
  --base-resume ~/my-resume.md \
  --candidate-name "Alice Johnson" \
  --output-dir ~/tailored \
  https://jobs.lever.co/google/abc123
```

### Example 2: With Custom Validator

```bash
./tailor_resume_generic.sh \
  --base-resume ~/my-resume.md \
  --candidate-name "Bob Chen" \
  --output-dir ~/tailored \
  --validator ~/my-company-validator.py \
  https://boards.greenhouse.io/company/jobs/1234567
```

### Example 3: Manual JD Input

```bash
./tailor_resume_generic.sh \
  --base-resume ~/my-resume.md \
  --candidate-name "Carol Smith" \
  --output-dir ~/tailored \
  https://example.com/job-posting

# Script will ask you to paste the JD if fetch fails
# Paste the text, then Ctrl+D to confirm
```

---

## Next Steps

1. **Try it**: Run the prep script with your resume and a job URL
2. **Generate**: Use the agent to create your first tailored script
3. **Test**: Run the generated script and review the output
4. **Refine**: Adjust bullets/content as needed
5. **Share**: Help others use these tools

---

## Questions or Feedback?

- Issues with the script? Check the output messages — they usually guide you to the fix
- Want to extend these tools? Create a custom agent or validator for your use case
- Have improvements? Consider contributing back to the original repository

---

## License & Attribution

These tools are provided as-is for personal and professional use. Feel free to:
- ✅ Use them for your own resume tailoring
- ✅ Share them with colleagues and friends
- ✅ Modify them for your specific needs
- ✅ Build on top of them (custom validators, agents, etc.)

Attribution appreciated but not required.

---

**Happy tailoring! 📄✨**
