# Testing Guidelines

This document outlines the testing approach and guidelines for the TradeLens project. Following these practices ensures the reliability and stability of the application.

## Testing Philosophy

TradeLens follows these testing principles:

1. **Test-Driven Development**: Write tests before implementing features when possible
2. **Comprehensive Coverage**: Aim for high test coverage of critical code paths
3. **Maintainable Tests**: Keep tests simple, focused, and easy to understand
4. **Fast Execution**: Tests should run quickly to encourage frequent testing

## Types of Tests

### 1. Unit Tests

Unit tests verify that individual components work correctly in isolation.

#### Key Characteristics

- Focus on testing a single function, class, or module
- Mock external dependencies
- Run quickly and reliably
- Test both normal and edge cases

#### Example

```python
import pytest
from utils import calculate_returns

def test_calculate_returns_normal_case():
    """Test return calculation with typical price series."""
    prices = [100, 105, 103, 110]
    expected = [0.05, -0.019, 0.068]
    assert calculate_returns(prices) == pytest.approx(expected)

def test_calculate_returns_with_zero():
    """Test return calculation with a zero price (division by zero case)."""
    prices = [100, 0, 50]
    with pytest.raises(ValueError):
        calculate_returns(prices)
```

### 2. Integration Tests

Integration tests verify that components work correctly together.

#### Key Characteristics

- Test interactions between components
- May involve multiple modules or classes
- Often test data flow between components
- Can involve database interactions

#### Example

```python
def test_stock_data_pipeline():
    """Test the complete stock data processing pipeline."""
    # Set up test data
    symbol = "TEST"
    dates = ["2023-01-01", "2023-01-02", "2023-01-03"]
    
    # Run the pipeline
    raw_data = fetch_stock_data(symbol, dates)
    processed_data = process_stock_data(raw_data)
    results = calculate_metrics(processed_data)
    
    # Verify results
    assert "returns" in results
    assert "volatility" in results
    assert len(results["returns"]) == len(dates) - 1
```

### 3. Functional Tests

Functional tests verify that the application meets business requirements.

#### Key Characteristics

- Focus on user scenarios and workflows
- Test the application as a whole
- Often involve UI interactions
- Verify business logic and requirements

#### Example

```python
def test_portfolio_analysis_workflow():
    """Test the complete portfolio analysis workflow."""
    # Set up test data
    transactions = [
        {"Date": "2023-01-01", "Symbol": "AAPL", "Side": "Buy", "Qty": 10, "AveragePrice": 150},
        {"Date": "2023-01-15", "Symbol": "MSFT", "Side": "Buy", "Qty": 5, "AveragePrice": 250}
    ]
    
    # Create a test client
    with app.test_client() as client:
        # Upload transactions
        response = client.post('/upload', data={'transactions': json.dumps(transactions)})
        assert response.status_code == 200
        
        # Run portfolio analysis
        response = client.get('/portfolio-analysis')
        assert response.status_code == 200
        
        # Verify analysis results are present
        assert b"Total Value" in response.data
        assert b"Sector Allocation" in response.data
```

### 4. API Tests

API tests verify that API endpoints function correctly.

#### Key Characteristics

- Focus on API endpoints
- Test request/response formats
- Verify authentication and authorization
- Check error handling

#### Example

```python
def test_stock_chart_api():
    """Test the stock chart API endpoint."""
    with app.test_client() as client:
        # Test successful response
        response = client.get('/api/stock_chart/AAPL')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert "dates" in data
        assert "prices" in data
        
        # Test error handling
        response = client.get('/api/stock_chart/INVALID')
        assert response.status_code == 404
```

## Test Setup

### Directory Structure

Tests should be organized to mirror the structure of the application code:

```
tradelens/
├── app.py
├── utils.py
├── ...
└── tests/
    ├── test_app.py
    ├── test_utils.py
    ├── ...
    ├── integration/
    │   └── test_data_pipeline.py
    └── functional/
        └── test_workflows.py
```

### Test Dependencies

- **pytest**: Main testing framework
- **pytest-cov**: For test coverage reporting
- **unittest.mock**: For mocking dependencies

## Writing Effective Tests

### Test Naming

Use descriptive names that indicate:
- What is being tested
- Under what conditions
- What the expected outcome is

```python
def test_get_stock_price_returns_none_when_data_not_available():
    # Test implementation
```

### Test Structure

Follow the Arrange-Act-Assert (AAA) pattern:

```python
def test_calculate_returns():
    # Arrange
    prices = [100, 110, 105]
    
    # Act
    returns = calculate_returns(prices)
    
    # Assert
    assert returns == pytest.approx([0.1, -0.045])
```

### Mocking

Use mocks for external dependencies:

```python
from unittest.mock import patch, MagicMock

@patch('yfinance.Ticker')
def test_get_historical_prices(mock_ticker):
    # Configure the mock
    mock_instance = MagicMock()
    mock_ticker.return_value = mock_instance
    mock_history = MagicMock()
    mock_instance.history.return_value = mock_history
    
    # Set up mock data
    mock_history.empty = False
    mock_history.__getitem__.return_value.iloc.__getitem__.return_value = 150.0
    
    # Call the function under test
    result = get_stock_price("AAPL", "2023-01-01")
    
    # Assert
    assert result == 150.0
    mock_instance.history.assert_called_once_with(start="2023-01-01", end="2023-01-01")
```

