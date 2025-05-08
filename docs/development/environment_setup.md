# Development Environment Setup

This guide provides instructions for setting up a development environment for contributing to the TradeLens project.

## Prerequisites

Before you begin, make sure you have the following installed:

- **Python 3.8 or higher**: Required for running the application
- **pip**: The Python package manager
- **Git**: For version control
- **SQLite**: For the database (usually comes with Python)
- **Node.js** (optional): For front-end development tasks

## Setting Up the Development Environment

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/tradelens.git
cd tradelens
```

### 2. Create and Activate a Virtual Environment

Creating a virtual environment isolates your development dependencies from your system Python installation.

#### On macOS/Linux:

```bash
python -m venv venv
source venv/bin/activate
```

#### On Windows:

```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Install Dependencies

Install all required Python packages:

```bash
pip install -r requirements.txt
```

For development, you might want to install additional development dependencies:

```bash
pip install pytest pytest-cov flake8 black mypy
```

### 4. Set Up Environment Variables

Create a `.env` file in the project root with the following content:

```
PERPLEXITY_API_KEY=your_perplexity_api_key
OPENAI_API_KEY=your_openai_api_key (optional)
FLASK_ENV=development
DEBUG=True
```

You'll need to obtain your own Perplexity API key for development.

### 5. Initialize the Database

Initialize the SQLite database with sample data:

```bash
python init_db.py
```

### 6. Run the Development Server

Start the Flask development server:

```bash
# Using the provided script
./run_server.sh

# Or directly with Python
python app.py
```

The application should now be running at `http://localhost:5000`.

## Development Workflow

### Code Organization

TradeLens follows a monolithic Flask architecture:

- `app.py`: Main application file with routes and core functionality
- `init_db.py`: Database initialization script
- `templates/`: HTML templates for the UI
- `static/`: Static assets (CSS, JS, images)

### Making Changes

1. Create a branch for your feature or bug fix:

```bash
git checkout -b feature/your-feature-name
```

2. Make your changes to the codebase
3. Run tests to ensure everything works
4. Commit your changes with a descriptive message
5. Push your branch and create a pull request

### Running Tests

TradeLens doesn't currently have an automated test suite, but you can manually test your changes:

1. Run the application in development mode
2. Test all affected functionality
3. Check for any errors in the console or application logs

### Code Quality Tools

#### Linting with Flake8

```bash
flake8 .
```

#### Formatting with Black

```bash
black .
```

#### Type Checking with MyPy

```bash
mypy app.py
```

## Debugging

### Flask Debugging

When running in development mode, Flask provides an interactive debugger in the browser. If an exception occurs, you'll see a detailed error page with a Python console.

### Logging

TradeLens uses Python's `logging` module. Log messages are written to both the console and `app.log`. You can add your own log messages for debugging:

```python
import logging
logger = logging.getLogger('tradelens')

# Then in your code:
logger.debug("Debug message")
logger.info("Info message")
logger.warning("Warning message")
logger.error("Error message")
```

### Database Inspection

You can directly inspect the SQLite database using the SQLite command-line tool or a GUI like [DB Browser for SQLite](https://sqlitebrowser.org/):

```bash
sqlite3 stock_transactions.db
```

## Development Tools

### Recommended IDE: Visual Studio Code

#### Useful Extensions:
- Python (by Microsoft)
- SQLite Viewer
- Prettier - Code formatter
- GitLens
- Flask-Snippets

### API Testing

For testing API endpoints, you can use:
- [Postman](https://www.postman.com/)
- [curl](https://curl.se/) command-line tool
- [Insomnia](https://insomnia.rest/)

### Browser Developer Tools

Use your browser's developer tools (F12 in most browsers) to:
- Debug JavaScript
- Inspect network requests
- Analyze performance
- View console messages

## Typical Development Tasks

### Adding a New Feature

1. Plan your feature and which files will need modification
2. Update the database schema in `init_db.py` if necessary
3. Add new routes/functions to `app.py`
4. Create or modify templates in the `templates/` directory
5. Add static assets (JS/CSS) to the `static/` directory
6. Test your feature thoroughly
7. Update documentation in the `docs/` directory

### Fixing a Bug

1. Identify the source of the bug
2. Write a failing test case (if possible)
3. Fix the bug in the appropriate file(s)
4. Verify the fix works
5. Add comments explaining the fix if necessary

### Working with the Database

If you need to modify the database schema:

1. Update the schema in `init_db.py`
2. Create a migration script if needed for existing installations
3. Test both fresh installations and upgrades

## Troubleshooting Development Issues

### Common Problems and Solutions

#### Application Won't Start

- Check that all dependencies are installed
- Verify that your `.env` file exists with the correct variables
- Make sure no other service is using port 5000

#### Database Errors

- Ensure SQLite is installed and working
- Check file permissions on the database file
- Verify your SQL syntax in any queries you've modified

#### API Integration Issues

- Validate your API keys
- Check network connectivity
- Look for rate limiting or quota issues

## Getting Help

If you need assistance with development:

- Check the existing documentation in the `docs/` directory
- Look for similar issues in the issue tracker
- Reach out to other developers on the project

## Next Steps

Once your development environment is set up, you may want to:

- Review the [Project Structure](project_structure.md) documentation
- Learn about the [AI Integration](ai_integration.md)
- Check the [Coding Standards](coding_standards.md) for the project 