import os
import csv
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, jsonify, flash
import pandas as pd
import sqlite3
import yfinance as yf
import time
from init_db import init_db
from openai import OpenAI
import openai
from dotenv import load_dotenv

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

# Load environment variables
load_dotenv()

# Initialize OpenAI client
openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# Initialize Perplexity client (fallback)
perplexity_client = None
if os.getenv('PERPLEXITY_API_KEY'):
    perplexity_client = OpenAI(
        api_key=os.getenv('PERPLEXITY_API_KEY'),
        base_url="https://api.perplexity.ai"
    )

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

@app.route('/api/chat', methods=['POST'])
def chat():
    """API endpoint to process chat messages and return responses using ChatGPT API"""
    data = request.get_json()
    message = data.get('message', '')
    current_stock = data.get('stock', None)  # Get the current stock from the request
    
    # Check if we're just checking API availability
    if message == 'check_api':
        openai_available = bool(os.getenv('OPENAI_API_KEY'))
        perplexity_available = bool(os.getenv('PERPLEXITY_API_KEY'))
        return jsonify({
            "openai_available": openai_available,
            "perplexity_available": perplexity_available,
            "api_available": openai_available or perplexity_available
        })
    
    if not message:
        return jsonify({"response": "Please enter a message."})
    
    # Get application context to provide to AI models
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM transactions')
    total_transactions = cursor.fetchone()[0]
    cursor.execute('SELECT DISTINCT Symbol FROM transactions')
    symbols = [row['Symbol'] for row in cursor.fetchall()]
    
    # Stock-specific context if the user is viewing a stock page
    stock_specific_context = ""
    if current_stock:
        # Get current stock price and recent performance
        price_data = get_stock_price(current_stock)
        
        # Get transactions for this specific stock
        cursor.execute('''
            SELECT * FROM transactions 
            WHERE Symbol = ? 
            ORDER BY Date DESC, Time DESC
        ''', (current_stock,))
        stock_transactions = cursor.fetchall()
        
        # Calculate stats for this stock
        stats = calculate_transaction_stats(stock_transactions)
        
        # Calculate average buy/sell prices
        total_buy_amount = 0
        total_buy_qty = 0
        total_sell_amount = 0
        total_sell_qty = 0
        
        for tx in stock_transactions:
            try:
                qty = float(tx['Qty'])
                price = float(tx['AveragePrice'])
                amount = price * qty
                
                if tx['Side'].lower() == 'buy':
                    total_buy_amount += amount
                    total_buy_qty += qty
                elif tx['Side'].lower() == 'sell':
                    total_sell_amount += amount
                    total_sell_qty += qty
            except (ValueError, TypeError):
                continue
        
        avg_buy_price = total_buy_amount / total_buy_qty if total_buy_qty > 0 else 0
        avg_sell_price = total_sell_amount / total_sell_qty if total_sell_qty > 0 else 0
        
        # Get the first and last transaction dates
        cursor.execute('''
            SELECT MIN(Date), MAX(Date) FROM transactions 
            WHERE Symbol = ?
        ''', (current_stock,))
        first_date, last_date = cursor.fetchone()
        
        # Create stock-specific context
        current_price = price_data.get('current_price', 'Unknown')
        change_percent = price_data.get('change_percent', 'Unknown')
        
        # Format the change percentage correctly
        if isinstance(change_percent, (int, float)):
            change_percent_display = f"{change_percent:.2f}%"
        else:
            change_percent_display = "Unknown"
        
        stock_specific_context = f"""
        The user is currently viewing the {current_stock} stock page.
        
        Stock details:
        - Current price: ${current_price if current_price != 'Unknown' else 'Unknown'}
        - Today's change: {change_percent_display}
        - User's average buy price: ${avg_buy_price:.2f}
        - User's average sell price: ${avg_sell_price:.2f}
        - First transaction: {first_date}
        - Most recent transaction: {last_date}
        - Total shares bought: {stats['total_stocks_bought']}
        - Total shares sold: {stats['total_stocks_sold']}
        - Net shares: {stats['total_stocks_bought'] - stats['total_stocks_sold']}
        
        The user may want recommendations about:
        1. Is it the right time to buy {current_stock} based on their transaction history and current price
        2. Whether they have made impulse buys or panic sells with this stock
        3. Analysis of their trading pattern with {current_stock}
        """
    
    conn.close()
    
    context = f"""
    You are a helpful assistant for a stock transactions analyzer application.
    The app allows users to analyze their stock portfolio and transactions.
    
    Key application features:
    - View stock transactions with filtering options (buy/sell, date ranges)
    - Charts showing stock price history and transaction points
    - MAG7 stocks section (Apple, Microsoft, Google, Amazon, Meta, NVIDIA, Tesla)
    - Other stocks section
    - Unlisted stocks section
    
    The user has {total_transactions} total stock transactions in their portfolio.
    Their portfolio includes stocks like: {', '.join(symbols[:10])}
    
    {stock_specific_context}
    
    Keep your responses concise, focused on stocks and the application features.
    If the user asks about buy timing or trading patterns for the current stock, provide personalized insights based on their transaction history.
    """
    
    # Try OpenAI first if available
    if os.getenv('OPENAI_API_KEY'):
        try:
            # Call OpenAI API
            response = openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": context},
                    {"role": "user", "content": message}
                ],
                max_tokens=1000,  # Increased from 300 to 1000
                temperature=0.7,
                presence_penalty=0.6,  # Add presence penalty to encourage complete responses
                frequency_penalty=0.2,  # Add frequency penalty
                stream=False  # Ensure we get complete responses
            )
            
            # Extract the response text
            chat_response = response.choices[0].message.content.strip()
            return jsonify({"response": chat_response, "provider": "openai"})
            
        except (openai.RateLimitError, openai.APIError) as e:
            print(f"OpenAI API error (possibly rate limit): {str(e)}")
            # Check if we have Perplexity as a fallback
            if perplexity_client:
                print("Falling back to Perplexity API...")
                # Continue to Perplexity fallback
            else:
                # No Perplexity fallback, use simple chat
                print("No Perplexity fallback available, using simple chat")
                return handle_simple_chat(message, current_stock)
                
        except Exception as e:
            print(f"Error calling OpenAI API: {str(e)}")
            if perplexity_client:
                print("Falling back to Perplexity API due to general error...")
                # Continue to Perplexity fallback
            else:
                # Fallback to simple response if API fails
                return handle_simple_chat(message, current_stock)
    
    # Try Perplexity if OpenAI failed or isn't available
    if perplexity_client:
        try:
            # Call Perplexity API using the OpenAI client interface
            response = perplexity_client.chat.completions.create(
                model="llama-3.1-sonar-small-128k-online",  # Use an appropriate Perplexity model
                messages=[
                    {"role": "system", "content": context},
                    {"role": "user", "content": message}
                ],
                max_tokens=300
            )
            
            # Extract the response text
            chat_response = response.choices[0].message.content.strip()
            return jsonify({"response": chat_response, "provider": "perplexity"})
            
        except Exception as e:
            print(f"Error calling Perplexity API: {str(e)}")
            # Fallback to simple response if both APIs fail
            return handle_simple_chat(message, current_stock)
    
    # If we got here, neither API is available or both failed
    return handle_simple_chat(message, current_stock)

