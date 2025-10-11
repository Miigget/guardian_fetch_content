# Code Style Configuration

## Summary

This project uses **Black** as the primary code formatter and **Flake8** as the linter, both configured to use **88 characters** as the maximum line length.

## Current Configuration

### Black (Formatter)
- **Line length**: 88 characters
- **Python versions**: 3.8, 3.9, 3.10, 3.11
- **Configuration file**: `pyproject.toml`

### Flake8 (Linter)
- **Line length**: 88 characters
- **Ignored errors**: E203, E266, W503, W293 (Black-compatible)
- **Per-file ignores**: F401 in `__init__.py`, C901 in `cli.py`
- **Configuration file**: `.flake8`

**Ignored Error Codes Explained:**
- `E203`: Whitespace before ':' (conflicts with Black)
- `E266`: Too many leading '#' for block comment
- `W503`: Line break before binary operator (conflicts with Black)
- `W293`: Blank line contains whitespace (common in multiline strings)
- `C901`: Function too complex (allowed in CLI interactive mode)
- `F401`: Unused imports (allowed in `__init__.py` for re-exports)

## Why 88 Characters Instead of 79?

### Advantages of 88 Characters:
1. **Widely accepted standard** - Black's default, used by:
   - Django
   - pytest
   - FastAPI
   - Requests
   - Flask

2. **~10% more space** - fewer broken lines, better readability

3. **Modern development environment** - today's monitors and editors are wider than 80-column terminals from the 1980s

4. **Compatibility** - still fits in editors with side panels open

### PEP-8 and 88 Characters:
- PEP-8 recommends 79 characters but is flexible
- PEP-8 itself states: "some teams strongly prefer a longer line length"
- 88 characters is a reasonable compromise between 79 and 99

## Using the Formatter

### Check code style
```bash
# Check if code is properly formatted
black --check src/ tests/

# Check with Flake8
flake8 src/ tests/
```

### Automatic formatting
```bash
# Format entire project
black src/ tests/

# Format specific file
black src/guardian_content_fetcher/api_client.py
```

### Run all quality checks
```bash
# All code quality tests
python scripts/run_tests.py

# Linting only
python scripts/run_tests.py --lint-only
```

## Switching to 79 Characters (Strict PEP-8)

If a code reviewer requires strict adherence to 79 characters from PEP-8:

### Step 1: Update `.flake8`
```ini
[flake8]
max-line-length = 79
# ... rest of configuration
```

### Step 2: Update `pyproject.toml`
```toml
[tool.black]
line-length = 79
# ... rest of configuration
```

### Step 3: Reformat code
```bash
black src/ tests/
```

### Step 4: Verify
```bash
flake8 src/ tests/
black --check src/ tests/
```

## IDE Integration

### VS Code
Add to `.vscode/settings.json`:
```json
{
  "python.formatting.provider": "black",
  "python.formatting.blackArgs": ["--line-length", "88"],
  "python.linting.flake8Enabled": true,
  "python.linting.enabled": true,
  "editor.formatOnSave": true,
  "editor.rulers": [88]
}
```

### PyCharm
1. Settings → Tools → Black
2. Check "On code reformat"
3. Settings → Editor → Code Style → Python → Set line length to 88

## Line Length Verification

### Check for lines longer than configured limit
```bash
# Check for lines longer than 88 characters
flake8 src/ tests/ --max-line-length=88 --statistics

# For 79 characters:
flake8 src/ tests/ --max-line-length=79 --statistics
```

### Current Project Status
- ✅ Black: all files compliant with 88 characters
- ✅ Flake8: configured for 88 characters
- ✅ No lines longer than 88 characters
- ✅ PEP-8 compliant (except line length)
- ✅ Unit tests: 90%+ coverage
- ✅ Security: Bandit scan clean

## References

- [PEP-8 Style Guide](https://peps.python.org/pep-0008/)
- [Black Documentation](https://black.readthedocs.io/)
- [Black's Line Length Philosophy](https://black.readthedocs.io/en/stable/the_black_code_style/current_style.html#line-length)
- [Flake8 Documentation](https://flake8.pycqa.org/)

## FAQ

**Q: Is 88 characters a violation of PEP-8?**  
A: Not in practical terms. PEP-8 says "limit all lines to a maximum of 79 characters", but also: "some teams strongly prefer a longer line length". 88 characters is widely accepted in the Python community.

**Q: Will this affect AWS Lambda compatibility?**  
A: No, line length does not affect package size or Lambda compatibility.

**Q: Are other tools compatible with 88 characters?**  
A: Yes, all popular tools (PyCharm, VS Code, pylint) support configurable line length.

**Q: Do I need to change to 79 characters?**  
A: Only if a code reviewer/examiner explicitly requires it. 88 characters is the standard in modern Python projects.

## Additional Notes

### Black Philosophy
Black is an "opinionated formatter" that deliberately makes choices to reduce bikeshedding. The 88-character limit is one of these choices, balancing readability with practicality.

### Project Consistency
All tooling in this project (Black, Flake8, editor configurations) is consistently set to 88 characters to avoid conflicts and confusion.
