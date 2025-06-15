# Contributing to GUST Bot Enhanced

Thank you for your interest in contributing to GUST Bot Enhanced! This document provides guidelines and information for contributors.

## 🤝 How to Contribute

### Ways to Contribute
- 🐛 **Bug Reports**: Report issues you encounter
- 💡 **Feature Requests**: Suggest new features
- 📝 **Documentation**: Improve or add documentation
- 💻 **Code**: Submit bug fixes or new features
- 🧪 **Testing**: Help test new features and releases
- 🎨 **UI/UX**: Improve the user interface and experience

## 🚀 Getting Started

### 1. Fork and Clone
```bash
# Fork the repository on GitHub
# Then clone your fork
git clone https://github.com/YOUR-USERNAME/GUST-MARK-1.git
cd GUST-MARK-1

# Add upstream remote
git remote add upstream https://github.com/WDC-GP/GUST-MARK-1.git
```

### 2. Development Setup
```bash
# Create directories
mkdir -p data templates static/css static/js

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install pytest pytest-flask black flake8

# Run in development mode
export FLASK_ENV=development
python main.py
```

### 3. Create Feature Branch
```bash
# Update your fork
git checkout main
git pull upstream main

# Create feature branch
git checkout -b feature/your-feature-name
# or
git checkout -b bugfix/issue-number
```

## 📋 Development Guidelines

### Code Style

#### Python Backend
- Follow [PEP 8](https://pep8.org/) style guidelines
- Use [Black](https://black.readthedocs.io/) for code formatting
- Use [Flake8](https://flake8.pycqa.org/) for linting
- Include type hints where possible
- Write comprehensive docstrings

#### JavaScript Frontend
- Use ES6+ features
- Follow consistent naming conventions
- Use modular design patterns
- Include JSDoc comments for functions
- Handle errors gracefully

### Testing Guidelines

#### Unit Tests
```python
import pytest
from app import GustBotEnhanced

def test_example_function():
    """Test example function behavior"""
    app = GustBotEnhanced()
    result = app.example_function("test")
    assert result is True
```

#### Manual Testing Checklist
- [ ] Test in demo mode
- [ ] Test with G-Portal credentials (if available)
- [ ] Test all UI tabs
- [ ] Test WebSocket connections
- [ ] Test mobile responsiveness
- [ ] Test error scenarios

## 🐛 Bug Reports

### Bug Report Template
Use our bug report template when creating issues. Include:
- Clear description of the bug
- Steps to reproduce
- Expected vs actual behavior
- Environment details (OS, Python version, browser)
- Screenshots if applicable

## 💡 Feature Requests

### Feature Request Template
Use our feature request template. Include:
- Clear description of the feature
- Use case and motivation
- Proposed implementation
- Alternatives considered

## 📥 Pull Request Process

### Before Submitting
- [ ] Code follows style guidelines
- [ ] All tests pass
- [ ] Documentation is updated
- [ ] Manual testing completed
- [ ] No merge conflicts

### Pull Request Checklist
- [ ] Descriptive title and description
- [ ] References related issues
- [ ] Includes tests for new functionality
- [ ] Updates documentation if needed
- [ ] Follows coding standards

## 🔒 Security Guidelines

### Input Validation
- Validate all user inputs server-side
- Sanitize HTML content
- Use parameterized queries
- Implement rate limiting

### Authentication
- Never store passwords in plain text
- Use secure session management
- Implement proper logout
- Validate tokens properly

## 📚 Documentation Guidelines

### Code Documentation
- Write clear docstrings for functions
- Comment complex logic
- Include usage examples
- Document API endpoints

### User Documentation
- Keep README up to date
- Provide clear setup instructions
- Include troubleshooting guides
- Add screenshots for UI features

## 🧪 Testing Strategy

### Test Types
- **Unit Tests**: Individual function testing
- **Integration Tests**: API endpoint testing
- **Manual Tests**: UI and workflow testing
- **Performance Tests**: Load and stress testing

## 💬 Community Guidelines

### Communication
- Be respectful and inclusive
- Provide constructive feedback
- Help newcomers
- Follow the code of conduct

### Issue Management
- Use clear, descriptive titles
- Provide sufficient context
- Follow up on requests for information
- Close issues when resolved

## 📞 Getting Help

### Resources
- [Documentation](.github/DOCUMENTATION.md)
- [Theme Customization](.github/THEME_QUICK_REF.md)
- [GitHub Discussions](https://github.com/WDC-GP/GUST-MARK-1/discussions)

### Contact
- Create GitHub issues for bugs
- Use discussions for questions
- Check existing issues first
- Provide detailed information

Thank you for contributing to GUST Bot Enhanced! Your contributions help make this project better for everyone in the Rust community.
