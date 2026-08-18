#!/usr/bin/env python3
"""
convert_resume_to_md.py — Convert PDF/DOCX resumes to Markdown format

Supports:
  - PDF files (via pypdf or pdfplumber)
  - DOCX files (via python-docx)

Usage:
  python3 convert_resume_to_md.py <input_file> [output_file]

Examples:
  python3 convert_resume_to_md.py ~/resume.pdf
  python3 convert_resume_to_md.py ~/resume.docx ~/resume.md
  python3 convert_resume_to_md.py ~/resume.pdf --interactive
"""

import sys
import os
import re
from pathlib import Path
from typing import List, Tuple

def extract_text_from_docx(filepath: str) -> str:
    """Extract text from DOCX file."""
    try:
        from docx import Document
        doc = Document(filepath)
        text = []
        for para in doc.paragraphs:
            if para.text.strip():
                text.append(para.text)
        return "\n".join(text)
    except ImportError:
        print("❌  python-docx not installed. Install with:")
        print("   pip install python-docx")
        sys.exit(1)
    except Exception as e:
        print(f"❌  Error reading DOCX: {e}")
        sys.exit(1)

def extract_text_from_pdf(filepath: str) -> str:
    """Extract text from PDF file using pdfplumber (preferred) or pypdf."""
    try:
        import pdfplumber
        with pdfplumber.open(filepath) as pdf:
            text = []
            for page in pdf.pages:
                text.append(page.extract_text() or "")
            return "\n".join(text)
    except ImportError:
        try:
            from pypdf import PdfReader
            reader = PdfReader(filepath)
            text = []
            for page in reader.pages:
                text.append(page.extract_text() or "")
            return "\n".join(text)
        except ImportError:
            print("❌  Neither pdfplumber nor pypdf installed. Install one with:")
            print("   pip install pdfplumber    # (recommended)")
            print("   OR")
            print("   pip install pypdf")
            sys.exit(1)
    except Exception as e:
        print(f"❌  Error reading PDF: {e}")
        sys.exit(1)

def extract_text(filepath: str) -> str:
    """Extract text from PDF or DOCX file."""
    ext = Path(filepath).suffix.lower()

    if ext == ".pdf":
        return extract_text_from_pdf(filepath)
    elif ext in [".docx", ".doc"]:
        if ext == ".doc":
            print("⚠️   .doc (old Word format) detected. Converting via docx...")
            # Try with docx library — it may support legacy format
        return extract_text_from_docx(filepath)
    else:
        print(f"❌  Unsupported file format: {ext}")
        print("    Supported: .pdf, .docx, .doc")
        sys.exit(1)

def parse_resume_structure(text: str) -> dict:
    """
    Parse resume text into structured sections.

    Returns:
        dict with keys: name, contact, summary, skills, experience, education, etc.
    """
    lines = text.split("\n")

    # Initialize structure
    resume = {
        "name": "",
        "contact": [],
        "summary": [],
        "skills": [],
        "experience": [],
        "education": [],
        "certificates": [],
        "awards": [],
        "patents": [],
        "raw": text  # Keep raw text for reference
    }

    # Find section headers (common patterns)
    section_patterns = {
        "summary": r"^(Summary|Professional Summary|Objective|Profile)",
        "skills": r"^(Skills|Technical Skills|Core Competencies)",
        "experience": r"^(Experience|Work Experience|Professional Experience)",
        "education": r"^(Education|Certifications & Education)",
        "certificates": r"^(Certificates|Certifications|Professional Certifications)",
        "awards": r"^(Awards|Recognition|Honors)",
        "patents": r"^(Patents|Intellectual Property)",
    }

    current_section = None
    header_found = False

    for i, line in enumerate(lines):
        stripped = line.strip()

        # Skip empty lines
        if not stripped:
            continue

        # First non-empty line is likely the name (if not header-like)
        if not header_found and not any(
            pattern.match(stripped, re.IGNORECASE)
            for section, pattern in section_patterns.items()
        ):
            if len(stripped) < 80 and not re.search(r"[@\(\)]", stripped):
                resume["name"] = stripped
                header_found = True
                continue

        # Check for section headers
        section_found = False
        for section, pattern in section_patterns.items():
            if re.search(pattern, stripped, re.IGNORECASE):
                current_section = section
                section_found = True
                break

        if section_found:
            continue

        # Add line to current section
        if current_section:
            resume[current_section].append(stripped)
        elif header_found and not resume["name"]:
            # Contact info lines (usually after name)
            if any(char in stripped for char in ["@", "(", ")"]):
                resume["contact"].append(stripped)

    # Clean up arrays
    for key in ["contact", "summary", "skills", "experience", "education",
                "certificates", "awards", "patents"]:
        resume[key] = [line for line in resume[key] if line.strip()]

    return resume

