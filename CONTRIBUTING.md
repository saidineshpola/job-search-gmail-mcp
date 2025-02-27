# Contributing to Gmail MCP Server

Thank you for your interest in contributing to the Gmail MCP Server! This document provides guidelines and instructions for contributing.

## Code of Conduct

Please be respectful and considerate of others when contributing to this project.

## How to Contribute

### Reporting Bugs

If you find a bug, please create an issue with the following information:
- A clear, descriptive title
- Steps to reproduce the bug
- Expected behavior
- Actual behavior
- Any relevant logs or screenshots
- Your environment (OS, Python version, etc.)

### Suggesting Enhancements

If you have an idea for an enhancement, please create an issue with:
- A clear, descriptive title
- A detailed description of the enhancement
- Any relevant examples or mockups

### Pull Requests

1. Fork the repository
2. Create a new branch (`git checkout -b feature/your-feature-name`)
3. Make your changes
4. Run tests if available
5. Commit your changes (`git commit -m 'Add some feature'`)
6. Push to the branch (`git push origin feature/your-feature-name`)
7. Open a Pull Request

## Development Setup

1. Clone your fork of the repository
2. Set up a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```
3. Install the package in development mode:
   ```bash
   pip install -e .
   ```

## Testing

Currently, the project does not have automated tests. If you're adding a new feature, please consider adding tests for it.

## Style Guidelines

- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) for Python code
- Use descriptive variable names
- Add comments for complex logic
- Update documentation when changing functionality

## Security Considerations

- Never commit credentials or tokens to the repository
- Be careful when handling user data and authentication
- Report security vulnerabilities privately to the maintainers

## License

By contributing to this project, you agree that your contributions will be licensed under the same license as the project. 