# Contributing to YT2Audi

First off, thank you for considering contributing to YT2Audi! It's people like you that make YT2Audi such a great tool.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [How Can I Contribute?](#how-can-i-contribute)
- [Style Guidelines](#style-guidelines)
- [Testing](#testing)
- [Pull Request Process](#pull-request-process)

## Code of Conduct

This project and everyone participating in it is governed by the principle of respect and professionalism. By participating, you are expected to uphold this code.

## Getting Started

### Prerequisites

- Python 3.11 or higher
- FFmpeg installed and in PATH
- Git

### Development Setup

1. **Fork and Clone**
   ```bash
   git clone https://github.com/YOUR_USERNAME/yt2audi.git
   cd yt2audi
   ```

2. **Install Dependencies**
   ```bash
   # Install in editable mode with dev dependencies
   pip install -r requirements.txt
   pip install -e .
   
   # Install development tools (optional but recommended)
   pip install pytest pytest-cov mypy ruff black
   ```

3. **Verify Installation**
   ```bash
   # Run manual foundation tests
   python tests/manual/test_foundation.py
   
   # List profiles to verify
   python -m yt2audi profiles
   ```

4. **Create a Branch**
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/your-bug-fix
   ```

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check the existing issues to avoid duplicates. When you create a bug report, include as many details as possible:

- **Use a clear and descriptive title**
- **Describe the exact steps to reproduce the problem**
- **Provide specific examples**
- **Describe the behavior you observed and what you expected**
- **Include Python version, OS, and FFmpeg version**
- **Include any error messages or stack traces**

**Bug Report Template:**
```markdown
**Description:**
A clear description of what the bug is.

**Steps to Reproduce:**
1. Go to '...'
2. Run command '....'
3. See error

**Expected Behavior:**
What you expected to happen.

**Actual Behavior:**
What actually happened.

**Environment:**
- OS: [e.g., Windows 11, Ubuntu 22.04]
- Python Version: [e.g., 3.11.5]
- FFmpeg Version: [e.g., 6.0]
- YT2Audi Version: [e.g., 2.0.0]

**Additional Context:**
Any other relevant information.
```

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion:

- **Use a clear and descriptive title**
- **Provide a detailed description of the suggested enhancement**
- **Explain why this enhancement would be useful**
- **List any alternative solutions you've considered**

### Your First Code Contribution

Unsure where to begin? Look for issues tagged with:
- `good-first-issue` - Simple issues for newcomers
- `help-wanted` - Issues where help is needed
- `bug` - Bug fixes are always welcome

### Pull Requests

1. **Follow the style guidelines** (see below)
2. **Write or update tests** for your changes
3. **Update documentation** if needed
4. **Ensure all tests pass**
5. **Write clear commit messages**

## Style Guidelines

### Python Code Style

We follow **PEP 8** with some modifications:

- **Line length:** 100 characters (not 79)
- **Use type hints** for all function signatures
- **Docstrings:** Google style for all public functions/classes
- **Imports:** Organized with `isort`
- **Formatting:** Automated with `black`
- **Linting:** Enforced with `ruff`

### Code Formatting Tools

Before submitting, run:

```bash
# Auto-format code
black src/yt2audi tests/

# Check and fix linting issues
ruff check src/yt2audi --fix

# Type checking
mypy src/yt2audi --strict
```

### Docstring Format

Use Google-style docstrings:

```python
def download_video(url: str, output_dir: Path) -> Path:
    """Download a single video from YouTube.

    Args:
        url: YouTube video URL
        output_dir: Directory to save the downloaded video

    Returns:
        Path to the downloaded video file

    Raises:
        DownloadError: If download fails
        ValueError: If URL is invalid

    Example:
        >>> video_path = download_video("https://youtube.com/...", Path("./output"))
        >>> print(video_path)
        PosixPath('/path/to/output/video.mp4')
    """
    # Implementation here
```

### Commit Messages

Follow **Conventional Commits** format:

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

**Examples:**
```bash
feat(downloader): add support for 8K video downloads

fix(splitter): resolve file size calculation bug
Closes #123

docs(readme): update installation instructions

test(converter): add GPU detection test cases
```

## Testing

### Running Tests

```bash
# Run all unit tests
pytest tests/unit/ -v

# Run with coverage
pytest tests/ --cov=yt2audi --cov-report=html

# Run manual/integration tests
python tests/manual/test_foundation.py

# Type checking
mypy src/yt2audi --strict
```

### Writing Tests

- **Unit tests** go in `tests/unit/`
- **Integration tests** go in `tests/integration/`
- **Manual tests** go in `tests/manual/`
- **Test fixtures** go in `tests/fixtures/`

Test naming convention:
```python
def test_<function_name>_<scenario>_<expected_result>():
    """Test that function_name does X when Y."""
    # Arrange
    # Act
    # Assert
```

### Test Coverage Requirements

- **Minimum coverage:** 80% for new code
- **Critical paths:** 100% coverage required
  - Security functions (`sanitize_path`, etc.)
  - Core download/convert logic
  - Profile validation

## Pull Request Process

1. **Update CHANGELOG.md** under "Unreleased" section
2. **Ensure all tests pass** and coverage meets requirements
3. **Update documentation** if you changed APIs
4. **Verify code style** with `black`, `ruff`, and `mypy`
5. **Create PR** with a clear title and description
6. **Link related issues** using "Fixes #123" or "Closes #456"
7. **Wait for review** - be patient and responsive to feedback

### PR Template

Your PR description should include:

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update

## Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing completed
- [ ] Coverage meets requirements (≥80%)

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Comments added to complex code
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] No new warnings generated
```

## Security Issues

**Do NOT** create public issues for security vulnerabilities. Instead, email the maintainers directly at [security email - to be added].

Include:
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

## Questions?

Feel free to:
- Open a discussion on GitHub
- Check existing issues
- Read the documentation in `/docs/`

## License

By contributing, you agree that your contributions will be licensed under theMIT License.

---

Thank you for contributing to YT2Audi! 🎉
