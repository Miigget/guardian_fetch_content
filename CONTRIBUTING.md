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

### Code Review Process

All contributions go through code review:

1. **Automated Checks**: GitHub Actions run quality checks
2. **Peer Review**: At least one maintainer reviews the code
3. **Testing**: Changes are tested in different environments
4. **Documentation**: Documentation updates are reviewed

## 🧪 Testing Guidelines

### Test Organization

- **Unit Tests**: Test individual components in isolation
- **Integration Tests**: Test component interactions
- **Mock Tests**: Use mocks for external dependencies
- **Edge Cases**: Test error conditions and edge cases

### Test Structure

```python
class TestClassName:
    """Test cases for ClassName."""
    
    def test_method_success_case(self):
        """Test successful operation of method."""
        # Arrange
        input_data = "test_input"
        expected_result = "expected_output"
        
        # Act
        result = class_instance.method(input_data)
        
        # Assert
        assert result == expected_result
    
    def test_method_error_case(self):
        """Test error handling in method."""
        with pytest.raises(ExpectedError, match="error message"):
            class_instance.method(invalid_input)
```

### Test Coverage

- Aim for 90%+ code coverage
- Test both success and failure paths
- Include edge cases and boundary conditions
- Mock external dependencies (APIs, AWS services)

## 📚 Documentation

### Documentation Requirements

- **README**: Keep the main README up to date
- **API Documentation**: Document all public APIs
- **Code Comments**: Explain complex logic
- **Examples**: Provide usage examples
- **Changelog**: Update CHANGELOG.md for significant changes

### Documentation Style

- Use clear, concise language
- Include code examples
- Provide context and rationale
- Link to related documentation

## 🏗 Architecture Guidelines

### Design Principles

- **Single Responsibility**: Each class/function has one clear purpose
- **Dependency Injection**: Use dependency injection for testability
- **Error Handling**: Graceful error handling with meaningful messages
- **Logging**: Comprehensive logging for debugging and monitoring
- **Configuration**: Externalize configuration via environment variables

### Code Organization

```
src/guardian_content_fetcher/
├── __init__.py          # Package exports
├── api_client.py        # Guardian API client
├── message_broker.py    # Message broker implementations
├── content_fetcher.py   # Main orchestrator
├── config.py           # Configuration management
└── cli.py              # Command-line interface
```

### Adding New Features

When adding new features:

1. **Design**: Consider the impact on existing code
2. **Interface**: Define clear, consistent APIs
3. **Testing**: Write tests before implementation (TDD)
4. **Documentation**: Document the feature thoroughly
5. **Backward Compatibility**: Maintain compatibility when possible

## 🔒 Security Considerations

### Security Guidelines

- **No Secrets in Code**: Never commit API keys or credentials
- **Input Validation**: Validate all external inputs
- **Error Messages**: Don't expose sensitive information in errors
- **Dependencies**: Keep dependencies updated and scan for vulnerabilities

### Security Review

Security-sensitive changes require additional review:

- Credential handling
- Network communications
- Data processing
- Error handling

## 🤝 Community Guidelines

### Code of Conduct

- Be respectful and inclusive
- Focus on constructive feedback
- Help others learn and improve
- Acknowledge contributions

### Communication

- **Issues**: Use GitHub issues for bug reports and feature requests
- **Discussions**: Use GitHub discussions for questions and ideas
- **Email**: Contact maintainers directly for security issues

## 📦 Release Process

### Version Numbering

We use Semantic Versioning (SemVer):
- `MAJOR.MINOR.PATCH`
- `MAJOR`: Breaking changes
- `MINOR`: New features (backward compatible)
- `PATCH`: Bug fixes (backward compatible)

### Release Checklist

1. Update version numbers
2. Update CHANGELOG.md
3. Run full test suite
4. Create release tag
5. Publish to PyPI (if applicable)
6. Update documentation

## 🙏 Recognition

Contributors are recognized in:
- CHANGELOG.md for significant contributions
- README.md contributors section
- GitHub contributors page

Thank you for contributing to Guardian Content Fetcher! 🎉
