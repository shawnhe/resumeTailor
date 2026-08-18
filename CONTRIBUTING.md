# Contributing to ResumeTailor

Thanks for your interest in improving ResumeTailor! This guide explains how to contribute.

---

## Getting Started

1. **Fork & Clone**
   ```bash
   git clone <your-fork>
   cd resumeTailor
   ```

2. **Install Dependencies**
   ```bash
   pip install pdfplumber python-docx requests anthropic openai
   ```

3. **Test Locally**
   ```bash
   ./bin/tailor_resume_generic.sh --help
   python3 bin/convert_resume_to_md.py --help
   python3 bin/generate_with_agent.py --help
   ```

---

## Types of Contributions

### 1. Bug Reports & Issues

Found a bug? Open an issue with:
- **Title**: Clear, specific (e.g., "convert_resume_to_md.py fails on DOCX with images")
- **Description**: Steps to reproduce, expected behavior, actual behavior
- **Environment**: Python version, OS, tool version
- **Error**: Full error message or traceback

### 2. Improvements to Existing Scripts

Help improve:
- **`tailor_resume_generic.sh`**: Better JD fetching, company name detection, error handling
- **`convert_resume_to_md.py`**: Better PDF/DOCX parsing, format detection
- **`generate_with_agent.py`**: New agent types, better error messages

Steps:
1. Identify the issue or improvement
2. Make changes in your fork
3. Test thoroughly
4. Submit PR with clear description of what changed and why

### 3. New Agent Support

Want to add support for Claude Opus, Mistral, or another model?

1. **Add function to `generate_with_agent.py`**:
   ```python
   def call_your_agent(api_key: str, model: str, prompt: str, output_file: str) -> bool:
       """Call YourAgent API"""
       # Implementation here
       return success
   ```

2. **Update argparse choices**:
   ```python
   parser.add_argument("--agent", choices=["wibey", "openai", "claude", "openrouter", "your_agent"])
   ```

3. **Add handler in main()**:
   ```python
   elif args.agent == "your_agent":
       success = call_your_agent(args.api_key, args.model, prompt, output_file)
   ```

4. **Update docs** (MULTI_AGENT_GUIDE.md)
5. **Submit PR** with tests

### 4. Documentation Improvements

Help clarify or expand:
- **README.md**: Clearer quick start, better examples
- **docs/USAGE_GUIDE.md**: More workflows, troubleshooting
- **docs/AGENT_SETUP.md**: Better setup instructions for each agent
- **docs/MULTI_AGENT_GUIDE.md**: Agent comparisons, cost analysis
- **docs/CONVERT_GUIDE.md**: Better conversion tips

Just edit the markdown and submit a PR.

### 5. Custom Validators

Create a validator for your specific resume rules?

1. **Create `my_validator.py`**:
   ```python
   def validate_resume_bullets(script_path: str):
       """Validate resume bullets against custom rules"""
       # Read script, check bullets
       # Raise ValueError if rule violated
       pass
   ```

2. **Document in a new guide**: `docs/CUSTOM_VALIDATORS.md`

3. **Share with team or submit PR**

### 6. Interview Prep Templates

Improve or extend the interview prep template?

1. Edit `docs/CONVERT_GUIDE.md` or create `templates/interview-prep-{company}.md`
2. Include: company research, technical focus areas, interview tips
3. Submit PR with clear structure

---

## Development Guidelines

### Code Style

- **Python**: Follow PEP 8 (use `black` for formatting)
- **Bash**: Use `shellcheck` for linting
- **Markdown**: Consistent formatting, clear headings

### Testing

Before submitting:
1. Test the script with sample data
2. Test with different agents/options
3. Verify error handling
4. Check documentation accuracy

### Commit Messages

Format:
```
[type] Brief description

Longer explanation if needed.
- Bullet point details
- Why this change matters
```

Types: `fix:`, `feat:`, `docs:`, `refactor:`, `test:`, `chore:`

Example:
```
feat: Add Mistral agent support to generate_with_agent.py

- Implement call_mistral() function
- Add Mistral to agent choices
- Update MULTI_AGENT_GUIDE.md with setup and pricing
```

### Pull Request Template

```markdown
## Summary
Brief description of changes

## Why
Why this change is needed

## What Changed
- Change 1
- Change 2

## Testing
How to test this change

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-reviewed my own changes
- [ ] Updated relevant documentation
- [ ] Tested locally
```

---

## Review Process

1. **Submit PR** with clear title and description
2. **Wait for review** (maintainers will comment)
3. **Address feedback** if any
4. **PR merged** once approved

---

## Common Scenarios

### Adding a New Agent Type

1. Implement `call_your_agent()` in `generate_with_agent.py`
2. Update argparse
3. Add to main() switch
4. Add setup section to `docs/AGENT_SETUP.md`
5. Add row to comparison table in `docs/MULTI_AGENT_GUIDE.md`
6. Test with sample resume + JD

### Improving Markdown Conversion

1. Test `convert_resume_to_md.py` with various PDF/DOCX formats
2. Identify parsing issues
3. Improve regex or parsing logic
4. Update `docs/CONVERT_GUIDE.md` with new tips
5. Submit PR with test cases

### Extending Interview Prep Template

1. Add new sections to the markdown template
2. Include guidance for each section
3. Document in `docs/CONVERT_GUIDE.md`
4. Submit PR

---

## Questions?

- **Issue with the tool?** Open an issue
- **Want to collaborate?** Start a discussion
- **Ideas for improvement?** Open an issue with `[enhancement]` label

---

## License

By contributing, you agree that your contributions will be licensed under the same license as this project (see LICENSE file).

---

## Code of Conduct

- Be respectful
- Assume good intent
- Welcome diverse perspectives
- Help each other learn

---

## Resources

- **Python**: https://pep8.org/
- **Bash**: https://www.shellcheck.net/
- **Git**: https://git-scm.com/doc
- **Markdown**: https://www.markdownguide.org/

---

**Thank you for contributing! 🙏**
