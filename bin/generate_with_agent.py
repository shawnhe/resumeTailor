#!/usr/bin/env python3
"""
generate_with_agent.py — Multi-agent wrapper for resume tailoring

Supports: Wibey, OpenAI, Claude API, OpenRouter, Manual (copy-paste)

Usage:
  python3 generate_with_agent.py \
    --agent wibey \
    --jd companies/Acme/Acme_jd.md \
    --resume ~/my-resume.md \
    --company Acme

  python3 generate_with_agent.py \
    --agent openai \
    --api-key sk-xxxx \
    --model gpt-4 \
    --jd companies/Acme/Acme_jd.md \
    --resume ~/my-resume.md \
    --company Acme

  python3 generate_with_agent.py \
    --agent claude \
    --api-key sk-ant-xxxx \
    --jd companies/Acme/Acme_jd.md \
    --resume ~/my-resume.md \
    --company Acme

  python3 generate_with_agent.py \
    --agent openrouter \
    --api-key sk-or-xxxx \
    --model claude-3.5-sonnet \
    --jd companies/Acme/Acme_jd.md \
    --resume ~/my-resume.md \
    --company Acme

  python3 generate_with_agent.py \
    --agent manual \
    --jd companies/Acme/Acme_jd.md \
    --resume ~/my-resume.md \
    --company Acme
"""

import sys
import os
import subprocess
import argparse
from pathlib import Path
from typing import Optional, Dict

# Get script directory for relative paths
SCRIPT_DIR = Path(__file__).parent.parent
AGENTS_DIR = SCRIPT_DIR / "agents"
AGENT_INSTRUCTIONS_FILE = AGENTS_DIR / "resume-tailor-generic.md"


def read_file(filepath: str) -> str:
    """Read a file safely."""
    try:
        with open(filepath, "r") as f:
            return f.read()
    except FileNotFoundError:
        print(f"❌  File not found: {filepath}")
        sys.exit(1)
    except Exception as e:
        print(f"❌  Error reading {filepath}: {e}")
        sys.exit(1)


def read_agent_instructions() -> str:
    """Read agent instructions from resume-tailor-generic.md."""
    if not AGENT_INSTRUCTIONS_FILE.exists():
        print(f"❌  Agent instructions not found: {AGENT_INSTRUCTIONS_FILE}")
        sys.exit(1)
    return read_file(str(AGENT_INSTRUCTIONS_FILE))


def extract_python_code(response: str) -> str:
    """Extract Python code from agent response."""
    # Look for ```python blocks
    import re
    matches = re.findall(r"```python\n(.*?)\n```", response, re.DOTALL)
    if matches:
        return matches[0]

    # Fallback: look for any triple-backtick block
    matches = re.findall(r"```\n(.*?)\n```", response, re.DOTALL)
    if matches:
        return matches[0]

    # Last resort: assume entire response is code
    return response


def call_wibey(prompt: str, output_file: str) -> bool:
    """Call Wibey CLI with prompt."""
    print("📞  Calling Wibey agent...")
    try:
        result = subprocess.run(
            ["wibey", "-p", prompt, "--response-style", "verbose"],
            capture_output=True,
            text=True,
            timeout=300
        )

        if result.returncode != 0:
            print(f"❌  Wibey failed: {result.stderr}")
            return False

        # Extract Python code from response
        code = extract_python_code(result.stdout)

        with open(output_file, "w") as f:
            f.write(code)

        print(f"✔   Generated: {output_file}")
        return True

    except FileNotFoundError:
        print("❌  Wibey not found. Install with: pip install wibey")
        return False
    except Exception as e:
        print(f"❌  Error calling Wibey: {e}")
        return False


def call_openai(api_key: str, model: str, prompt: str, output_file: str) -> bool:
    """Call OpenAI API to generate script."""
    print(f"📞  Calling OpenAI ({model})...")

    try:
        import openai
    except ImportError:
        print("❌  openai package not installed. Install with: pip install openai")
        return False

    try:
        openai.api_key = api_key
        client = openai.OpenAI(api_key=api_key)

        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=4000
        )

        code = extract_python_code(response.choices[0].message.content)

        with open(output_file, "w") as f:
            f.write(code)

        print(f"✔   Generated: {output_file}")
        return True

    except Exception as e:
        print(f"❌  OpenAI API error: {e}")
        return False


def call_claude_api(api_key: str, prompt: str, output_file: str) -> bool:
    """Call Claude API (Anthropic) to generate script."""
    print("📞  Calling Claude API...")

    try:
        import anthropic
    except ImportError:
        print("❌  anthropic package not installed. Install with: pip install anthropic")
        return False

    try:
        client = anthropic.Anthropic(api_key=api_key)

        message = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=4096,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        code = extract_python_code(message.content[0].text)

        with open(output_file, "w") as f:
            f.write(code)

        print(f"✔   Generated: {output_file}")
        return True

    except Exception as e:
        print(f"❌  Claude API error: {e}")
        return False


def call_openrouter(api_key: str, model: str, prompt: str, output_file: str) -> bool:
    """Call OpenRouter API to generate script."""
    print(f"📞  Calling OpenRouter ({model})...")

    try:
        import requests
    except ImportError:
        print("❌  requests package not installed. Install with: pip install requests")
        return False

    try:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "HTTP-Referer": "https://github.com/resumeTailor",
            "X-Title": "resumeTailor",
            "Content-Type": "application/json"
        }

        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json={
                "model": model,
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7,
                "max_tokens": 4000
            },
            timeout=300
        )

        if response.status_code != 200:
            print(f"❌  OpenRouter API error: {response.status_code}")
            print(f"    {response.text}")
            return False

        data = response.json()
        if "choices" not in data or len(data["choices"]) == 0:
            print(f"❌  Invalid OpenRouter response: {data}")
            return False

        code = extract_python_code(data["choices"][0]["message"]["content"])

        with open(output_file, "w") as f:
            f.write(code)

        print(f"✔   Generated: {output_file}")
        return True

    except Exception as e:
        print(f"❌  OpenRouter API error: {e}")
        return False


