import os
import csv
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, jsonify, flash
import pandas as pd
import sqlite3
import yfinance as yf
import time
from init_db import init_db

# Define MAG7 stocks
MAG7_STOCKS = {
    'AAPL': 'Apple Inc.',
    'MSFT': 'Microsoft Corporation',
    'GOOGL': 'Alphabet Inc.',
    'AMZN': 'Amazon.com Inc.',
    'META': 'Meta Platforms Inc.',
    'NVDA': 'NVIDIA Corporation',
    'TSLA': 'Tesla Inc.'
}

# Cache for stock splits
split_cache = {}
SPLIT_CACHE_TIMEOUT = 86400  # 24 hours

def get_stock_splits(symbol, start_date=None):
    """
    Fetch stock split history for a given symbol.
    Returns a list of tuples (date, ratio) sorted by date.
    """
    cache_key = f"{symbol}:{start_date}"
    
    # Check cache
    if cache_key in split_cache:
        cached_data = split_cache[cache_key]
        if time.time() - cached_data['timestamp'] < SPLIT_CACHE_TIMEOUT:
            return cached_data['data']
    
    try:
        stock = yf.Ticker(symbol)
        
        # Get stock split data
        if start_date:
            splits = stock.splits[start_date:]
        else:
            splits = stock.splits
        
        # Convert to list of tuples (date, ratio)
        split_data = [(date.strftime('%Y-%m-%d'), ratio) for date, ratio in splits.items()]
        split_data.sort(key=lambda x: x[0])  # Sort by date
        
        # Cache the result
        split_cache[cache_key] = {
            'data': split_data,
            'timestamp': time.time()
        }
        
        return split_data
    except Exception as e:
        print(f"Error fetching stock splits for {symbol}: {e}")
        return []

def adjust_for_splits(price, quantity, transaction_date, splits):
    """
    Adjust price and quantity based on stock splits.
    Since yfinance returns split-adjusted prices, we need to:
    - For transactions BEFORE a split: Leave them as is (they're already adjusted by yfinance)
    - For transactions AFTER a split: Multiply price by split ratio, divide quantity by split ratio
    This ensures consistency with yfinance's adjusted prices
    """
    if not splits:
        return price, quantity
    
    transaction_date = datetime.strptime(transaction_date, '%Y-%m-%d').date()
    adjustment_ratio = 1.0
    
    # Sort splits by date to process them in chronological order
    splits.sort(key=lambda x: datetime.strptime(x[0], '%Y-%m-%d').date())
    
    # Only adjust for splits that happened before the transaction
    for split_date, split_ratio in splits:
        split_date = datetime.strptime(split_date, '%Y-%m-%d').date()
        if split_date < transaction_date:
            adjustment_ratio *= split_ratio
    
    if adjustment_ratio != 1.0:
        # For transactions after splits:
        # - Multiply the price by the split ratio (to match historical prices)
        # - Divide the quantity by the split ratio (to reflect historical shares)
        adjusted_price = price * adjustment_ratio
        adjusted_quantity = quantity / adjustment_ratio
        return adjusted_price, adjusted_quantity
    
    return price, quantity

def categorize_stock(symbol, name):
    try:
        # Check if it's a MAG7 stock first (no API call needed)
        if symbol in MAG7_STOCKS:
            return 'mag7'
        
        # Check if stock is still trading
        stock = yf.Ticker(symbol)
        info = stock.info
        
        # Check if we can get any price data
        try:
            # Try multiple price fields as different stocks might use different fields
            price_fields = ['regularMarketPrice', 'currentPrice', 'previousClose', 'open']
            has_price = any(info.get(field) is not None for field in price_fields)
            
            if not has_price:
                return 'unlisted'
            
            return 'other'
        except (KeyError, AttributeError, TypeError):
            return 'unlisted'
            
    except Exception as e:
        print(f"Error categorizing stock {symbol}: {e}")
        # If we can't determine the status, assume it's unlisted
        return 'unlisted'

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Needed for flash messages

