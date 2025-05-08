# Coding Standards

This document outlines the coding standards and best practices for the TradeLens project. Following these guidelines ensures consistency, maintainability, and quality across the codebase.

## Python Style Guide

TradeLens follows [PEP 8](https://www.python.org/dev/peps/pep-0008/) for Python code style, with a few project-specific adaptations.

### Code Formatting

- **Indentation**: 4 spaces (no tabs)
- **Line Length**: Maximum 100 characters
- **Line Breaks**: Use line breaks for clarity, especially in complex expressions
- **Imports**: Group imports in the following order:
  1. Standard library imports
  2. Related third-party imports
  3. Local application imports
- **Whitespace**: Follow PEP 8 whitespace guidelines

```python
# Good example
import os
import sys
import json
from datetime import datetime, timedelta

import pandas as pd
import numpy as np
from flask import Flask, render_template

from init_db import init_db
from utils import format_date, calculate_returns
```

### Naming Conventions

- **Functions and Variables**: Use `snake_case` for functions and variables
- **Classes**: Use `PascalCase` for class names
- **Constants**: Use `UPPER_CASE_WITH_UNDERSCORES` for constants
- **Private Methods/Variables**: Prefix with a single underscore (`_`)
- **Module-Level Dunder Names**: Place at top of file after docstrings but before imports

```python
# Good example
DEFAULT_TIMEOUT = 60  # Constant

def calculate_returns(prices, dates):
    """Calculate returns from a series of prices."""
    # Function implementation

class StockAnalyzer:
    """Class for analyzing stock performance."""
    
    def __init__(self, symbol):
        self.symbol = symbol
        self._cache = {}  # Private variable
    
    def get_historical_data(self):
        """Public method."""
        return self._fetch_data()  # Calls private method
    
    def _fetch_data(self):
        """Private method."""
        # Implementation
```

### Documentation

- **Docstrings**: Use Google-style docstrings for functions, classes, and modules
- **Comments**: Add comments to explain complex logic or non-obvious decisions
- **TODO/FIXME**: Mark incomplete code with `# TODO: description` or `# FIXME: description`

```python
def calculate_sharpe_ratio(returns, risk_free_rate=0.0):
    """Calculate the Sharpe ratio for a series of returns.
    
    The Sharpe ratio is the average return earned in excess of the risk-free
    rate per unit of volatility.
    
    Args:
        returns (list or numpy.array): Array of percentage returns
        risk_free_rate (float, optional): Risk-free rate of return. Defaults to 0.0.
        
    Returns:
        float: The Sharpe ratio
        
    Raises:
        ValueError: If returns is empty or contains non-numeric values
    """
    # Implementation follows...
```

## JavaScript Style Guide

For JavaScript code, TradeLens follows a simplified version of the [Airbnb JavaScript Style Guide](https://github.com/airbnb/javascript).

### Key JavaScript Guidelines

- Use semicolons at the end of statements
- Use `const` for variables that won't be reassigned, `let` otherwise
- Prefer arrow functions for anonymous functions
- Use template literals for string interpolation
- Use camelCase for variables and functions, PascalCase for classes

```javascript
// Good example
const calculateReturns = (prices) => {
    const returns = [];
    for (let i = 1; i < prices.length; i++) {
        const returnValue = (prices[i] - prices[i-1]) / prices[i-1];
        returns.push(returnValue);
    }
    return returns;
};

// Good example of string interpolation
const formatPrice = (price, currency = 'USD') => {
    return `${currency} ${price.toFixed(2)}`;
};
```

## HTML/CSS Standards

### HTML Guidelines

- Use HTML5 semantic elements (`<header>`, `<footer>`, `<nav>`, etc.)
- Maintain proper indentation (2 spaces)
- Use lowercase for element names, attributes, and values
- Use double quotes for attribute values
- Include alt text for images

### CSS Guidelines

- Use classes for styling, not IDs
- Follow BEM (Block Element Modifier) naming convention where appropriate
- Use CSS variables for colors, fonts, and other repeated values
- Organize CSS properties in logical groups
- Comment CSS sections for clarity

```css
/* Good example */
/* Color variables */
:root {
    --primary-color: #4051b5;
    --secondary-color: #6573c3;
    --text-color: #333;
    --background-color: #f9f9f9;
}

/* Dashboard components */
.dashboard__widget {
    background-color: white;
    border-radius: 4px;
    padding: 1rem;
    margin-bottom: 1rem;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.dashboard__widget-title {
    font-size: 1.2rem;
    color: var(--text-color);
    margin-bottom: 0.5rem;
}
```

## SQL Standards

- Use uppercase for SQL keywords (SELECT, INSERT, etc.)
- Use snake_case for table and column names
- Include appropriate indexes for frequently queried columns
- Use parameterized queries to prevent SQL injection
- Comment complex queries

```python
# Good example - parameterized query
def get_transactions_by_symbol(symbol):
    """Get all transactions for a specific stock symbol."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT Date, Time, Symbol, Side, AveragePrice, Qty, Fees 
        FROM transactions 
        WHERE Symbol = ? 
        ORDER BY Date DESC
    """, (symbol,))
    return cursor.fetchall()
```

## Testing Standards

- Write tests for all new features and bug fixes
- Structure tests to match the module structure
- Use descriptive test names that indicate what is being tested
- Include positive tests, negative tests, and edge cases

```python
# Good example
def test_calculate_returns_positive_values():
    """Test return calculation with positive price values."""
    prices = [100, 110, 105, 115]
    expected = [0.10, -0.045, 0.095]
    assert calculate_returns(prices) == pytest.approx(expected)

def test_calculate_returns_empty_list():
    """Test return calculation with empty list raises ValueError."""
    with pytest.raises(ValueError):
        calculate_returns([])
```

## Code Organization

### File Structure

- Keep files focused on a single responsibility
- Organize related functionality into modules
- Limit file size (consider refactoring files over 500 lines)

### Function and Class Design

- Follow the Single Responsibility Principle
- Keep functions short and focused (ideally < 50 lines)
- Limit function parameters (ideally <= 5)
- Use default parameter values where appropriate
- Return early from functions to reduce nesting

```python
# Good example
def validate_transaction(transaction):
    """Validate a transaction record before processing."""
    if not transaction:
        return False
        
    if 'Symbol' not in transaction or not transaction['Symbol']:
        return False
        
    if 'Date' not in transaction:
        return False
        
    # More validation...
    return True
```

## Error Handling

- Use specific exception types
- Catch exceptions at the appropriate level
- Log exceptions with useful context
- Provide friendly error messages to users

```python
# Good example
def get_stock_price(symbol, date):
    """Get the stock price for a symbol on a specific date."""
    try:
        stock = yf.Ticker(symbol)
        data = stock.history(start=date, end=date)
        if data.empty:
            logger.warning(f"No price data found for {symbol} on {date}")
            return None
        return data['Close'].iloc[0]
    except Exception as e:
        logger.error(f"Error fetching price for {symbol} on {date}: {str(e)}")
        raise StockDataError(f"Could not retrieve price data for {symbol}") from e
```

## Version Control Practices

### Commit Messages

- Use the imperative mood ("Add feature" not "Added feature")
- Keep the first line under 50 characters
- Provide more details in the commit body if needed
- Reference issue numbers where appropriate

```
# Good example
Add portfolio diversification calculation

- Calculate sector diversification using Shannon entropy
- Add visualization for sector allocation
- Update documentation

Fixes #123
```

### Branching Strategy

- `main`: Stable, production-ready code
- `develop`: Integration branch for feature development
- Feature branches: Named `feature/name-of-feature`
- Bug fix branches: Named `fix/brief-description`

### Pull Requests

- Provide a clear description of changes
- Link to relevant issues
- Keep PRs focused on a single change
- Include screenshots for UI changes

## Security Guidelines

- Never commit sensitive information (API keys, passwords, etc.)
- Use environment variables for configuration
- Validate all user inputs
- Use parameterized queries for database access
- Follow secure coding practices

## Performance Considerations

- Be mindful of memory usage, especially with large datasets
- Use appropriate data structures for performance
- Cache expensive operations where appropriate
- Profile code for performance bottlenecks
- Optimize critical paths

## Accessibility

- Ensure UI is keyboard navigable
- Use semantic HTML elements
- Provide alt text for images
- Maintain sufficient color contrast
- Test with screen readers

## Conclusion

Following these coding standards will help maintain a high-quality, consistent codebase that is easier to understand, modify, and extend. If you have suggestions for improvements to these standards, please discuss them with the team. 