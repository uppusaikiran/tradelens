# TradeLens Database Schema

TradeLens uses SQLite as its database engine. This document outlines the schema of the database, including all tables, their fields, and relationships.

## Database File

The database is stored in a file named `stock_transactions.db` in the root directory of the project.

## Tables

### transactions

Stores information about stock transactions (buys and sells).

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key, auto-increment |
| Date | DATE | Date of the transaction (YYYY-MM-DD) |
| Time | TEXT | Time of the transaction |
| Symbol | TEXT | Stock symbol (e.g., AAPL) |
| Name | TEXT | Company name |
| Type | TEXT | Transaction type |
| Side | TEXT | Buy or Sell |
| AveragePrice | REAL | Average price per share |
| Qty | REAL | Number of shares |
| State | TEXT | Transaction state (e.g., Filled) |
| Fees | REAL | Transaction fees |

### thesis_jobs

Stores information about investment thesis validation jobs.

| Column | Type | Description |
|--------|------|-------------|
| job_id | TEXT | Primary key, unique identifier for the job |
| thesis | TEXT | The investment thesis being validated |
| status | TEXT | Job status (pending, processing, completed, failed) |
| created_at | TEXT | Timestamp when the job was created |
| completed_at | TEXT | Timestamp when the job was completed (NULL if not completed) |
| result | TEXT | JSON-encoded result of the thesis validation |

### earnings_jobs

Stores information about earnings research jobs.

| Column | Type | Description |
|--------|------|-------------|
| job_id | TEXT | Primary key, unique identifier for the job |
| symbol | TEXT | Stock symbol being researched |
| earnings_date | TEXT | Date of the earnings release |
| status | TEXT | Job status (pending, processing, completed, failed) |
| created_at | TEXT | Timestamp when the job was created |
| completed_at | TEXT | Timestamp when the job was completed (NULL if not completed) |
| result | TEXT | JSON-encoded result of the earnings research |

### earnings_calendar

Stores information about upcoming earnings announcements.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key, auto-increment |
| symbol | TEXT | Stock symbol |
| company_name | TEXT | Company name |
| earnings_date | TEXT | Date of the earnings announcement |
| time_of_day | TEXT | Time of day for the announcement (BMO, AMC, etc.) |
| eps_estimate | REAL | Earnings per share estimate |
| last_updated | TEXT | Timestamp when the record was last updated |

### market_events

Stores information about important market events that could impact stocks.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key, auto-increment |
| event_date | DATE | Date of the event |
| event_time | TEXT | Time of the event (if applicable) |
| event_type | TEXT | Type of event (FOMC, CPI, Earnings, etc.) |
| symbol | TEXT | Related stock symbol (if applicable) |
| title | TEXT | Event title |
| subtitle | TEXT | Event subtitle |
| description | TEXT | Detailed description of the event |
| impact_level | TEXT | Estimated impact level (High, Medium, Low) |
| source | TEXT | Source of the event information |
| created_at | TEXT | Timestamp when the record was created |
| updated_at | TEXT | Timestamp when the record was last updated |

## Initialization

The database is initialized using the `init_db.py` script, which creates the tables if they don't exist. It also imports transaction data from a CSV file (`stock_orders.csv`) if the transactions table is empty.

## Data Types

- **INTEGER**: Whole numbers
- **REAL**: Floating-point numbers
- **TEXT**: Text strings
- **DATE**: Date values stored as text in ISO format (YYYY-MM-DD)

## Relationships

While SQLite doesn't enforce foreign key constraints by default, the following relationships exist conceptually:

- The `symbol` field in `earnings_jobs` relates to the `Symbol` field in `transactions`
- The `symbol` field in `earnings_calendar` relates to the `Symbol` field in `transactions`
- The `symbol` field in `market_events` may relate to the `Symbol` field in `transactions`

## Data Storage

All date and time values are stored as text strings in ISO format:
- Dates: YYYY-MM-DD
- Timestamps: YYYY-MM-DD HH:MM:SS

Complex data (like job results) is stored as JSON-encoded text strings in the database.

## Database Backup

It is recommended to regularly back up the `stock_transactions.db` file to prevent data loss. The application does not currently include automated backup functionality. 