### Test Data

Use fixtures for common test data:

```python
import pytest

@pytest.fixture
def sample_transactions():
    return [
        {"Date": "2023-01-01", "Symbol": "AAPL", "Side": "Buy", "Qty": 10, "AveragePrice": 150},
        {"Date": "2023-01-15", "Symbol": "MSFT", "Side": "Buy", "Qty": 5, "AveragePrice": 250},
        {"Date": "2023-02-01", "Symbol": "AAPL", "Side": "Sell", "Qty": 5, "AveragePrice": 170}
    ]

def test_calculate_portfolio_value(sample_transactions):
    result = calculate_portfolio_value(sample_transactions)
    # Test with the fixture data
```

## Testing Database Operations

For database tests, use an in-memory SQLite database:

```python
import sqlite3
import pytest

@pytest.fixture
def test_db():
    """Create an in-memory database for testing."""
    conn = sqlite3.connect(':memory:')
    cursor = conn.cursor()
    
    # Create test schema
    cursor.execute('''
    CREATE TABLE transactions (
        id INTEGER PRIMARY KEY,
        Date TEXT,
        Symbol TEXT,
        Side TEXT,
        Qty REAL,
        AveragePrice REAL
    )
    ''')
    
    # Insert test data
    cursor.execute('''
    INSERT INTO transactions (Date, Symbol, Side, Qty, AveragePrice)
    VALUES (?, ?, ?, ?, ?)
    ''', ('2023-01-01', 'AAPL', 'Buy', 10, 150))
    
    conn.commit()
    return conn

def test_get_transactions(test_db):
    """Test getting transactions from the database."""
    # Use the test database connection
    result = get_transactions(db_connection=test_db)
    assert len(result) == 1
    assert result[0]['Symbol'] == 'AAPL'
```

## Testing Flask Routes

Use Flask's test client for testing routes:

```python
def test_index_route():
    """Test the main dashboard route."""
    with app.test_client() as client:
        response = client.get('/')
        assert response.status_code == 200
        assert b"TradeLens Dashboard" in response.data
```

## Testing AI Features

For testing AI-powered features, create mock responses:

```python
@patch('app.perplexity_client')
def test_ai_chat_feature(mock_perplexity):
    """Test the AI chat feature with mock responses."""
    # Configure the mock
    mock_completion = MagicMock()
    mock_perplexity.chat.completions.create.return_value = mock_completion
    mock_completion.choices = [MagicMock()]
    mock_completion.choices[0].message.content = "This is a mock AI response about AAPL."
    
    # Call the endpoint
    with app.test_client() as client:
        response = client.post('/api/chat', json={
            'message': 'Tell me about AAPL',
            'current_stock': 'AAPL'
        })
        
        # Verify response
        assert response.status_code == 200
        data = json.loads(response.data)
        assert "This is a mock AI response" in data['response']
```

## Test Coverage

Aim for high test coverage, especially for critical components:

```bash
# Run tests with coverage reporting
pytest --cov=. --cov-report=term --cov-report=html
```

Review the coverage report to identify areas that need additional tests.

## Continuous Integration

Run tests automatically in the CI pipeline:

- Run tests on every push and pull request
- Enforce minimum coverage thresholds
- Prevent merging code that fails tests

## Regression Testing

Create regression tests for fixed bugs:

```python
def test_bug_123_fixed():
    """Test that bug #123 is fixed.
    
    Bug description: Portfolio value calculation was incorrect when
    a stock was completely sold.
    """
    transactions = [
        {"Date": "2023-01-01", "Symbol": "AAPL", "Side": "Buy", "Qty": 10, "AveragePrice": 150},
        {"Date": "2023-02-01", "Symbol": "AAPL", "Side": "Sell", "Qty": 10, "AveragePrice": 170}
    ]
    
    result = calculate_portfolio_value(transactions)
    assert result == 0  # Portfolio should be empty
```

## Performance Testing

Test performance of critical operations:

```python
def test_large_portfolio_performance():
    """Test performance with a large portfolio."""
    # Generate a large portfolio
    large_portfolio = generate_test_portfolio(1000)  # 1000 transactions
    
    # Measure execution time
    start_time = time.time()
    result = calculate_portfolio_metrics(large_portfolio)
    execution_time = time.time() - start_time
    
    # Assert reasonable performance
    assert execution_time < 1.0  # Should complete in under 1 second
```

## Getting Started with Testing

To run the tests:

```bash
# Install test dependencies
pip install pytest pytest-cov

# Run all tests
pytest

# Run a specific test file
pytest tests/test_utils.py

# Run a specific test
pytest tests/test_utils.py::test_calculate_returns
```

## Best Practices

1. **Write tests for new features**: All new features should include tests
2. **Write regression tests for bugs**: Create tests that verify bug fixes
3. **Keep tests independent**: Tests should not depend on each other
4. **Use descriptive assertions**: Error messages should clearly indicate what went wrong
5. **Maintain test code quality**: Apply the same code quality standards to tests as to application code 