# Add more aggressive caching
chart_cache = {}
price_cache = {}
stock_category_cache = {}
CACHE_TIMEOUT = 300  # 5 minutes

# Load the CSV data
def load_data():
    transactions = []
    with open('stock_orders.csv', 'r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            # Convert date string to datetime object for sorting
            row['Date'] = datetime.strptime(row['Date'], '%m/%d/%Y')
            transactions.append(row)
    
    # Sort by Date in descending order (newest first)
    transactions.sort(key=lambda x: x['Date'], reverse=True)
    
    return transactions

# Get unique stocks
def get_unique_stocks(transactions):
    # Get unique stock symbols and names
    stocks = {}
    for transaction in transactions:
        symbol = transaction['Symbol']
        name = transaction['Name']
        if symbol not in stocks:
            stocks[symbol] = name
    
    # Convert to list of tuples and sort alphabetically by Symbol
    stock_list = [(symbol, name) for symbol, name in stocks.items()]
    stock_list.sort(key=lambda x: x[0])
    return stock_list

def get_db_connection():
    conn = sqlite3.connect('stock_transactions.db')
    conn.row_factory = sqlite3.Row
    return conn

def get_categorized_stocks(cursor):
    # Check if we have cached results
    if 'categorized_stocks' in stock_category_cache:
        return stock_category_cache['categorized_stocks']
    
    cursor.execute('SELECT DISTINCT Symbol, Name FROM transactions ORDER BY Symbol')
    all_stocks = cursor.fetchall()
    
    categorized_stocks = {
        'mag7': [],
        'other': [],
        'unlisted': []
    }
    
    for stock in all_stocks:
        category = categorize_stock(stock['Symbol'], stock['Name'])
        categorized_stocks[category].append({
            'symbol': stock['Symbol'],
            'name': stock['Name']
        })
    
    # Cache the results
    stock_category_cache['categorized_stocks'] = categorized_stocks
    return categorized_stocks

def get_stock_price(symbol, start_date=None, end_date=None):
    # Generate cache key
    cache_key = f"{symbol}:{start_date}:{end_date}"
    
    # Check cache
    if cache_key in price_cache:
        cached_data = price_cache[cache_key]
        if time.time() - cached_data['timestamp'] < CACHE_TIMEOUT:
            return cached_data['data']
    
    try:
        stock = yf.Ticker(symbol)
        if start_date and end_date:
            # Get historical data for specific date range
            hist = stock.history(start=start_date, end=end_date)
        elif start_date:
            # Get historical data from start date to now
            hist = stock.history(start=start_date)
        else:
            # Get current price data
            hist = stock.history(period="1d")
        
        if not hist.empty:
            current_price = hist['Close'].iloc[-1]
            previous_close = hist['Close'].iloc[0]
            change = current_price - previous_close
            change_percent = (change / previous_close * 100)
            result = {
                'current_price': current_price,
                'change': change,
                'change_percent': change_percent,
                'previous_close': previous_close,
                'error': None
            }
        else:
            result = {
                'current_price': None,
                'change': None,
                'change_percent': None,
                'previous_close': None,
                'error': 'No price data available'
            }
    except Exception as e:
        print(f"Error fetching stock price: {e}")
        result = {
            'current_price': None,
            'change': None,
            'change_percent': None,
            'previous_close': None,
            'error': str(e)
        }
    
    # Cache the result
    price_cache[cache_key] = {
        'data': result,
        'timestamp': time.time()
    }
    
    return result

def get_stock_chart(symbol, start_date, end_date):
    """
    Get stock chart data and adjust prices to show historical prices.
    yfinance returns split-adjusted prices, so we need to unadjust older prices
    to show the actual historical prices that were seen at the time.
    """
    try:
        stock = yf.Ticker(symbol)
        
        # Get historical data
        hist = stock.history(
            start=start_date,
            end=end_date,
            auto_adjust=True  # This gives us split-adjusted prices
        )
        
        if hist.empty:
            print(f"No historical data found for {symbol}")
            return {
                'dates': [],
                'prices': [],
                'error': 'No historical data found'
            }
        
        # Get the dates and prices
        dates = hist.index.strftime('%Y-%m-%d').tolist()
        prices = hist['Close'].tolist()
        
        # Get splits that occurred in our date range
        splits = get_stock_splits(symbol, start_date.strftime('%Y-%m-%d'))
        print(f"Found splits for {symbol}: {splits}")
        
        if splits:
            # Calculate cumulative split ratio for each date
            # For dates before a split, we need to multiply the price by the split ratio
            # to show the actual historical price
            cumulative_ratios = []
            
            for date in dates:
                date_dt = datetime.strptime(date, '%Y-%m-%d').date()
                # Start with ratio 1
                current_ratio = 1.0
                # For each split that happened after this date,
                # multiply by the split ratio to get the historical price
                for split_date, ratio in splits:
                    split_dt = datetime.strptime(split_date, '%Y-%m-%d').date()
                    if date_dt < split_dt:
                        current_ratio *= ratio
                cumulative_ratios.append(current_ratio)
            
            # Multiply prices by their cumulative ratios to get historical prices
            prices = [price * ratio for price, ratio in zip(prices, cumulative_ratios)]
            
            # Debug output
            print("Sample of price adjustments:")
            for i in range(min(5, len(dates))):
                print(f"Date: {dates[i]}, Ratio: {cumulative_ratios[i]}, Price: {prices[i]}")
        
        # Ensure we have valid data
        if not dates or not prices or len(dates) != len(prices):
            print(f"Invalid data for {symbol}: dates={len(dates)}, prices={len(prices)}")
            return {
                'dates': [],
                'prices': [],
                'error': 'Invalid data received'
            }
        
        # Debug output
        print(f"Chart data for {symbol}:")
        print(f"Date range: {dates[0]} to {dates[-1]}")
        print(f"Price range: ${min(prices):.2f} to ${max(prices):.2f}")
        print(f"Number of points: {len(dates)}")
        
        return {
            'dates': dates,
            'prices': prices,
            'error': None,
            'split_events': [{
                'date': split_date,
                'ratio': ratio,
                'price': next((p for d, p in zip(dates, prices) 
                             if d == split_date), None)
            } for split_date, ratio in splits]
        }
    except Exception as e:
        print(f"Error fetching stock chart for {symbol}: {e}")
        import traceback
        traceback.print_exc()
        return {
            'dates': [],
            'prices': [],
            'error': str(e)
        }

def process_transactions(transactions):
    """Process transactions without any split adjustments"""
    processed = []
    for t in transactions:
        try:
            date_obj = datetime.strptime(t['Date'], '%Y-%m-%d')
            price = float(t['AveragePrice'])
            qty = float(t['Qty'])
            
            processed.append({
                'Id': t['Id'],
                'Date': date_obj,
                'Time': t['Time'],
                'Symbol': t['Symbol'],
                'Name': t['Name'],
                'Type': t['Type'],
                'Side': t['Side'],
                'AveragePrice': price,
                'Qty': qty,
                'State': t['State'],
                'Fees': t['Fees'],
                'HasSplitAdjustment': False
            })
        except (ValueError, TypeError) as e:
            print(f"Error processing transaction: {t}, Error: {e}")
            processed.append({
                'Id': t['Id'],
                'Date': date_obj,
                'Time': t['Time'],
                'Symbol': t['Symbol'],
                'Name': t['Name'],
                'Type': t['Type'],
                'Side': t['Side'],
                'AveragePrice': t['AveragePrice'],
                'Qty': t['Qty'],
                'State': t['State'],
                'Fees': t['Fees'],
                'HasSplitAdjustment': False
            })
    
    return processed

def calculate_transaction_stats(transactions):
    stats = {
        'total_stocks_bought': 0,
        'total_stocks_sold': 0,
        'total_amount_bought': 0,
        'total_amount_sold': 0
    }
    
    for tx in transactions:
        try:
            # Use adjusted quantities and prices for calculations
            qty = float(tx['Qty'])
            price = float(tx['AveragePrice'])
            amount = price * qty
            
            if tx['Side'].lower() == 'buy':
                stats['total_stocks_bought'] += qty
                stats['total_amount_bought'] += amount
            elif tx['Side'].lower() == 'sell':
                stats['total_stocks_sold'] += qty
                stats['total_amount_sold'] += amount
        except (ValueError, TypeError) as e:
            print(f"Error processing transaction stats: {tx}, Error: {e}")
            continue
    
    # Round the values for display
    stats['total_stocks_bought'] = round(stats['total_stocks_bought'], 2)
    stats['total_stocks_sold'] = round(stats['total_stocks_sold'], 2)
    stats['total_amount_bought'] = round(stats['total_amount_bought'], 2)
    stats['total_amount_sold'] = round(stats['total_amount_sold'], 2)
    
    return stats

@app.route('/api/stock_chart/<symbol>')
def api_stock_chart(symbol):
    range_ = request.args.get('range', 'ytd')
    today = datetime.today()
    
    # Get transactions for this symbol
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if range_ == 'all':
        # For 'all', get the date range from actual transactions
        cursor.execute('''
            SELECT MIN(Date), MAX(Date) 
            FROM transactions 
            WHERE Symbol = ?
        ''', (symbol,))
        min_date, max_date = cursor.fetchone()
        if min_date and max_date:
            start_date = datetime.strptime(min_date, '%Y-%m-%d')
            end_date = datetime.strptime(max_date, '%Y-%m-%d') + timedelta(days=1)  # Include the last day
        else:
            start_date = today - timedelta(days=30)  # Default to last 30 days if no transactions
            end_date = today
    elif range_ == 'ytd':
        start_date = datetime(today.year, 1, 1)
        end_date = today
    elif range_ == '1y':
        start_date = today - timedelta(days=365)
        end_date = today
    elif range_ == '2y':
        start_date = today - timedelta(days=2*365)
        end_date = today
    elif range_ == '5y':
        start_date = today - timedelta(days=5*365)
        end_date = today
    elif range_ == 'max':
        # For max, get the earliest transaction date
        cursor.execute('SELECT MIN(Date) FROM transactions WHERE Symbol = ?', (symbol,))
        earliest_date = cursor.fetchone()[0]
        if earliest_date:
            start_date = datetime.strptime(earliest_date, '%Y-%m-%d')
        else:
            start_date = today - timedelta(days=365)  # Default to 1 year if no transactions
        end_date = today
    else:  # Default to YTD if unknown range
        start_date = datetime(today.year, 1, 1)
        end_date = today
    
    # Get transactions within the date range
    query = '''
        SELECT Id, Date, Time, Side, AveragePrice, Qty 
        FROM transactions 
        WHERE Symbol = ? AND Date >= ? AND Date <= ?
        ORDER BY Date ASC, Time ASC
    '''
    cursor.execute(query, (symbol, start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')))
    transactions = cursor.fetchall()
    conn.close()
    
    # Process transactions for charting
    buy_transactions = []
    sell_transactions = []
    
    for tx in transactions:
        if not tx['AveragePrice']:
            continue
        try:
            price = float(tx['AveragePrice'])
            point = {
                'id': tx['Id'],
                'date': tx['Date'],
                'time': tx['Time'],
                'price': price,
                'qty': tx['Qty']
            }
            if tx['Side'].lower() == 'buy':
                buy_transactions.append(point)
            else:
                sell_transactions.append(point)
        except (ValueError, TypeError) as e:
            print(f"Error processing transaction: {tx}, Error: {e}")
            continue
    
    # Get chart data for the specified date range
    chart_data = get_stock_chart(symbol, start_date, end_date)
    
    # Get split data
    splits = get_stock_splits(symbol, start_date.strftime('%Y-%m-%d'))
    split_events = []
    
    # Process splits for chart annotations
    for split_date, split_ratio in splits:
        split_date_obj = datetime.strptime(split_date, '%Y-%m-%d')
        if start_date <= split_date_obj <= end_date:
            # Find the closest price to the split date
            closest_date_index = min(range(len(chart_data['dates'])), 
                                   key=lambda i: abs(datetime.strptime(chart_data['dates'][i], '%Y-%m-%d') - split_date_obj))
            
            if closest_date_index < len(chart_data['prices']):
                price = chart_data['prices'][closest_date_index]
                split_events.append({
                    'date': split_date,
                    'ratio': split_ratio,
                    'price': price
                })
    
    # Add split events to chart data
    chart_data['split_events'] = split_events
    
    # Add transaction data
    chart_data['buy_transactions'] = buy_transactions
    chart_data['sell_transactions'] = sell_transactions
    
    # Cache the data
    cache_key = f"{symbol}:{range_}"
    now = time.time()
    chart_cache[cache_key] = {'data': {
        'dates': chart_data['dates'],
        'prices': chart_data['prices'],
        'error': chart_data['error']
    }, 'timestamp': now}
    
    return jsonify(chart_data)

@app.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    per_page = 20
    active_tab = request.args.get('tab', 'mag7')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM transactions')
    total_transactions = cursor.fetchone()[0]
    total_pages = (total_transactions + per_page - 1) // per_page
    offset = (page - 1) * per_page
    cursor.execute('''
        SELECT * FROM transactions 
        ORDER BY Date DESC, Time DESC 
        LIMIT ? OFFSET ?
    ''', (per_page, offset))
    transactions = cursor.fetchall()
    cursor.execute('''
        SELECT DISTINCT Symbol, Name 
        FROM transactions 
        ORDER BY Symbol
    ''')
    stocks = cursor.fetchall()
    conn.close()
    
    # Categorize stocks
    categorized_stocks = {
        'mag7': [],
        'other': [],
        'unlisted': []
    }
    
    for stock in stocks:
        category = categorize_stock(stock['Symbol'], stock['Name'])
        categorized_stocks[category].append({
            'symbol': stock['Symbol'],
            'name': stock['Name']
        })
    
    processed_transactions = process_transactions(transactions)
    return render_template('index.html', 
                         transactions=processed_transactions,
                         stocks=categorized_stocks,
                         page=page,
                         total_pages=total_pages,
                         current_filter=None,
                         active_tab=active_tab)

@app.route('/stock/<symbol>')
def stock_detail(symbol):
    page = request.args.get('page', 1, type=int)
    per_page = 20
    side = request.args.get('side', 'all')
    range_ = request.args.get('range', 'ytd')
    active_tab = request.args.get('tab', 'mag7')
    
    today = datetime.today()
    start_date = None
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get the stock name and transactions in a single query
    cursor.execute('''
        SELECT t.*, 
               (SELECT DISTINCT Name FROM transactions WHERE Symbol = ? LIMIT 1) as stock_name
        FROM transactions t
        WHERE t.Symbol = ?
    ''', (symbol, symbol))
    result = cursor.fetchone()
    stock_name = result['stock_name']
    
    # Build the base query for transactions
    base_query = 'SELECT * FROM transactions WHERE Symbol = ?'
    params = [symbol]
    
    # Handle side filter
    if side in ['buy', 'sell']:
        base_query += ' AND LOWER(Side) = ?'
        params.append(side)
    
    # Handle date range
    if range_ == 'all':
        # For 'all' filter, we want all transactions without date filtering
        pass
    elif range_ == 'max':
        # For 'max' filter, we want the entire stock history
        # Get the earliest transaction date
        cursor.execute('SELECT MIN(Date) FROM transactions WHERE Symbol = ?', (symbol,))
        earliest_date = cursor.fetchone()[0]
        if earliest_date:
            start_date = datetime.strptime(earliest_date, '%Y-%m-%d')
    elif range_ == 'ytd':
        start_date = datetime(today.year, 1, 1)
    elif range_ == '1y':
        start_date = today - timedelta(days=365)
    elif range_ == '2y':
        start_date = today - timedelta(days=2*365)
    elif range_ == '5y':
        start_date = today - timedelta(days=5*365)
    elif range_ == '1mo':
        start_date = today - timedelta(days=30)
    
    # Add date filter if needed
    if start_date and range_ != 'all':
        base_query += ' AND Date >= ?'
        params.append(start_date.strftime('%Y-%m-%d'))
    
    # Get total count for pagination
    count_query = f'SELECT COUNT(*) FROM ({base_query})'
    cursor.execute(count_query, params)
    total_transactions = cursor.fetchone()[0]
    total_pages = (total_transactions + per_page - 1) // per_page
    
    # Ensure page is within valid range
    if page < 1:
        page = 1
    elif page > total_pages and total_pages > 0:
        page = total_pages
    
    # Calculate offset for pagination
    offset = (page - 1) * per_page
    
    # First get all transactions for stats (without pagination)
    cursor.execute(base_query, params)
    all_transactions = cursor.fetchall()
    
    # Calculate stats from all transactions
    transaction_stats = calculate_transaction_stats(all_transactions)
    
    # Add pagination to the query for display
    final_query = f'{base_query} ORDER BY Date DESC, Time DESC LIMIT ? OFFSET ?'
    params += [per_page, offset]
    
    # Execute the final query
    cursor.execute(final_query, params)
    transactions = cursor.fetchall()
    
    # Get categorized stocks from cache
    categorized_stocks = get_categorized_stocks(cursor)
    
    conn.close()
    
    processed_transactions = process_transactions(transactions)
    
    # Get price data with appropriate date range
    if range_ == 'all':
        # For 'all' filter, we want to show price data for transaction dates only
        # Get unique transaction dates
        transaction_dates = sorted(set(t['Date'] for t in all_transactions))
        if transaction_dates:
            start_date = datetime.strptime(transaction_dates[0], '%Y-%m-%d')
            end_date = datetime.strptime(transaction_dates[-1], '%Y-%m-%d')
            price_data = get_stock_price(symbol, start_date=start_date, end_date=end_date)
        else:
            price_data = get_stock_price(symbol)
    else:
        price_data = get_stock_price(symbol, start_date=start_date)
    
    return render_template('index.html', 
                         transactions=processed_transactions,
                         stocks=categorized_stocks,
                         current_filter=symbol,
                         stock_name=stock_name,
                         page=page,
                         total_pages=total_pages,
                         price_data=price_data,
                         selected_side=side,
                         selected_range=range_,
                         active_tab=active_tab,
                         transaction_stats=transaction_stats)

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        flash('No file selected', 'error')
        return redirect(url_for('index'))
    
    file = request.files['file']
    if file.filename == '':
        flash('No file selected', 'error')
        return redirect(url_for('index'))
    
    if not file.filename.endswith('.csv'):
        flash('Please upload a CSV file', 'error')
        return redirect(url_for('index'))
    
    # Save the file
    file.save('stock_orders.csv')
    
    try:
        # Reinitialize the database with the new file
        init_db()
        flash('File uploaded and processed successfully!', 'success')
    except Exception as e:
        flash(f'Error processing file: {str(e)}', 'error')
        # Clean up the uploaded file
        if os.path.exists('stock_orders.csv'):
            os.remove('stock_orders.csv')
    
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True) 