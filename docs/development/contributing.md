# Contributing Guidelines

Thank you for your interest in contributing to TradeLens! This document provides guidelines and instructions for contributing to the project.

## Code of Conduct

Please read and follow our [Code of Conduct](code_of_conduct.md) to help us maintain a healthy and welcoming community.

## Getting Started

### Prerequisites

Before you begin, ensure you have:

- Python 3.8 or higher
- Git
- A GitHub account
- Familiarity with Flask (for backend contributions)
- Basic understanding of HTML/CSS/JavaScript (for frontend contributions)

### Setting Up Your Development Environment

1. Fork the repository on GitHub
2. Clone your fork locally:
   ```bash
   git clone https://github.com/yourusername/tradelens.git
   cd tradelens
   ```
3. Set up the development environment by following the [Environment Setup](environment_setup.md) guide
4. Create a branch for your work:
   ```bash
   git checkout -b feature/your-feature-name
   ```

## Types of Contributions

### Bug Fixes

1. If you find a bug, first check if it's already reported in the Issues section
2. If not, create a new issue with a clear description, steps to reproduce, and expected vs. actual behavior
3. If you're fixing a bug, reference the issue number in your pull request

### Feature Development

1. For new features, first open an issue to discuss the feature before implementing it
2. This helps ensure the feature aligns with the project's goals and avoids duplicate work
3. Once the feature is approved, create a branch and implement it

### Documentation Improvements

1. Documentation improvements are always welcome
2. Check the existing documentation in the `docs/` directory
3. Submit a pull request with your proposed changes or additions

### Code Refactoring

1. Code refactoring should improve code quality without changing functionality
2. Ensure thorough testing of refactored code
3. Clearly explain the benefits of the refactoring in your pull request

## Development Workflow

### Branching Strategy

- `main`: Stable production code
- `develop`: Integration branch for features
- Feature branches: Created from `develop` and named `feature/your-feature-name`
- Bug fix branches: Named `fix/issue-description`

### Commit Guidelines

- Write clear, concise commit messages
- Use the imperative mood ("Add feature" not "Added feature")
- Reference issue numbers when applicable
- Keep commits focused and atomic
- Example: `Add portfolio diversification calculation (#123)`

### Pull Request Process

1. Ensure your code follows the [Coding Standards](coding_standards.md)
2. Update documentation to reflect any changes
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit the pull request to the `develop` branch
6. Fill out the pull request template completely

### Code Review

- All code changes require review before merging
- Address review feedback promptly
- Be open to constructive criticism
- Explain your design decisions when asked

## Testing

- All new features should include appropriate tests
- All bug fixes should include tests that verify the fix
- Follow the [Testing Guidelines](testing.md) for writing effective tests

## Documentation

- Update documentation for any feature changes
- Document new features thoroughly
- Improve existing documentation where needed
- Use clear, concise language

## Performance Considerations

- Be mindful of the performance impact of your changes
- Consider both time complexity and memory usage
- Test with large datasets where appropriate
- Profile code if you're working on performance-critical sections

## Security Best Practices

- Never commit sensitive information (API keys, passwords, etc.)
- Validate all user inputs
- Use parameterized SQL queries to prevent injection
- Follow secure coding practices
- Report security vulnerabilities privately

## Pull Request Template

When submitting a pull request, please use the following template:

```markdown
## Description
[Provide a brief description of the changes]

## Issue
[Link to the related issue, if applicable]

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Refactoring
- [ ] Performance improvement
- [ ] Other (please describe)

## Testing
[Describe the testing you've done]

## Screenshots
[If applicable, add screenshots]

## Checklist
- [ ] My code follows the project's coding standards
- [ ] I have updated the documentation
- [ ] I have added tests that prove my fix/feature works
- [ ] All tests pass locally
- [ ] I have checked for potential performance issues
```

## Review Process

1. A maintainer will review your pull request
2. They may request changes or clarification
3. Once approved, your changes will be merged
4. You'll be credited as a contributor

## Getting Help

If you need help with your contribution:

- Check the documentation in the `docs/` directory
- Look for similar issues or pull requests
- Ask questions in the issue or pull request
- Reach out to the maintainers

## Recognition

All contributors will be recognized in the project's `CONTRIBUTORS.md` file. We value every contribution, no matter how small!

## Style Guides

### Python Style Guide

Follow the project's [Coding Standards](coding_standards.md) for Python code.

### JavaScript Style Guide

- Use ES6+ features where possible
- Follow a consistent indentation (2 spaces)
- Use semicolons at the end of statements
- Use meaningful variable and function names

### HTML/CSS Style Guide

- Use semantic HTML5 elements
- Maintain consistent indentation (2 spaces)
- Follow BEM naming convention for CSS classes
- Use CSS variables for consistent theming

## License

By contributing to TradeLens, you agree that your contributions will be licensed under the project's license. 