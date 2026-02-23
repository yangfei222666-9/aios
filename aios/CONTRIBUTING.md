# Contributing to AIOS

Thank you for your interest in contributing to AIOS! This document provides guidelines for contributing.

## Code of Conduct

Be respectful, constructive, and professional. We're building something useful together.

## How to Contribute

### Reporting Bugs

1. Check if the bug is already reported in [Issues](https://github.com/yangfei222666-9/aios/issues)
2. If not, create a new issue with:
   - Clear title and description
   - Steps to reproduce
   - Expected vs actual behavior
   - Environment (OS, Python version, AIOS version)
   - Relevant logs or screenshots

### Suggesting Features

1. Check [Issues](https://github.com/yangfei222666-9/aios/issues) for existing suggestions
2. Create a new issue with:
   - Clear use case
   - Why it's useful
   - Proposed implementation (optional)

### Pull Requests

1. Fork the repo
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Make your changes
4. Add tests if applicable
5. Update documentation
6. Commit with clear messages: `git commit -m "Add feature: your feature"`
7. Push to your fork: `git push origin feature/your-feature`
8. Open a pull request

## Development Setup

```bash
# Clone the repo
git clone https://github.com/yangfei222666-9/aios.git
cd aios

# Install in editable mode with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/

# Check code style
black --check .
flake8 .
```

## Code Style

- Follow PEP 8
- Use `black` for formatting
- Use type hints where possible
- Write docstrings for public APIs
- Keep functions small and focused

## Testing

- Write tests for new features
- Ensure existing tests pass
- Aim for >80% coverage
- Test on Windows, macOS, and Linux if possible

## Documentation

- Update README.md if adding user-facing features
- Update CHANGELOG.md following [Keep a Changelog](https://keepachangelog.com/)
- Add docstrings to new functions/classes
- Update API docs if changing public APIs

## Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

- `feat: add new feature`
- `fix: fix bug`
- `docs: update documentation`
- `test: add tests`
- `refactor: refactor code`
- `chore: update dependencies`

## Review Process

1. Maintainers will review your PR
2. Address feedback if requested
3. Once approved, your PR will be merged
4. Your contribution will be credited in CHANGELOG.md

## Questions?

- Open a [Discussion](https://github.com/yangfei222666-9/aios/discussions)
- Join our [Discord](https://discord.gg/aios) *(coming soon)*
- Email: *(to be added)*

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

**Thank you for making AIOS better!**
