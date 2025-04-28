# Stock Transactions Analyzer

A Flask web application to analyze stock transactions from a CSV file.

## Features

1. View all transactions with pagination (10 per page)
2. Sort transactions by date (newest first)
3. Filter transactions by stock ticker
4. Responsive UI with Bootstrap

## Installation

1. Clone this repository:
```
git clone <repository-url>
cd robinhood_analyze
```

2. Create a virtual environment and activate it:
```
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install the required dependencies:
```
pip install -r requirements.txt
```

## Usage

1. Make sure your stock transaction data is in the `stock_orders.csv` file in the root directory.

2. Run the application:
```
python app.py
```

3. Open your browser and navigate to `http://127.0.0.1:5000`.

## File Structure

- `app.py`: Main Flask application
- `stock_orders.csv`: CSV file containing stock transaction data
- `templates/`: Directory containing HTML templates
- `static/css/`: Directory containing CSS files
- `requirements.txt`: List of Python dependencies

## CSV Format

The application expects a CSV file with the following columns:
- Symbol: Stock ticker symbol
- Name: Company name
- AveragePrice: Purchase/sale price
- Qty: Quantity of shares
- Type: Transaction type (e.g., market, limit)
- Side: Buy or sell
- Fees: Transaction fees
- State: Transaction state (e.g., filled, rejected)
- Date: Transaction date (MM/DD/YYYY)
- Time: Transaction time 