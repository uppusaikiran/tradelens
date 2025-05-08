# TradeLens Project Structure

This document outlines the structure of the TradeLens project, explaining the purpose of each directory and key files.

## Directory Structure

```
tradelens/
├── static/                  # Static assets
│   ├── css/                 # CSS stylesheets
│   ├── img/                 # Images
│   │   ├── avatar/          # User avatars
│   │   ├── dashboard_images/ # Dashboard screenshots for documentation
│   │   ├── icons/           # UI icons
│   │   └── logos/           # Company logos
│   └── js/                  # JavaScript files
├── templates/               # HTML templates
├── venv/                    # Python virtual environment
├── .env                     # Environment variables (API keys, etc.)
├── .gitignore               # Git ignore rules
├── add_sidebar_script.sh    # Script to add sidebar to templates
├── app.log                  # Application log file
├── app.py                   # Main application file
├── check_earnings.py        # Script to check for upcoming earnings
├── clean.sh                 # Cleanup script
├── cleanup.sh               # Another cleanup script
├── cleanup_logos.py         # Script to clean up logo files
├── fix_earnings_dates.py    # Script to fix earnings dates in the database
├── init_db.py               # Database initialization script
├── package-lock.json        # npm package lock file
├── package.json             # npm package file
├── populate_earnings_data.py # Script to populate earnings data
├── README.md                # Project readme
├── rebuild_db.sh            # Script to rebuild the database
├── requirements.txt         # Python dependencies
├── run_server.sh            # Script to run the server
├── setup_env.sh             # Script to set up environment
├── stock_orders.csv         # Sample stock order data
└── stock_transactions.db    # SQLite database
```

## Key Files

### Application Code

- **app.py**: The main Flask application file containing:
  - Route definitions
  - API endpoints
  - Database access functions
  - Business logic for portfolio analysis
  - AI integration

- **init_db.py**: Initializes the SQLite database and sets up the schema.

### Utility Scripts

- **check_earnings.py**: Checks for upcoming earnings announcements for stocks in the portfolio.
- **populate_earnings_data.py**: Populates earnings data from external sources.
- **fix_earnings_dates.py**: Utility to fix earnings dates in the database.
- **cleanup_logos.py**: Cleans up and organizes company logo files.

### Configuration

- **.env**: Contains environment variables such as API keys.
- **requirements.txt**: Lists Python dependencies.
- **package.json**: Lists npm dependencies (if any).

### Shell Scripts

- **run_server.sh**: Script to start the Flask server.
- **rebuild_db.sh**: Rebuilds the database from scratch.
- **setup_env.sh**: Sets up the development environment.
- **clean.sh** / **cleanup.sh**: Cleanup scripts for development.
- **add_sidebar_script.sh**: Utility script to add navigation sidebars to templates.

## Templates

The `templates/` directory contains HTML templates used by Flask's template engine. Key templates include:

- **layout.html**: Base layout template with common elements
- **index.html**: Main dashboard template
- **stock_detail.html**: Individual stock detail page
- **settings.html**: Settings page
- **thesis_validation.html**: Investment thesis validation page
- **earnings_companion.html**: Earnings analysis page
- **risk_review.html**: Risk assessment page
- **strategy_backtesting.html**: Strategy backtesting page
- **event_risk_calendar.html**: Event risk calendar page

## Static Files

The `static/` directory contains static assets organized as follows:

### CSS

- CSS stylesheets for styling the application.

### JavaScript

- Client-side JavaScript files for interactive features.

### Images

- **avatar/**: User avatar images.
- **dashboard_images/**: Screenshots of the dashboard for documentation.
- **icons/**: Icons used in the user interface.
- **logos/**: Company logos for stocks in the portfolio.

## Database

The `stock_transactions.db` file is a SQLite database containing all persistent data for the application. See the [Database Schema](../database/schema.md) document for details on its structure.

## Virtual Environment

The `venv/` directory contains the Python virtual environment with all dependencies installed. This directory is typically excluded from version control.

## Adding New Features

When adding new features to the project:

1. **Backend changes**:
   - Add new routes and functionality to `app.py`
   - Create new utility scripts if needed
   - Update database schema in `init_db.py` if required

2. **Frontend changes**:
   - Add new templates to the `templates/` directory
   - Add CSS styles to files in `static/css/`
   - Add JavaScript functionality to files in `static/js/`

3. **Documentation**:
   - Update relevant documentation in the `docs/` directory

Always follow the existing patterns and conventions when making changes to maintain consistency throughout the project. 