def manual_copy_paste(prompt: str, output_file: str) -> bool:
    """Guide user through manual copy-paste workflow."""
    print("\n" + "=" * 70)
    print("MANUAL COPY-PASTE WORKFLOW")
    print("=" * 70)
    print("\n1. Copy the prompt below:")
    print("-" * 70)
    print(prompt)
    print("-" * 70)
    print("\n2. Go to Claude Code or your preferred AI tool")
    print("3. Paste the prompt")
    print("4. Copy the Python code from the response")
    print(f"5. Save to: {output_file}")
    print("\n6. Or run:")
    print(f"   pbpaste > {output_file}  # macOS")
    print(f"   xclip -o > {output_file}  # Linux")
    print("=" * 70)

    response = input("\nPaste the generated Python code and press Ctrl+D when done:\n")

    try:
        with open(output_file, "w") as f:
            f.write(response)
        print(f"✔   Saved: {output_file}")
        return True
    except Exception as e:
        print(f"❌  Error saving: {e}")
        return False


def build_prompt(
    jd_content: str,
    resume_content: str,
    company_name: str,
    candidate_name: str
) -> str:
    """Build the prompt for the agent."""
    instructions = read_agent_instructions()

    prompt = f"""You are a resume tailoring specialist. Generate a Python script for resume tailoring.

INSTRUCTIONS:
{instructions}

---

JOB DESCRIPTION:
{jd_content}

---

CANDIDATE RESUME:
{resume_content}

---

TASK:
Generate a complete, standalone Python script named `generate_resume_{company_name.lower()}.py` that:
1. Creates a tailored resume for {company_name}
2. Candidate name: {candidate_name}
3. Selects bullets from the resume based on JD relevance
4. Outputs both PDF and DOCX files
5. Keeps to exactly 2 pages (hard constraint)

The script should be ready to run immediately without modification.

OUTPUT ONLY the Python code in ```python``` blocks. No explanations.
"""

    return prompt


def main():
    parser = argparse.ArgumentParser(
        description="Multi-agent wrapper for resume tailoring"
    )
    parser.add_argument(
        "--agent",
        required=True,
        choices=["wibey", "openai", "claude", "openrouter", "manual"],
        help="Which agent to use"
    )
    parser.add_argument("--jd", required=True, help="Path to job description")
    parser.add_argument("--resume", required=True, help="Path to resume")
    parser.add_argument("--company", required=True, help="Company name")
    parser.add_argument("--candidate-name", help="Candidate name (optional, inferred from prompt)")
    parser.add_argument("--output-dir", help="Output directory (optional)")

    # OpenAI options
    parser.add_argument("--api-key", help="API key for OpenAI or Claude")
    parser.add_argument("--model", default="gpt-4", help="OpenAI model (default: gpt-4)")

    # Wibey options
    parser.add_argument("--wibey-cmd", default="wibey", help="Wibey command path")

    args = parser.parse_args()

    # Expand home directory
    jd_path = os.path.expanduser(args.jd)
    resume_path = os.path.expanduser(args.resume)

    # Read files
    print(f"📄  Reading JD: {jd_path}")
    jd_content = read_file(jd_path)

    print(f"📄  Reading resume: {resume_path}")
    resume_content = read_file(resume_path)

    # Determine output file
    company_lower = args.company.lower().replace(" ", "_")
    output_dir = args.output_dir or str(Path(jd_path).parent)
    output_file = os.path.join(output_dir, f"generate_resume_{company_lower}.py")

    # Build prompt
    candidate_name = args.candidate_name or "Candidate"
    print(f"\n🔨  Building prompt for {args.company}...")
    prompt = build_prompt(jd_content, resume_content, args.company, candidate_name)

    # Call appropriate agent
    print(f"\n🤖  Using agent: {args.agent.upper()}")
    success = False

    if args.agent == "wibey":
        success = call_wibey(prompt, output_file)

    elif args.agent == "openai":
        if not args.api_key:
            print("❌  --api-key required for OpenAI agent")
            sys.exit(1)
        success = call_openai(args.api_key, args.model, prompt, output_file)

    elif args.agent == "claude":
        if not args.api_key:
            print("❌  --api-key required for Claude agent")
            sys.exit(1)
        success = call_claude_api(args.api_key, prompt, output_file)

    elif args.agent == "openrouter":
        if not args.api_key:
            print("❌  --api-key required for OpenRouter agent")
            sys.exit(1)
        success = call_openrouter(args.api_key, args.model, prompt, output_file)

    elif args.agent == "manual":
        success = manual_copy_paste(prompt, output_file)

    if not success:
        print("\n❌  Generation failed.")
        sys.exit(1)

    # Verify output
    if not os.path.isfile(output_file):
        print(f"❌  Output file not created: {output_file}")
        sys.exit(1)

    file_size = os.path.getsize(output_file)
    if file_size < 100:
        print(f"⚠️   Warning: Generated file is very small ({file_size} bytes)")

    print(f"\n✅  Success! Generated script ready at:")
    print(f"   {output_file}")
    print(f"\n📋  Next steps:")
    print(f"   1. Review the script: cat {output_file}")
    print(f"   2. Run the script: python3 {output_file}")
    print(f"   3. Check outputs in: {output_dir}")


if __name__ == "__main__":
    main()
