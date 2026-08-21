# Resume Tailoring Rules

**Authority:** This document is the single source of truth for all rules enforced during resume tailoring. All resume generation scripts and agents reference this file.

---

## Content Rules (Hard Failures)

These rules are **mechanically enforced** by the validator. Violations cause generation to fail.

### Rule 6: No Metrics in Tailored Resumes
**Rationale:** Metrics date quickly and may not match the current job context.

❌ **Forbidden patterns:**
- Numeric counts: "25+ repositories", "4,300+ commits", "10+ engineers"
- Transaction/impression counts: "processed 5M transactions", "1B+ impressions"
- Specific velocity: "delivered 12 features per sprint"

✅ **Allowed:**
- Qualitative impact: "Handled high-volume production workloads"
- Percentage improvements: "Improved API latency by 60%"
- Ratios: "Mentored 1:1 with two engineers"

**How to verify:** Run the generator script — validator will flag any numeric counts before PDF generation.

---

### Rule 6a: No PR Review Bullets
**Rationale:** "Reviewed PRs" is expected, not noteworthy.

❌ **Forbidden:**
- "Reviewed and approved all team PRs"
- "Performed technical code reviews"
- "Enforced PR review standards"

✅ **Instead, highlight impact:**
- "Established code review culture that improved onboarding time by 40%"
- "Created review guidelines that reduced bug escapes by 25%"

---

### Rule 10: All Bullets Must Exist in Comprehensive Resume
**Rationale:** Ensures factual accuracy and prevents fabrication.

**How it works:**
1. Comprehensive resume is your single source of truth
2. Every tailored bullet must exist verbatim (or be a minor reword) in comprehensive
3. Validator checks this automatically and exits if a bullet is not found
4. No new bullets can be synthesized — only reorder and select from existing ones

**How to fix violations:**
- If you want to use a bullet about an accomplishment, add it to comprehensive first
- Then tailored resumes can select and reorder it

---

### Rule 11: Core Accomplishments Priority
**For tailored resumes matching Walmart/advertising platform experience:**

1. **Always start with the 10 locked Core Accomplishment bullets** from comprehensive resume
2. Reorder by JD relevance (most relevant first)
3. Only ADD supplementary bullets if they fill a specific JD gap
4. These bullets have been vetted and are proven strong across multiple roles

**Location in comprehensive:** "Core Accomplishments (Priority Bullets for All Tailored Resumes)" section

---

### Rule 12: Strategic Bullet Selection for Staff/Senior Roles
**For Staff/Senior/Principal level positions:**

**Prioritize (in order):**
1. **Architecture & System Design** — Kubernetes, service mesh, API design, scalability
2. **Technical Leadership** — Mentorship, team growth, technical standards, code review culture
3. **Operational Excellence** — Observability, zero-downtime deployments, reliability
4. **Cross-Team Impact** — Platform enablement, adoption, downstream value

**De-prioritize:**
- Feature-level implementation work (use only if JD explicitly requires it)
- Individual contributor contributions (save for mid-level roles)

**Example reordering:**
- **BAD:** Feature work first, then leadership, then architecture (chronological)
- **GOOD:** Architecture + leadership first, feature work last (relevance to level)

---

### Internal Terms Banned
**These terms are blocked from tailored resumes** (not expanded/unexplained):

- **WCNP** — Use "Walmart Cloud Native Platform" or specific product name
- **DARPA** — Unexplained "DARPA" is blocked; explain context if included
- **OneOps** — Use full name or specific product
- **Strati** — Unexplained Strati is blocked
- **CCM** — Unexplained CCM is blocked

**Rationale:** Walmart-internal acronyms confuse external recruiters. Spell them out or use product names.

---

## ATS (Applicant Tracking System) Rules

ATS systems parse resumes as plain text and extract keywords. These rules ensure your resume survives automated screening.

### ATS-1: Full Forms for Abbreviations
**When to use:** If an abbreviation appears in the JD, expand it in the resume.

**Required expansions** (validator warns if missing):
- "Kubernetes" must appear (not just "K8s")
- "Continuous Integration / Continuous Delivery (CI/CD)" at least once in Skills/Summary
- "Model Context Protocol (MCP)" at least once if MCP is mentioned
- "Change Data Capture (CDC)" at least once if CDC is mentioned
- "OpenTelemetry" (already full form)

**Universally understood** (no expansion required):
- SOX, LDAP, API, PSD2, AWS, GCP, ML

**Format:** Write full form once, then abbreviation in context: "Kubernetes (K8s)", "Continuous Integration / Continuous Delivery (CI/CD)"

---

