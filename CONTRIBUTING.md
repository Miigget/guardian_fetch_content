# Contributing to Guardian Content Fetcher

We welcome contributions to the Guardian Content Fetcher project! This document provides guidelines for contributing code, reporting issues, and suggesting improvements.

## 🚀 Getting Started

### Prerequisites

- Python 3.8 or higher
- Git
- Guardian API key (for testing)
- AWS account (for Kinesis testing, optional)

### Development Setup

```bash
# Fork and clone the repository
git clone https://github.com/your-username/guardian_fetch_content.git
cd guardian_fetch_content

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies
pip install -r requirements.txt
pip install -e .

# Install development dependencies
pip install pytest pytest-cov black flake8 mypy bandit safety sphinx

# Set up environment variables
cp env_template.txt .env
# Edit .env with your test credentials
```

### Running Tests

```bash
# Run all quality checks
python run_tests.py

# Run specific checks
python run_tests.py --tests-only      # Unit tests only
python run_tests.py --lint-only       # Code style checks
python run_tests.py --security-only   # Security scans
python run_tests.py --verbose         # Verbose output
```

## 📝 Code Standards

### Style Guidelines

We follow strict code quality standards:

- **PEP-8 Compliance**: All code must follow PEP-8 style guidelines
- **Black Formatting**: Code is automatically formatted with Black
- **Type Hints**: All functions must include type hints
- **Docstrings**: All modules, classes, and functions must have comprehensive docstrings
- **Comments**: Complex logic should include explanatory comments

### Code Quality Requirements

- **Test Coverage**: Minimum 90% test coverage required
- **Static Type Checking**: Code must pass MyPy type checking
- **Security**: Code must pass Bandit security scanning
- **Dependencies**: All dependencies must pass Safety vulnerability checks

### Docstring Format

Use Google-style docstrings:

```python
def example_function(param1: str, param2: int = 10) -> bool:
    """
    Brief description of the function.
    
    Longer description explaining the purpose, behavior, and any important
    details about the function.
    
    Args:
        param1 (str): Description of the first parameter
        param2 (int): Description of the second parameter (default: 10)
        
    Returns:
        bool: Description of the return value
        
    Raises:
        ValueError: Description of when this exception is raised
        
    Example:
        >>> result = example_function("test", 5)
        >>> print(result)
        True
    """
    pass
```

## 🐛 Reporting Issues

### Bug Reports

When reporting bugs, please include:

1. **Environment Information**:
   - Python version
   - Operating system
   - Package version

2. **Reproduction Steps**:
   - Clear steps to reproduce the bug
   - Expected vs actual behavior
   - Error messages and stack traces

3. **Test Case** (if possible):
   - Minimal code example that reproduces the issue

### Feature Requests

For feature requests, please provide:

1. **Use Case**: Describe the problem you're trying to solve
2. **Proposed Solution**: Your suggested approach
3. **Alternatives**: Other solutions you've considered
4. **Impact**: Who would benefit from this feature

## 🔄 Development Workflow

### Branching Strategy

- `main`: Stable release branch
- `develop`: Integration branch for new features
- `feature/description`: Feature development branches
- `bugfix/description`: Bug fix branches
- `hotfix/description`: Critical fixes for production

### Pull Request Process

1. **Create a Feature Branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make Your Changes**:
   - Write code following our standards
   - Add comprehensive tests
   - Update documentation as needed

3. **Run Quality Checks**:
   ```bash
   python run_tests.py
   ```

4. **Commit Your Changes**:
   ```bash
   git add .
   git commit -m "feat: add new feature description"
   ```
   
   Use conventional commit messages:
   - `feat:` for new features
   - `fix:` for bug fixes
   - `docs:` for documentation changes
   - `test:` for test additions/modifications
   - `refactor:` for code refactoring
   - `style:` for formatting changes

5. **Push and Create PR**:
   ```bash
   git push origin feature/your-feature-name
   ```
   
   Create a pull request with:
   - Clear title and description
   - Reference to related issues
   - Testing instructions
   - Screenshots (if applicable)

All contributions go through code