def handle_simple_chat(message, current_stock=None):
    """Fallback to simple responses if API is not available"""
    message = message.lower()
    
    # Stock-specific recommendations if user is viewing a stock page
    if current_stock and ('time to buy' in message or 'right time' in message or 'good buy' in message):
        return jsonify({
            "response": f"Without access to real-time market data, I can't provide specific buy recommendations for {current_stock}. Consider checking the price chart and your transaction history to identify your own patterns. You might also want to research recent news about {current_stock} before making any decisions."
        })
    
    if current_stock and ('impulse' in message or 'panic' in message or 'emotion' in message or 'pattern' in message):
        return jsonify({
            "response": f"To analyze your trading patterns with {current_stock}, I'd need to evaluate your transaction timing and price points. Look at your transaction history - do you see a pattern of buying at peaks or selling at lows? Consider enabling API access for more personalized insights on your trading patterns."
        })
    
    # Simple response logic based on keywords
    if 'hello' in message or 'hi' in message:
        response = "Hello! How can I help you with your stock portfolio today?"
    elif 'help' in message:
        response = "I can help you analyze your stock transactions. Try asking about specific stocks, transaction history, or general market information."
    elif any(word in message for word in ['stock', 'stocks', 'portfolio']):
        response = "Your portfolio contains various stocks. You can view detailed information by clicking on specific stocks in the main view."
    elif any(word in message for word in ['transaction', 'transactions', 'history']):
        response = "Your transaction history is displayed in the main table. You can filter by stock, transaction type, and date range."
    elif 'mag7' in message or 'magnificent 7' in message:
        response = "The Magnificent Seven (MAG7) are: Apple (AAPL), Microsoft (MSFT), Alphabet/Google (GOOGL), Amazon (AMZN), Meta/Facebook (META), NVIDIA (NVDA), and Tesla (TSLA)."
    elif 'chart' in message or 'graph' in message:
        response = "Charts are displayed when you select a specific stock. They show price history and your buy/sell transactions."
    elif 'filter' in message:
        response = "You can filter transactions by stock symbol, transaction type (buy/sell), and date range using the buttons above the transaction table."
    elif 'buy' in message or 'sell' in message:
        response = "Your buy and sell transactions are color-coded in the transaction table. You can also filter to show only buys or sells."
    elif 'clear' in message:
        response = "You can clear our conversation by clicking the trash icon in the top-right corner of this chat window."
    elif 'thanks' in message or 'thank you' in message:
        response = "You're welcome! Let me know if you have any other questions."
    elif 'bye' in message or 'goodbye' in message:
        response = "Goodbye! Feel free to chat again if you have more questions."
    else:
        response = "I'm sorry, I don't have specific information about that. Try asking about your stock portfolio, transactions, or how to use this application."
    
    return jsonify({"response": response})


if __name__ == '__main__':
    # Make sure the database exists
    init_db()
    app.run(debug=True) 