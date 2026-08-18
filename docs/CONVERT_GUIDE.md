# Resume Conversion Guide

Convert your existing PDF or DOCX resume to Markdown format for use with the generic resume tailoring tools.

---

## Installation

### Requirements

Install one or both of these libraries:

```bash
# For PDF support (pdfplumber is preferred)
pip install pdfplumber

# Fallback PDF support
pip install pypdf

# For DOCX support
pip install python-docx
```

### Check Installation

```bash
python3 -c "import pdfplumber; print('✓ pdfplumber installed')"
python3 -c "import docx; print('✓ python-docx installed')"
```

---

## Quick Start

### Convert PDF

```bash
python3 bin/convert_resume_to_md.py ~/resume.pdf

# Output: ~/resume.md
```

### Convert DOCX

```bash
python3 bin/convert_resume_to_md.py ~/resume.docx

# Output: ~/resume.md
```

### Specify Output File

```bash
python3 bin/convert_resume_to_md.py ~/resume.pdf ~/my-resume.md

# Output: ~/my-resume.md
```

### Interactive Mode (Review Before Saving)

```bash
python3 bin/convert_resume_to_md.py ~/resume.pdf --interactive
```

---

## What It Does

1. **Extracts text** from PDF or DOCX
2. **Parses structure** (sections: Summary, Skills, Experience, etc.)
3. **Formats as Markdown** with proper headers and bullets
4. **Saves output** as a `.md` file ready for resume tailoring

### Detected Sections

- Name (first non-empty line)
- Contact info (email, phone, LinkedIn)
- Summary / Objective
- Skills
- Experience / Work History
- Education
- Certificates
- Awards
- Patents

---

## Example: Step-by-Step

### 1. Convert Your Resume

```bash
$ python3 bin/convert_resume_to_md.py ~/Downloads/Jane_Smith_Resume.pdf

📄  Converting: ~/Downloads/Jane_Smith_Resume.pdf
📝  Output: ~/Downloads/Jane_Smith_Resume.md

🔍  Extracting text...
✓  Extracted 3245 characters

📊  Parsing resume structure...
✓  Found: name, 3 contact lines, 4 experience entries, 2 education entries

✍️   Converting to Markdown...
✓  Generated 2890 characters of Markdown

✅  Saved: ~/Downloads/Jane_Smith_Resume.md

📋  Next steps:
   1. Review the markdown file: ~/Downloads/Jane_Smith_Resume.md
   2. Fix any parsing errors (section headers, bullets, etc.)
   3. Add missing content (skills, experience details, etc.)
```

### 2. Review and Edit

Open the generated markdown file in your editor:

```bash
vim ~/Downloads/Jane_Smith_Resume.md
# or
code ~/Downloads/Jane_Smith_Resume.md
```

### 3. Use with Tailoring Script

```bash
./tailor_resume_generic.sh \
  --base-resume ~/Downloads/Jane_Smith_Resume.md \
  --candidate-name "Jane Smith" \
  --output-dir ~/tailored_resumes \
  https://jobs.lever.co/company/job-id
```

---

## Common Issues & Fixes

### Issue 1: Sections Not Detected

**Symptom**: Your markdown is mostly in one section, or some sections are missing.

**Fix**: Open the generated `.md` file and manually add section headers:

```markdown
## Summary
Your summary text here...

## Skills
- Skill 1
- Skill 2

## Experience
...
```

### Issue 2: Bullets Are Not Formatted

**Symptom**: Bullet points appear as plain text instead of markdown bullets.

**Fix**: Add dashes to create bullets:

```markdown
## Experience

### Senior Engineer — Acme Corp (2020 - Present)
- Bullet 1: Implemented feature X
- Bullet 2: Led team of Y engineers
```

### Issue 3: Experience Section is Messy

**Symptom**: Job titles, companies, and dates are jumbled together.

**Fix**: Manually structure experience entries:

```markdown
### Job Title — Company Name (Month Year - Month Year)
- Bullet describing achievement
- Bullet describing impact
```

