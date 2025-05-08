# TradeLens Development Guide

This guide is intended for developers who want to contribute to the TradeLens project or understand its architecture for maintenance or extension.

## Table of Contents

- [Project Structure](project_structure.md)
- [Development Environment Setup](environment_setup.md)
- [Coding Standards](coding_standards.md)
- [Database Schema](../database/schema.md)
- [API Reference](../api/index.md)
- [AI Integration](ai_integration.md)
- [Testing Guidelines](testing.md)
- [Contributing Guidelines](contributing.md)

## Architecture Overview

TradeLens follows a monolithic Flask-based architecture with the following components:

### Backend

- **Flask Web Framework**: Handles HTTP requests, renders templates, and serves API endpoints
- **SQLite Database**: Stores transaction data, job information, and application state
- **yfinance Integration**: Fetches stock data from Yahoo Finance
- **Perplexity API Integration**: Provides AI-powered analysis and insights

### Frontend

- **HTML/CSS/JavaScript**: Standard web technologies for the user interface
- **Chart.js**: For interactive data visualization
- **Bootstrap**: For responsive design and UI components

## Core Features and Implementation

### Portfolio Management

The application's portfolio management features are implemented in the main `app.py` file. Key functions include:

- `get_unique_stocks()`: Identifies unique stocks in the transaction history
- `get_stock_price()`: Fetches historical price data for a stock
- `process_transactions()`: Processes raw transaction data for display and analysis
- `calculate_transaction_stats()`: Calculates performance metrics for transactions

### AI Analysis

AI-powered analysis is implemented through the Perplexity API. Key components include:

- AI chat interface for natural language interaction
- Thesis validation for testing investment hypotheses
- Earnings research for pre/post earnings analysis
- Risk assessment for portfolio risk analysis

### Asynchronous Processing

Long-running tasks like thesis validation and earnings research are processed asynchronously:

1. A job is created and stored in the database with a unique ID
2. The task is executed in a background thread
3. Results are stored in the database when complete
4. The frontend polls for job status and displays results when available

## Development Workflow

1. Set up your development environment following the [Environment Setup](environment_setup.md) guide
2. Make code changes following the [Coding Standards](coding_standards.md)
3. Test your changes thoroughly
4. Submit a pull request with a clear description of the changes

## Key Files

- `app.py`: Main application code
- `init_db.py`: Database initialization script
- `requirements.txt`: Python dependencies
- Templates in the `templates/` directory
- Static assets (CSS, JS, images) in the `static/` directory

## Extending TradeLens

To add new features to TradeLens:

1. For UI changes: Modify or add templates in the `templates/` directory
2. For new API endpoints: Add routes to `app.py`
3. For database changes: Update the schema in `init_db.py` and create a migration plan
4. For new AI capabilities: Implement them using the existing Perplexity API integration

See the [Project Structure](project_structure.md) document for details on where to find specific components.

## Future Development

Potential areas for future development include:

- User authentication and multi-user support
- More advanced portfolio analytics
- Additional data sources beyond Yahoo Finance
- Machine learning models for custom predictions
- Mobile application support

## Getting Help

If you need help with development, check the existing documentation or open an issue on the GitHub repository. 