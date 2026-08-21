#!/usr/bin/env python3
"""
generate_resume_script.py — Call Claude API to generate a tailored resume Python script.

Usage:
    python3 generate_resume_script.py \
        --comprehensive <path> \
        --jd <path> \
        --candidate <name> \
        --company <name> \
        --output <path> \
        [--api-key <key>] \
        [--model <model>]

If --api-key not provided, tries to detect Wibey plugin context.
If neither works, exits with error.
"""

import sys
import os
import json
import argparse
import subprocess
from pathlib import Path


def detect_wibey_context():
    """Check if running in Wibey plugin context and get API key."""
    # In Wibey plugin context, env vars might be available
    if os.environ.get("WIBEY_API_KEY"):
        return {
            "api_key": os.environ["WIBEY_API_KEY"],
            "model": os.environ.get("WIBEY_MODEL", "claude-opus"),
            "provider": "wibey"
        }

    # Check for .wibey config
    wibey_config = Path.home() / ".wibey" / "config.json"
    if wibey_config.exists():
        try:
            with open(wibey_config) as f:
                config = json.load(f)
                if config.get("api_key"):
                    return {
                        "api_key": config["api_key"],
                        "model": config.get("model", "claude-opus"),
                        "provider": "wibey-config"
                    }
        except Exception:
            pass

    return None


def call_claude_api(comprehensive_text, jd_text, candidate_name, company_name, api_key, model):
    """Call Claude API to generate tailored resume script. Supports Claude, OpenAI, and OpenRouter."""

    try:
        import openai
    except ImportError:
        print("❌  openai package not found. Install with: pip install openai")
        sys.exit(1)

    # Detect provider based on model format or key prefix
    is_openrouter = "/" in model or api_key.startswith("sk-or-")
    is_openai = model.startswith("gpt-") and not is_openrouter

    if is_openrouter:
        # OpenRouter API (OpenAI-compatible)
        client = openai.OpenAI(
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1"
        )
    elif is_openai:
        # OpenAI API
        client = openai.OpenAI(api_key=api_key)
    else:
        # Anthropic API (Claude)
        try:
            import anthropic
        except ImportError:
            print("❌  anthropic package not found. Install with: pip install anthropic")
            sys.exit(1)
        client = anthropic.Anthropic(api_key=api_key)
        is_openai = False

    prompt = f"""You are a resume tailoring expert. Generate a Python script that creates a tailored resume for {candidate_name} for a job at {company_name}.

## Comprehensive Resume (Source of Truth)
{comprehensive_text}

## Job Description
{jd_text}

## Your Task
Create a complete, standalone Python script that:
1. Selects the most relevant bullets from the comprehensive resume
2. Reorders by job description relevance
3. Generates a PDF and DOCX resume (exactly 2 pages)
4. Uses python-docx and reportlab libraries

The script must:
- Import necessary libraries at the top
- Define all content as Python variables (not read from files)
- Have a __main__ section that generates both PDF and DOCX
- In __main__: Add parent directories to sys.path before importing resume_validator (for validator discovery)
- Import resume_validator with try/except (it may not be installed; if missing, skip validation)
- Include validation before PDF generation (if available)
- Follow the resume tailoring rules:
  - No metrics (25+, 4,300+, counts)
  - All bullets from the comprehensive resume (verify before including)
  - For Staff/Senior roles: architecture + leadership first
  - Exactly 2 pages, 18-22 bullets maximum

Output file naming (in generate_docx and generate_pdf functions):
- PDF: f"{CANDIDATE_NAME.replace(' ', '')}_{COMPANY_NAME}.pdf"
- DOCX: f"{CANDIDATE_NAME.replace(' ', '')}_{COMPANY_NAME}.docx"
Example: ShawnHe_RockstarGames.pdf and ShawnHe_RockstarGames.docx (no "Resume", no underscores between first/last name)

**CRITICAL formatting rules:**
- Use ONLY ASCII characters in all strings (no smart/curly quotes, em dashes, etc.)
- Replace: " with ", ' with ', — with -, – with -
- All docstrings and comments use regular ASCII quotes only
- No Unicode characters anywhere in the output

Output ONLY the Python script code, wrapped in ```python ... ``` blocks. No explanation or comments outside the code block.
"""

    provider_name = "OpenRouter" if is_openrouter else ("OpenAI" if is_openai else "Anthropic")
    print(f"🤖 Calling {provider_name} ({model})...", file=sys.stderr)

    if is_openai or is_openrouter:
        # OpenAI-compatible API (including OpenRouter)
        response = client.chat.completions.create(
            model=model,
            max_tokens=4000,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        response_text = response.choices[0].message.content
    else:
        # Anthropic API (Claude)
        message = client.messages.create(
            model=model,
            max_tokens=4000,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        response_text = message.content[0].text

    # Find the Python code block
    import re
    code_match = re.search(r'```python\n(.*?)\n```', response_text, re.DOTALL)

    if not code_match:
        print("❌  Could not extract Python code from Claude response.", file=sys.stderr)
        print("Response:", response_text[:500], file=sys.stderr)
        return None

    return code_match.group(1)


def main():
    parser = argparse.ArgumentParser(description="Generate tailored resume Python script")
    parser.add_argument("--comprehensive", required=True, help="Path to comprehensive resume")
    parser.add_argument("--jd", required=True, help="Path to job description")
    parser.add_argument("--candidate", required=True, help="Candidate name")
    parser.add_argument("--company", required=True, help="Company name")
    parser.add_argument("--output", required=True, help="Output script path")
    parser.add_argument("--api-key", help="Claude API key (optional, auto-detect if not provided)")
    parser.add_argument("--model", default="claude-opus", help="Model to use (default: claude-opus)")

    args = parser.parse_args()

    # Check input files
    if not os.path.isfile(args.comprehensive):
        print(f"❌  Comprehensive resume not found: {args.comprehensive}", file=sys.stderr)
        sys.exit(1)

    if not os.path.isfile(args.jd):
        print(f"❌  Job description not found: {args.jd}", file=sys.stderr)
        sys.exit(1)

    # Read input files
    with open(args.comprehensive) as f:
        comprehensive_text = f.read()

    with open(args.jd) as f:
        jd_text = f.read()

    # Get API key
    api_key = args.api_key
    if not api_key:
        wibey_context = detect_wibey_context()
        if wibey_context:
            api_key = wibey_context["api_key"]
            print(f"ℹ️  Using Wibey context ({wibey_context['provider']})", file=sys.stderr)
        else:
            print("❌  No API key provided and Wibey context not detected.", file=sys.stderr)
            print("    Provide --api-key or set WIBEY_API_KEY environment variable.", file=sys.stderr)
            sys.exit(1)

    # Generate script
    script_code = call_claude_api(
        comprehensive_text, jd_text, args.candidate, args.company,
        api_key, args.model
    )

    if not script_code:
        print("❌  Failed to generate script.", file=sys.stderr)
        sys.exit(1)

    # Save script
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        f.write(script_code)

    output_path.chmod(0o755)

    print(f"✅ Script generated: {output_path}", file=sys.stderr)
    sys.exit(0)


if __name__ == "__main__":
    main()