### Issue 4: PDF Won't Extract

**Symptom**: Error like "pdfplumber not installed"

**Fix**: Install the library:

```bash
pip install pdfplumber
```

Or use the fallback:

```bash
pip install pypdf
```

### Issue 5: DOCX Won't Convert

**Symptom**: Error like "python-docx not installed"

**Fix**: Install it:

```bash
pip install python-docx
```

---

## Markdown Template

Here's a clean template to follow after conversion:

```markdown
# Jane Smith

**Email:** jane@example.com | **Phone:** (555) 123-4567 | **LinkedIn:** linkedin.com/in/janesmith | **Location:** San Francisco, CA

## Summary

Experienced Staff Software Engineer with 15+ years building scalable distributed systems. Expertise in cloud infrastructure (AWS, Kubernetes), real-time data pipelines, and leading high-performing engineering teams. Proven track record delivering mission-critical systems at scale.

## Skills

**Cloud & Infrastructure:** AWS (EC2, S3, RDS), Kubernetes, Docker, Terraform, CloudFormation

**Languages:** Python, Java, Go, SQL, TypeScript

**Data & Real-Time:** Kafka, Debezium, Elasticsearch, PostgreSQL, Redis

**Leadership:** Technical mentoring, team leadership, architecture design, cross-functional collaboration

## Experience

### Senior Staff Engineer — Acme Corp (January 2022 - Present)
- Led migration of monolithic platform to microservices, reducing deployment time from 45 min to 5 min
- Designed and implemented real-time data pipeline processing 500K events/second with sub-100ms latency
- Mentored 8 engineers, two of whom earned promotions; established code review standards

### Staff Engineer — BigTech (June 2019 - December 2021)
- Built distributed cache layer (Redis cluster) serving 100M requests/day with 99.99% uptime
- Architected Kubernetes migration for 50+ services, reducing ops overhead by 60%
- Led infrastructure team of 5 engineers; designed and delivered SLA monitoring system

### Senior Software Engineer — StartupXYZ (2016 - 2019)
- Developed core API platform handling 1M+ requests/day in production
- Implemented automated testing and CI/CD pipeline, reducing manual testing by 75%

## Education

- **MS, Computer Science** — University of California (2016)
- **BS, Engineering** — State University (2014)

## Certifications

- Kubernetes Administrator (CKAD), Linux Foundation (2021)
- AWS Solutions Architect Professional (2020)

## Awards

- Engineering Excellence Award, Acme Corp (2023)
- Innovation Prize, BigTech (2020)
```

---

## Tips for Quality

After conversion, check:

- ✅ Name is at the top
- ✅ Contact info (email, phone, location) is present
- ✅ Summary is 3-4 sentences
- ✅ Skills are organized by category
- ✅ Experience shows: **Title — Company (Dates)**
- ✅ Bullets start with action verbs (Led, Built, Designed, etc.)
- ✅ No formatting artifacts (extra spaces, weird characters)
- ✅ Dates are consistent format (Month Year - Month Year)
- ✅ Education includes degree, field, school, year

---

## Advanced: Custom Parsing

If the automated conversion doesn't work well for your resume, you can:

1. **Copy the raw text** from the PDF/DOCX
2. **Create markdown manually** using the template above
3. **Use the conversion script as a starting point**, then edit

Or, for complex resumes:

```bash
# Extract text only (no structure parsing)
python3 -c "
from convert_resume_to_md import extract_text
text = extract_text('resume.pdf')
with open('resume_raw.txt', 'w') as f:
    f.write(text)
"
```

Then manually format the extracted text as markdown.

---

## Next Steps

1. Convert your resume: `python3 bin/convert_resume_to_md.py ~/resume.pdf`
2. Review and edit the markdown file
3. Use it with the tailoring script: `./tailor_resume_generic.sh --base-resume ~/resume.md ...`
4. Generate tailored resumes for job applications

---

**Questions?** Check the main README_GENERIC.md for more details on the tailoring workflow.