### ATS-2: Standard Section Headings
**Required headings** (exact names):
- `Summary` (not "About Me", "Profile", "Executive Summary")
- `Skills` (not "Tech Stack", "Technologies", "Core Competencies")
- `Experience` (not "Work History", "Career", "Professional Experience")
- `Education`

**Optional headings** (recognized by ATS):
- Certifications
- Awards & Recognition
- Patents
- Projects

---

### ATS-3: No Raw Unicode
**Format:**
- Use ASCII dashes (`-`), not em dashes (`—`) or en dashes (`–`)
- Use straight quotes (`"`), not curly quotes (`"`)
- Use regular apostrophes (`'`), not smart quotes (`'`)

**Why:** Some ATS systems fail to parse Unicode correctly, treating it as line breaks or garbage.

---

### ATS-4: JD Keyword Matching
**Before submitting, do this manually:**

1. Scan the JD for 5-10 key technical noun phrases
   - Examples: "distributed systems", "Go programming", "event streaming", "Kafka"
2. Verify each phrase appears **verbatim** in your resume (Skills or Summary section)
3. If JD says "Go" as a language, ensure "Go" (not "Golang") appears in Skills
4. If JD title is "Staff Software Engineer", use that exact title in your Summary

**Why:** ATS performs exact-match keyword extraction. Synonyms ("event queue" vs "Kafka") may not match.

---

### ATS-5: File Format Choice
- **DOCX** → Use for online portal submissions (ATS parses DOCX cleanly)
- **PDF** → Use when emailing directly to a human recruiter

Both are generated automatically — choose based on submission method.

---

### ATS-6: Work Date Format
**Required:** Include months in date ranges

✅ **Correct:** "June 2020 - May 2026"
❌ **Wrong:** "2020 - 2026"

**Why:** ATS needs months to calculate total experience accurately.

---

## Validation Workflow

### Before Each Tailoring Session

1. **Read comprehensive resume completely** — understand what bullets are available
2. **Read job description** — identify level (Staff, Senior, Mid) and key requirements
3. **Start with Rule 11** — 10 Core Accomplishment bullets from comprehensive
4. **Reorder by JD relevance** — most relevant first (Rule 12 for Staff roles)
5. **Add supplementary bullets only if needed** — fill gaps not covered by core bullets
6. **Create/update generation script** — using verified bullets only
7. **Run validator** — check all rules before generating PDF
8. **Verify filenames** — match naming convention

---

### Fixing Validation Failures

**If validator fails:**

1. Read the error message — it shows exactly which rule was violated
2. Identify the offending bullet or pattern
3. Fix in the generation script:
   - Remove metrics (Rule 6)
   - Source bullet from comprehensive (Rule 10)
   - Spell out abbreviations (ATS-1)
4. Re-run validator
5. Once validation passes, proceed with PDF/DOCX generation

**Example validator output:**
```
❌ Rule 6 (No metrics): "25+ repositories" found in generate_resume_acme.py line 42
   Remove numeric counts and reword to focus on impact.

✅ All other rules pass.

Fix the above and re-run validator.
```

---

## Output File Naming Convention

| File Type | Format | Example |
|-----------|--------|---------|
| PDF | `{FirstName}_{LastName}_{CompanyName}.pdf` | `Jane_Smith_Acme.pdf` |
| DOCX | `{FirstName}_{LastName}_{CompanyName}.docx` | `Jane_Smith_Acme.docx` |
| Generator script | `generate_resume_{company_lowercase}.py` | `generate_resume_acme.py` |

All files auto-save to `companies/{CompanyName}/` directory.

---

## Quick Reference Checklist

Before generating PDF, verify:

- [ ] All bullets sourced from comprehensive resume (Rule 10)
- [ ] No metrics/counts in bullets (Rule 6)
- [ ] No PR review bullets (Rule 6a)
- [ ] Internal terms explained or removed (WCNP, DARPA, etc.)
- [ ] Validator passes without errors
- [ ] "Kubernetes" appears (not just "K8s") if mentioned (ATS-1)
- [ ] "Continuous Integration / Continuous Delivery (CI/CD)" appears once (ATS-1)
- [ ] Section headings are standard: Summary, Skills, Experience, Education (ATS-2)
- [ ] Work dates include months (ATS-6)
- [ ] 5-10 JD keywords appear verbatim (ATS-4) — manual check
- [ ] Filename matches convention (Naming Convention)

---

## Contact & Questions

If rules conflict with your situation:

1. Check if your use case is documented in "When to Break the Rules" (see comprehensive resume)
2. Contact the maintainer for rule clarification
3. All rule changes must be approved and documented here

---

**Last Updated:** August 17, 2026  
**Authority:** This document is the canonical source for all resume tailoring rules.