def format_as_markdown(resume: dict) -> str:
    """Format parsed resume as Markdown."""
    md = []

    # Header
    if resume["name"]:
        md.append(f"# {resume['name']}")
        md.append("")

    # Contact info
    if resume["contact"]:
        md.append("**Contact:** " + " | ".join(resume["contact"]))
        md.append("")

    # Summary
    if resume["summary"]:
        md.append("## Summary")
        for line in resume["summary"]:
            md.append(line)
        md.append("")

    # Skills
    if resume["skills"]:
        md.append("## Skills")
        for line in resume["skills"]:
            # Convert to bullet points if not already
            if not line.startswith("-"):
                md.append(f"- {line}")
            else:
                md.append(line)
        md.append("")

    # Experience
    if resume["experience"]:
        md.append("## Experience")
        md.append("")
        for line in resume["experience"]:
            # Try to identify job title / company lines vs bullets
            if re.search(r"\(|\)|–|—|-\s+\d+", line) or len(line) < 150:
                if line.startswith("-"):
                    md.append(line)
                else:
                    md.append(f"**{line}**")
            else:
                md.append(f"- {line}")
        md.append("")

    # Education
    if resume["education"]:
        md.append("## Education")
        for line in resume["education"]:
            if not line.startswith("-"):
                md.append(f"- {line}")
            else:
                md.append(line)
        md.append("")

    # Certificates
    if resume["certificates"]:
        md.append("## Certificates")
        for line in resume["certificates"]:
            if not line.startswith("-"):
                md.append(f"- {line}")
            else:
                md.append(line)
        md.append("")

    # Awards
    if resume["awards"]:
        md.append("## Awards")
        for line in resume["awards"]:
            if not line.startswith("-"):
                md.append(f"- {line}")
            else:
                md.append(line)
        md.append("")

    # Patents
    if resume["patents"]:
        md.append("## Patents")
        for line in resume["patents"]:
            if not line.startswith("-"):
                md.append(f"- {line}")
            else:
                md.append(line)
        md.append("")

    return "\n".join(md)

def interactive_refine(md_text: str) -> str:
    """Allow user to refine the markdown output."""
    print("\n" + "=" * 70)
    print("PREVIEW (first 50 lines):")
    print("=" * 70)

    lines = md_text.split("\n")
    for i, line in enumerate(lines[:50], 1):
        print(f"{i:3d} | {line}")

    if len(lines) > 50:
        print(f"... ({len(lines) - 50} more lines)")

    print("\n" + "=" * 70)
    print("REVIEW CHECKLIST:")
    print("=" * 70)
    print("✓ Name is correct?")
    print("✓ Contact info is present (email, phone, LinkedIn)?")
    print("✓ Summary section is clear?")
    print("✓ Skills are well-organized?")
    print("✓ Experience section shows role, company, and bullets?")
    print("✓ Education, certificates, awards are included?")
    print("")

    response = input("Save this markdown? [y/n/edit]: ").strip().lower()

    if response in ["y", "yes"]:
        return md_text
    elif response in ["e", "edit"]:
        print("\n⚠️   Manual editing required.")
        print("    The markdown has been saved — open it in an editor to refine manually.")
        return md_text
    else:
        print("❌  Aborted — no file saved.")
        sys.exit(0)

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    interactive = "--interactive" in sys.argv

    # Validate input file
    if not os.path.isfile(input_file):
        print(f"❌  File not found: {input_file}")
        sys.exit(1)

    # Default output file
    if not output_file:
        input_path = Path(input_file)
        output_file = str(input_path.with_suffix(".md"))

    print(f"📄  Converting: {input_file}")
    print(f"📝  Output: {output_file}")
    print("")

    # Extract text
    print("🔍  Extracting text...")
    raw_text = extract_text(input_file)
    print(f"✓  Extracted {len(raw_text)} characters")

    # Parse structure
    print("📊  Parsing resume structure...")
    resume = parse_resume_structure(raw_text)
    print(f"✓  Found: name, {len(resume['contact'])} contact lines, "
          f"{len(resume['experience'])} experience entries, "
          f"{len(resume['education'])} education entries")

    # Format as markdown
    print("✍️   Converting to Markdown...")
    md_text = format_as_markdown(resume)
    print(f"✓  Generated {len(md_text)} characters of Markdown")

    # Interactive review (optional)
    if interactive:
        md_text = interactive_refine(md_text)

    # Write output
    print("")
    try:
        with open(output_file, "w") as f:
            f.write(md_text)
        print(f"✅  Saved: {output_file}")
        print("")
        print("📋  Next steps:")
        print(f"   1. Review the markdown file: {output_file}")
        print("   2. Fix any parsing errors (section headers, bullets, etc.)")
        print("   3. Add missing content (skills, experience details, etc.)")
        print("")
        print("   Then use it with the resume tailoring script:")
        print(f"   ./tailor_resume_generic.sh --base-resume {output_file} ...")

    except IOError as e:
        print(f"❌  Error writing file: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
