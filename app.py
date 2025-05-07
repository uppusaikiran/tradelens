import os
import csv
import json
import uuid
import logging
import traceback
import sys
import time
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, jsonify, flash, session, send_from_directory
import pandas as pd
import sqlite3
import yfinance as yf
import time
from init_db import init_db
from openai import OpenAI
import openai
from dotenv import load_dotenv
import threading
import markdown
import requests
from itertools import groupby
from dateutil.relativedelta import relativedelta
import shutil
from concurrent.futures import ThreadPoolExecutor, TimeoutError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('app.log')
    ]
)
logger = logging.getLogger('tradelens')

# Create the logo storage directory if it doesn't exist
LOGO_DIR = os.path.join('static', 'img', 'logos')
os.makedirs(LOGO_DIR, exist_ok=True)

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

# Define Perplexity AI model options
PERPLEXITY_MODELS = {
    'sonar': 'sonar',
    'sonar-pro': 'sonar-pro',
    'sonar-reasoning': 'sonar-reasoning',
    'sonar-reasoning-pro': 'sonar-reasoning-pro',
    'sonar-deep-research': 'sonar-deep-research',
    'r1-1776': 'r1-1776',
    'llama-3.1-sonar-small': 'llama-3.1-sonar-small'
}

# Investment thesis examples for dropdown
INVESTMENT_THESES = [
    "AI stocks will outperform in Q3 2025",
    "Renewable energy sector will see growth due to recent policy changes",
    "Semiconductor stocks will face headwinds from supply chain disruptions",
    "Fintech companies will benefit from rising interest rates",
    "Healthcare innovation stocks will outperform due to aging demographics",
    "E-commerce stocks will decline with return to brick-and-mortar shopping",
    "Cybersecurity stocks will surge due to increased corporate spending",
    "Small-cap stocks will outperform large-caps in the next fiscal year",
    "Cloud computing providers will face margin pressure from competition",
    "Electric vehicle stocks will underperform due to raw material costs"
]

# Set default model
DEFAULT_PERPLEXITY_MODEL = 'sonar'

# Load environment variables from .env file
load_dotenv()

# Get OpenAI API key
openai_api_key = os.getenv('OPENAI_API_KEY')

# Initialize OpenAI client
openai_client = OpenAI(api_key=openai_api_key)

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

# Set default settings
DEFAULT_SETTINGS = {
    'ai_provider': 'perplexity',  # 'openai' or 'perplexity'
    'perplexity_model': 'sonar'   # Default Perplexity model
}

# Function to get current settings
def get_settings():
    try:
        # Check if we have a Flask request context
        if 'settings' not in session:
            session['settings'] = DEFAULT_SETTINGS.copy()
        return session['settings']
    except RuntimeError:
        # If there's no request context, return default settings
        logger.warning("No request context available for settings, using defaults")
        return DEFAULT_SETTINGS.copy()

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
app.secret_key = os.getenv('SECRET_KEY', 'dev_secret_key_change_in_production')

# Add custom Jinja2 filter for strptime
@app.template_filter('strptime')
def strptime_filter(date_str, format_str):
    """Convert a date string to a datetime object using the given format"""
    return datetime.strptime(date_str, format_str)

# Add custom Jinja2 filter for strftime
@app.template_filter('strftime')
def strftime_filter(date_obj, format_str):
    """Format a datetime object as a string using the given format"""
    return date_obj.strftime(format_str)

# Add markdown filter for rendering markdown content
@app.template_filter('markdown')
def markdown_filter(text):
    """Convert markdown text to HTML"""
    try:
        # Install markdown package if not present
        import markdown
        return markdown.markdown(text)
    except ImportError:
        # Fallback if markdown package is not installed
        return text.replace('\n', '<br>')

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
    
    # Add custom converter functions to handle TEXT to numeric conversions
    def convert_to_float(value):
        if value is None or value == "null" or value == "":
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None
    
    # Register adapter and converter for REAL type
    sqlite3.register_adapter(float, lambda val: str(val))
    sqlite3.register_converter("REAL", convert_to_float)
    
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
            # Convert date string to datetime object
            date_obj = datetime.strptime(t['Date'], '%Y-%m-%d') if isinstance(t['Date'], str) else t['Date']
            
            # Convert text values to float, handling possible null values
            try:
                price = float(t['AveragePrice']) if t['AveragePrice'] and str(t['AveragePrice']).lower() != 'null' else None
            except (ValueError, TypeError, AttributeError):
                price = None
                
            try:
                qty = float(t['Qty']) if t['Qty'] and str(t['Qty']).lower() != 'null' else None
            except (ValueError, TypeError, AttributeError):
                qty = None
            
            processed.append({
                'Id': t['Id'],
                'Date': date_obj,
                'Time': t['Time'],
                'Symbol': t['Symbol'],
                'Name': t['Name'],
                'Type': t['Type'],
                'Side': t['Side'],
                'AveragePrice': price,  # Always use the converted float or None
                'Qty': qty,
                'State': t['State'],
                'Fees': t['Fees'],
                'HasSplitAdjustment': False
            })
        except (ValueError, TypeError) as e:
            print(f"Error processing transaction: {t}, Error: {e}")
            # Even in error case, try to convert price and quantity
            try:
                price = float(t['AveragePrice']) if t['AveragePrice'] and str(t['AveragePrice']).lower() != 'null' else None
            except (ValueError, TypeError, AttributeError):
                price = None
                
            try:
                qty = float(t['Qty']) if t['Qty'] and str(t['Qty']).lower() != 'null' else None
            except (ValueError, TypeError, AttributeError):
                qty = None
                
            processed.append({
                'Id': t['Id'],
                'Date': date_obj if 'date_obj' in locals() else None,
                'Time': t['Time'],
                'Symbol': t['Symbol'],
                'Name': t['Name'],
                'Type': t['Type'],
                'Side': t['Side'],
                'AveragePrice': price,  # Use converted float or None, not raw string
                'Qty': qty,
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
            # Safely convert text values to float
            try:
                qty = float(tx['Qty']) if tx['Qty'] and str(tx['Qty']).lower() != 'null' else 0
            except (ValueError, TypeError):
                qty = 0
                
            try:
                price = float(tx['AveragePrice']) if tx['AveragePrice'] and str(tx['AveragePrice']).lower() != 'null' else 0
            except (ValueError, TypeError):
                price = 0
                
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
        try:
            # Safely convert AveragePrice to float
            if tx['AveragePrice'] is None or (isinstance(tx['AveragePrice'], str) and (not tx['AveragePrice'] or tx['AveragePrice'].lower() == 'null')):
                continue
                
            try:
                price = float(tx['AveragePrice'])
            except (ValueError, TypeError):
                continue
                
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
                         per_page=per_page,
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
    
    # Handle case where no transactions are found for this symbol
    if result is None:
        flash(f"No transactions found for symbol {symbol}", "warning")
        return redirect(url_for('index'))
        
    # Get stock name with a fallback if not found
    stock_name = result['stock_name'] if result and result['stock_name'] else symbol
    
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
                         per_page=per_page,
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
        
        # Populate earnings calendar data to ensure it's not empty
        try:
            from populate_earnings_data import populate_sample_earnings_data
            populate_sample_earnings_data()
            flash('File uploaded and database processed successfully! Earnings calendar has been refreshed.', 'success')
        except Exception as e:
            flash(f'File uploaded, but error refreshing earnings data: {str(e)}', 'warning')
            
    except Exception as e:
        flash(f'Error processing file: {str(e)}', 'error')
        # Clean up the uploaded file
        if os.path.exists('stock_orders.csv'):
            os.remove('stock_orders.csv')
    
    return redirect(url_for('index'))

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    """Route to display and update application settings"""
    if request.method == 'POST':
        # Update settings
        settings = get_settings()
        
        # Update AI provider
        settings['ai_provider'] = request.form.get('ai_provider', 'perplexity')
        
        # Update Perplexity model if applicable
        if settings['ai_provider'] == 'perplexity':
            perplexity_model = request.form.get('perplexity_model')
            if perplexity_model in PERPLEXITY_MODELS:
                settings['perplexity_model'] = perplexity_model
        
        # Save settings to session
        session['settings'] = settings
        
        # Redirect back to settings page with success message
        flash('Settings updated successfully!', 'success')
        return redirect(url_for('settings'))
    
    # GET method
    settings = get_settings()
    
    # Check API availability
    openai_available = bool(os.getenv('OPENAI_API_KEY'))
    perplexity_available = bool(os.getenv('PERPLEXITY_API_KEY'))
    
    return render_template('settings.html', 
                           settings=settings,
                           perplexity_models=list(PERPLEXITY_MODELS.keys()),
                           openai_available=openai_available,
                           perplexity_available=perplexity_available)

@app.route('/risk-review')
def risk_review():
    """Portfolio risk review page that analyzes tariff and other risks for current holdings."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get current portfolio positions by aggregating buy/sell transactions
    cursor.execute('''
        SELECT 
            Symbol, 
            Name,
            SUM(CASE WHEN Side = 'buy' THEN Qty ELSE -Qty END) as CurrentShares,
            SUM(CASE WHEN Side = 'buy' THEN Qty * AveragePrice ELSE -Qty * AveragePrice END) as TotalInvestment
        FROM 
            transactions
        GROUP BY 
            Symbol
        HAVING 
            CurrentShares > 0
        ORDER BY 
            CurrentShares * 
            (SELECT AveragePrice FROM transactions 
             WHERE Symbol = transactions.Symbol 
             ORDER BY Date DESC, Time DESC LIMIT 1) DESC
    ''')
    
    portfolio = cursor.fetchall()
    
    # Get the latest stock prices and calculate portfolio metrics
    current_prices = {}
    sectors = {}
    tariff_impacts = {}
    average_costs = {}
    unrealized_gains = {}
    
    # Portfolio summary metrics
    portfolio_summary = {
        'total_value': 0,
        'total_investment': 0,
        'total_gain_loss': 0,
        'total_gain_loss_percentage': 0,
        'total_shares': 0,
        'total_stocks': len(portfolio)
    }
    
    for stock in portfolio:
        symbol = stock['Symbol']
        current_shares = stock['CurrentShares']
        total_investment = stock['TotalInvestment']
        
        # Calculate average cost
        if current_shares > 0:
            average_cost = total_investment / current_shares
            average_costs[symbol] = average_cost
        else:
            average_cost = 0
            average_costs[symbol] = 0
        
        try:
            # Get latest price
            price_data = get_stock_price(symbol)
            if price_data and 'current_price' in price_data and price_data['current_price'] is not None:
                current_price = price_data['current_price']
                current_prices[symbol] = current_price
                
                # Calculate position value and gain/loss
                position_value = current_shares * current_price
                unrealized_gain = position_value - total_investment
                unrealized_gains[symbol] = {
                    'amount': unrealized_gain,
                    'percentage': (unrealized_gain / total_investment * 100) if total_investment > 0 else 0
                }
                
                # Add to portfolio totals
                portfolio_summary['total_value'] += position_value
                portfolio_summary['total_investment'] += total_investment
                portfolio_summary['total_shares'] += current_shares
            else:
                current_prices[symbol] = None
                unrealized_gains[symbol] = {'amount': 0, 'percentage': 0}
                
            # Get sector info
            sectors[symbol] = get_stock_sector(symbol)
            
            # Get tariff impact assessment
            tariff_impacts[symbol] = assess_tariff_risk(symbol, sectors[symbol])
            
        except Exception as e:
            print(f"Error getting data for {symbol}: {e}")
            current_prices[symbol] = None
            sectors[symbol] = "Unknown"
            unrealized_gains[symbol] = {'amount': 0, 'percentage': 0}
            tariff_impacts[symbol] = {
                "risk_level": "Unknown",
                "risk_score": 0.5,
                "assessment": "Could not assess tariff risk for this stock."
            }
    
    # Calculate total gain/loss for portfolio
    if portfolio_summary['total_investment'] > 0:
        portfolio_summary['total_gain_loss'] = portfolio_summary['total_value'] - portfolio_summary['total_investment']
        portfolio_summary['total_gain_loss_percentage'] = (portfolio_summary['total_gain_loss'] / portfolio_summary['total_investment']) * 100
    
    # Calculate simplified risk metrics to avoid using .get() method
    risk_metrics = {
        "overall_risk_level": "Medium",
        "overall_risk_score": 0.6,
        "sector_diversification_score": 0.4,
        "high_risk_percentage": 35.0,
        "recommendation": "Consider diversifying away from high-tariff-risk sectors or specific companies particularly vulnerable to trade tensions."
    }
    
    # Close connection
    conn.close()
    
    return render_template('risk_review.html', 
                           portfolio=portfolio, 
                           current_prices=current_prices,
                           sectors=sectors,
                           tariff_impacts=tariff_impacts,
                           risk_metrics=risk_metrics,
                           average_costs=average_costs,
                           unrealized_gains=unrealized_gains,
                           portfolio_summary=portfolio_summary,
                           risk_analysis_date=datetime.now().strftime('%Y-%m-%d'),
                           settings=get_settings())

@app.route('/strategy-backtesting')
def strategy_backtesting():
    """Strategy backtesting page that allows users to analyze historical performance."""
    # Prepare backtesting presets
    backtesting_presets = [
        {
            "id": "macro_impact_sp500_2020",
            "name": "Summarize macro economic events that impacted S&P500 between Jan-May 2020",
            "prompt": "Summarize the major macroeconomic events that impacted the S&P500 between January and May 2020. Focus on key market-moving events, policy responses, and their impact on market performance."
        },
        {
            "id": "covid_recovery_tech",
            "name": "Analyze tech sector performance during COVID recovery (2020-2021)",
            "prompt": "Analyze how the technology sector performed during the COVID recovery period from March 2020 through December 2021. Include key trends, notable outperformers, and factors that drove the sector's performance."
        },
        {
            "id": "interest_rate_impact_2022",
            "name": "Interest rate impacts on growth stocks in 2022",
            "prompt": "Analyze how the Federal Reserve's interest rate hikes in 2022 impacted growth stocks. Compare performance before and after key rate decisions and identify which subsectors were most affected."
        },
        {
            "id": "banking_crisis_2023",
            "name": "Banking sector crisis impact on markets (March 2023)",
            "prompt": "Analyze the banking sector crisis of March 2023 (Silicon Valley Bank, Signature Bank, etc.) and its impact on broader market indices. What were the warning signs, policy responses, and how did different sectors react?"
        },
        {
            "id": "ai_stocks_performance",
            "name": "AI stock performance since ChatGPT launch (Nov 2022)",
            "prompt": "Analyze the performance of AI-related stocks since the public launch of ChatGPT in November 2022. Which companies saw the biggest gains, what were key catalysts, and how did this compare to broader technology indices?"
        }
    ]
    
    # Get current portfolio data to show relevant stocks
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get current portfolio positions by aggregating buy/sell transactions
    cursor.execute('''
        SELECT 
            Symbol, 
            Name,
            SUM(CASE WHEN Side = 'buy' THEN Qty ELSE -Qty END) as CurrentShares,
            SUM(CASE WHEN Side = 'buy' THEN Qty * AveragePrice ELSE -Qty * AveragePrice END) as TotalInvestment
        FROM 
            transactions
        GROUP BY 
            Symbol
        HAVING 
            CurrentShares > 0
        ORDER BY 
            CurrentShares * 
            (SELECT AveragePrice FROM transactions 
             WHERE Symbol = transactions.Symbol 
             ORDER BY Date DESC, Time DESC LIMIT 1) DESC
    ''')
    
    portfolio = cursor.fetchall()
    
    # Get current prices for portfolio holdings
    current_prices = {}
    for stock in portfolio:
        symbol = stock['Symbol']
        try:
            price_data = get_stock_price(symbol)
            if price_data and 'current_price' in price_data and price_data['current_price'] is not None:
                current_prices[symbol] = price_data['current_price']
            else:
                current_prices[symbol] = None
        except Exception as e:
            print(f"Error getting price for {symbol}: {e}")
            current_prices[symbol] = None
    
    # Close connection
    conn.close()
    
    return render_template('strategy_backtesting.html', 
                           portfolio=portfolio,
                           current_prices=current_prices,
                           backtesting_presets=backtesting_presets,
                           analysis_date=datetime.now().strftime('%Y-%m-%d'),
                           settings=get_settings())

def analyze_tariff_risk(current_stock=None):
    """Analyze tariff risks for stocks in the portfolio to support AI assistant responses."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get current portfolio positions
    cursor.execute('''
        SELECT 
            Symbol, 
            Name,
            SUM(CASE WHEN Side = 'buy' THEN Qty ELSE -Qty END) as CurrentShares
        FROM 
            transactions
        GROUP BY 
            Symbol
        HAVING 
            CurrentShares > 0
        ORDER BY 
            CurrentShares * 
            (SELECT AveragePrice FROM transactions 
             WHERE Symbol = transactions.Symbol 
             ORDER BY Date DESC, Time DESC LIMIT 1) DESC
    ''')
    
    portfolio = cursor.fetchall()
    
    # Define high-risk tariff stocks
    high_risk_stocks = ['AAPL', 'NVDA', 'TSLA', 'NIO', 'BABA', 'JD', 'PDD', 'XPEV']
    medium_risk_stocks = ['MSFT', 'AMD', 'AMZN', 'INTC', 'QCOM', 'MU', 'AMAT', 'LRCX']
    
    # Create a risk analysis
    risk_analysis = {
        "high_risk": [],
        "medium_risk": [],
        "low_risk": [],
        "total_stocks": len(portfolio),
        "current_stock_risk": None
    }
    
    for stock in portfolio:
        stock_dict = dict(stock)
        
        if stock['Symbol'] in high_risk_stocks:
            stock_dict['risk_level'] = 'high'
            stock_dict['risk_factors'] = [
                'Direct Chinese manufacturing exposure',
                'Significant supply chain dependence on impacted regions',
                'Limited short-term alternatives for key components'
            ]
            risk_analysis['high_risk'].append(stock_dict)
            
        elif stock['Symbol'] in medium_risk_stocks:
            stock_dict['risk_level'] = 'medium'
            stock_dict['risk_factors'] = [
                'Partial supply chain exposure to tariff-affected regions',
                'Some reliance on Chinese components or assembly',
                'Potential for margin pressure due to increased costs'
            ]
            risk_analysis['medium_risk'].append(stock_dict)
            
        else:
            stock_dict['risk_level'] = 'low'
            stock_dict['risk_factors'] = [
                'Limited direct exposure to affected regions',
                'Diversified supply chain',
                'Primarily domestic operations'
            ]
            risk_analysis['low_risk'].append(stock_dict)
        
        # Check if this is the current stock being viewed
        if current_stock and stock['Symbol'] == current_stock:
            risk_analysis['current_stock_risk'] = stock_dict
    
    # Add some general tariff risk context
    risk_analysis['tariff_context'] = {
        'recent_developments': 'Recent tariff increases on Chinese imports include up to 100% on EVs, 25% on semiconductors, batteries, and critical minerals.',
        'potential_impacts': 'Companies with Chinese manufacturing or supply chain exposure face increased costs, margin pressure, and potential need for expensive supply chain restructuring.',
        'sectors_most_affected': 'Technology, automotive, and consumer electronics sectors face the highest risks due to their deep integration with Chinese manufacturing.'
    }
    
    conn.close()
    return risk_analysis

@app.route('/api/chat', methods=['POST'])
def chat():
    """API endpoint to process chat messages and return responses using ChatGPT API"""
    request_id = str(uuid.uuid4())[:8]  # Generate a request ID for tracking
    start_time = time.time()
    
    logger.info(f"[{request_id}] New chat request received")
    
    try:
        data = request.get_json()
        message = data.get('message', '')
        current_stock = data.get('stock', None)  # Get the current stock from the request
        
        logger.info(f"[{request_id}] Message: '{message[:50]}...' for stock: {current_stock}")
        
        # Get current settings
        settings = get_settings()
        logger.info(f"[{request_id}] Current settings: {settings}")
        
        # Check if we're just checking API availability
        if message == 'check_api':
            openai_available = bool(os.getenv('OPENAI_API_KEY'))
            perplexity_available = bool(os.getenv('PERPLEXITY_API_KEY'))
            logger.info(f"[{request_id}] API availability check - OpenAI: {openai_available}, Perplexity: {perplexity_available}")
            return jsonify({
                "openai_available": openai_available,
                "perplexity_available": perplexity_available,
                "api_available": openai_available or perplexity_available,
                "current_settings": settings
            })
        
        if not message:
            logger.warning(f"[{request_id}] Empty message received")
            return jsonify({"response": "Please enter a message."})
        
        # Enhanced logging for request size and context
        message_length = len(message)
        logger.info(f"[{request_id}] Message length: {message_length} characters")
        if message_length > 1000:
            logger.warning(f"[{request_id}] Long message detected ({message_length} chars), may increase processing time")
            
        # Set up timeout protection 
        request_timeout = 55  # Shorter than client timeout
        
        # Capture current request for use in the thread
        ctx_app = app.app_context()
        ctx_req = request._get_current_object()
        
        def process_api_request_with_timeout():
            """Wrapper function for API processing with timeout"""
            with ctx_app:  # Establish app context within the thread
                try:
                    # Get application context to provide to AI models
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    cursor.execute('SELECT COUNT(*) FROM transactions')
                    total_transactions = cursor.fetchone()[0]
                    cursor.execute('SELECT DISTINCT Symbol FROM transactions')
                    symbols = [row['Symbol'] for row in cursor.fetchall()]
                    logger.debug(f"[{request_id}] Portfolio context loaded: {total_transactions} transactions, {len(symbols)} symbols")
                    
                    # Stock-specific context if the user is viewing a stock page
                    stock_specific_context = ""
                    if current_stock:
                        logger.info(f"[{request_id}] Preparing stock-specific context for {current_stock}")
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
                    
                    # Log the context size for debugging
                    context_size = len(context)
                    logger.debug(f"[{request_id}] Context size: {context_size} characters")
                    
                    # Determine AI provider based on settings
                    ai_provider = settings.get('ai_provider', 'perplexity')
                    
                    # Try Perplexity first if available and selected
                    perplexity_client = None
                    if os.getenv('PERPLEXITY_API_KEY') and ai_provider == 'perplexity':
                        try:
                            import openai
                            perplexity_client = openai.OpenAI(
                                api_key=os.getenv('PERPLEXITY_API_KEY'),
                                base_url="https://api.perplexity.ai",
                            )
                        except ImportError:
                            logger.error(f"[{request_id}] OpenAI SDK not installed for Perplexity API")
                        except Exception as e:
                            logger.error(f"[{request_id}] Error initializing Perplexity client: {e}")
                    
                    if perplexity_client:
                        logger.info(f"[{request_id}] Attempting to use Perplexity API")
                        try:
                            # Get the selected model from settings
                            selected_model = settings.get('perplexity_model', 'sonar')
                            
                            # Map names to actual model IDs
                            PERPLEXITY_MODELS = {
                                'sonar': 'sonar',
                                'mixtral': 'mixtral-8x7b-instruct',
                                'claude': 'claude-3-sonnet-20240229',
                                'sonar-medium': 'sonar-medium-online',
                                'sonar-small': 'sonar-small-online',
                                'codellama': 'codellama-70b-instruct',
                                'sonar-deep-research': 'deepseek-research-1.3b'
                            }
                            
                            # Use model ID from mapping or fallback to sonar
                            model_id = PERPLEXITY_MODELS.get(selected_model, 'sonar')
                            logger.info(f"[{request_id}] Using Perplexity model: {selected_model} (ID: {model_id})")
                            
                            perplexity_start = time.time()
                            # Call Perplexity API using the OpenAI client interface
                            response = perplexity_client.chat.completions.create(
                                model=model_id,  # Use the model ID from the mapping
                                messages=[
                                    {"role": "system", "content": context},
                                    {"role": "user", "content": message}
                                ],
                                max_tokens=1000
                            )
                            perplexity_time = time.time() - perplexity_start
                            logger.info(f"[{request_id}] Perplexity API call successful in {perplexity_time:.2f}s")
                            
                            # Extract the response text
                            chat_response = response.choices[0].message.content.strip()
                            total_time = time.time() - start_time
                            logger.info(f"[{request_id}] Total request time: {total_time:.2f}s")
                            
                            response_data = {
                                "response": chat_response, 
                                "provider": "perplexity",
                                "model": selected_model
                            }
                            return response_data
                            
                        except Exception as e:
                            logger.error(f"[{request_id}] Error calling Perplexity API: {str(e)}")
                            logger.error(f"[{request_id}] Perplexity API error details: {traceback.format_exc()}")
                            logger.info(f"[{request_id}] Falling back to OpenAI API...")
                            # Continue to OpenAI fallback
                    
                    # Try OpenAI if Perplexity failed or isn't available or OpenAI is selected
                    openai_client = None
                    if os.getenv('OPENAI_API_KEY') and (ai_provider == 'openai' or not perplexity_client):
                        try:
                            import openai
                            openai_client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
                        except ImportError:
                            logger.error(f"[{request_id}] OpenAI SDK not installed")
                        except Exception as e:
                            logger.error(f"[{request_id}] Error initializing OpenAI client: {e}")
                    
                    if openai_client:
                        logger.info(f"[{request_id}] Attempting to use OpenAI API")
                        try:
                            openai_start = time.time()
                            # Log API request details
                            logger.debug(f"[{request_id}] OpenAI API request: model=gpt-3.5-turbo, message_length={len(message)}")
                            
                            # Call OpenAI API
                            response = openai_client.chat.completions.create(
                                model="gpt-3.5-turbo",
                                messages=[
                                    {"role": "system", "content": context},
                                    {"role": "user", "content": message}
                                ],
                                max_tokens=1000,
                                temperature=0.7,
                                presence_penalty=0.6,
                                frequency_penalty=0.2,
                                stream=False
                            )
                            
                            openai_time = time.time() - openai_start
                            logger.info(f"[{request_id}] OpenAI API call successful in {openai_time:.2f}s")
                            
                            # Log response details
                            response_id = getattr(response, 'id', 'unknown')
                            model = getattr(response, 'model', 'gpt-3.5-turbo')
                            usage = getattr(response, 'usage', {})
                            logger.debug(f"[{request_id}] OpenAI response ID: {response_id}, model: {model}")
                            logger.debug(f"[{request_id}] Token usage: {usage}")
                            
                            # Extract the response text
                            chat_response = response.choices[0].message.content.strip()
                            total_time = time.time() - start_time
                            logger.info(f"[{request_id}] Total request time: {total_time:.2f}s")
                            
                            response_data = {
                                "response": chat_response, 
                                "provider": "openai",
                                "model": "gpt-3.5-turbo"
                            }
                            return response_data
                            
                        except Exception as e:
                            logger.error(f"[{request_id}] Unexpected error calling OpenAI API: {str(e)}")
                            logger.error(f"[{request_id}] Error details: {traceback.format_exc()}")
                            logger.info(f"[{request_id}] Falling back to simple chat due to unexpected error")
                            chat_response = handle_simple_chat(message, current_stock)
                            if isinstance(chat_response, dict):
                                return chat_response
                            return {
                                "response": "Sorry, an error occurred while processing your message. Please try again later.",
                                "provider": "error",
                                "error": str(e)
                            }
                    
                    # If both fail, use simple chat fallback
                    logger.warning(f"[{request_id}] No AI provider available, using simple chat fallback")
                    chat_response = handle_simple_chat(message, current_stock)
                    if isinstance(chat_response, dict):
                        return chat_response
                    return {
                        "response": str(chat_response),
                        "provider": "fallback"
                    }
                except Exception as e:
                    logger.error(f"[{request_id}] Error in API processing: {str(e)}")
                    logger.error(f"[{request_id}] API processing error details: {traceback.format_exc()}")
                    return {
                        "response": "Sorry, an error occurred while processing your message. Please try again later.",
                        "provider": "error",
                        "error": str(e)
                    }
        
        # Use a thread with timeout to prevent hanging the server
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(process_api_request_with_timeout)
            try:
                result = future.result(timeout=request_timeout)
                return jsonify(result)
            except TimeoutError:
                logger.error(f"[{request_id}] API processing timed out after {request_timeout} seconds")
                return jsonify({
                    "response": "Sorry, the request took too long to process. Please try again with a simpler query.",
                    "provider": "timeout",
                    "error": "API processing timeout"
                }), 500
    except Exception as e:
        logger.error(f"[{request_id}] Critical error in chat endpoint: {str(e)}")
        logger.error(f"[{request_id}] Critical error details: {traceback.format_exc()}")
        total_time = time.time() - start_time
        logger.info(f"[{request_id}] Failed request completed in {total_time:.2f}s")
        
        return jsonify({
            "response": "Sorry, an unexpected error occurred while processing your request. Please try again later.",
            "provider": "error",
            "error": str(e)
        }), 500

@app.route('/api/risk/tariff', methods=['GET'])
def api_tariff_risk():
    """API endpoint to get tariff risk analysis for the portfolio."""
    try:
        # Get symbol parameter if provided
        symbol = request.args.get('symbol', None)
        risk_data = analyze_tariff_risk(symbol)
        
        return jsonify({
            "success": True,
            "data": risk_data
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

def handle_simple_chat(message, current_stock=None):
    """Handle a simple chat message with the AI assistant."""
    request_id = str(uuid.uuid4())[:8]  # Generate a request ID for tracking
    logger.info(f"[{request_id}] Starting handle_simple_chat fallback with message: '{message[:50]}...'")
    
    # Make sure we're in an application context
    if not app.app_context.top:
        logger.info(f"[{request_id}] Creating app context for handle_simple_chat")
        ctx = app.app_context()
        ctx.push()
    
    # Look for indicators of questions needing portfolio risk data
    need_risk_data = False
    risk_keywords = ['risk', 'tariff', 'trade war', 'china', 'supply chain', 'import tax', 'export', 'trade policy']
    
    for keyword in risk_keywords:
        if keyword.lower() in message.lower():
            need_risk_data = True
            logger.info(f"[{request_id}] Risk keyword detected: '{keyword}'")
            break
    
    # Get risk analysis data if needed
    risk_data = None
    if need_risk_data:
        logger.info(f"[{request_id}] Gathering risk analysis data for {current_stock if current_stock else 'portfolio'}")
        try:
            risk_data = analyze_tariff_risk(current_stock)
            logger.debug(f"[{request_id}] Risk data gathered successfully")
        except Exception as e:
            logger.error(f"[{request_id}] Error gathering risk data: {str(e)}")
            logger.error(f"[{request_id}] Risk data error details: {traceback.format_exc()}")
    
    # Format transactions for context
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if current_stock:
            logger.info(f"[{request_id}] Fetching transactions for {current_stock}")
            # Get transactions for the current stock
            cursor.execute('SELECT * FROM transactions WHERE Symbol = ? ORDER BY Date DESC, Time DESC LIMIT 20', (current_stock,))
        else:
            logger.info(f"[{request_id}] Fetching recent transactions for portfolio")
            # Get recent transactions
            cursor.execute('SELECT * FROM transactions ORDER BY Date DESC, Time DESC LIMIT 10')
        
        transactions = cursor.fetchall()
        conn.close()
        logger.debug(f"[{request_id}] Retrieved {len(transactions)} transactions for context")
    except Exception as e:
        logger.error(f"[{request_id}] Error retrieving transactions: {str(e)}")
        logger.error(f"[{request_id}] Transaction retrieval error details: {traceback.format_exc()}")
        transactions = []
    
    # Format transactions for context
    transaction_context = ""
    if transactions:
        transaction_context = "Recent transactions:\n"
        for t in transactions:
            try:
                # Convert AveragePrice to float if it's a string
                avg_price = float(t['AveragePrice']) if isinstance(t['AveragePrice'], str) else t['AveragePrice']
                transaction_context += f"- {t['Date']} {t['Symbol']} {t['Side'].upper()} {t['Qty']} shares at ${avg_price:.2f}\n"
            except (ValueError, TypeError) as e:
                logger.warning(f"[{request_id}] Error formatting transaction {t.get('Id', 'unknown')}: {str(e)}")
                # Fallback to string format if conversion fails
                transaction_context += f"- {t['Date']} {t['Symbol']} {t['Side'].upper()} {t['Qty']} shares at ${t['AveragePrice']}\n"
    
    # Include risk analysis if available
    risk_context = ""
    if risk_data:
        logger.debug(f"[{request_id}] Adding risk context to prompt")
        # Add general tariff context
        risk_context += "\nTariff Risk Context:\n"
        risk_context += f"- Recent Developments: {risk_data['tariff_context']['recent_developments']}\n"
        risk_context += f"- Potential Impacts: {risk_data['tariff_context']['potential_impacts']}\n"
        risk_context += f"- Most Affected Sectors: {risk_data['tariff_context']['sectors_most_affected']}\n\n"
        
        # Add portfolio risk exposure
        risk_context += f"Portfolio Tariff Risk Exposure:\n"
        risk_context += f"- High Risk Holdings: {len(risk_data['high_risk'])} stocks\n"
        if risk_data['high_risk']:
            risk_context += "  " + ", ".join([f"{s['Symbol']} ({s['Name']})" for s in risk_data['high_risk']]) + "\n"
        
        risk_context += f"- Medium Risk Holdings: {len(risk_data['medium_risk'])} stocks\n"
        if risk_data['medium_risk']:
            risk_context += "  " + ", ".join([f"{s['Symbol']} ({s['Name']})" for s in risk_data['medium_risk']]) + "\n"
        
        # Add specific stock risk if viewing a stock
        if current_stock and risk_data['current_stock_risk']:
            stock_risk = risk_data['current_stock_risk']
            risk_context += f"\nRisk Profile for {current_stock} ({stock_risk['Name']}):\n"
            risk_context += f"- Risk Level: {stock_risk['risk_level'].upper()}\n"
            risk_context += f"- Risk Factors:\n"
            for factor in stock_risk['risk_factors']:
                risk_context += f"  * {factor}\n"
    
    # Get settings in a way that doesn't require request context
    try:
        settings = get_settings()  # This might still fail if it uses session
        ai_provider = settings.get('ai_provider', DEFAULT_SETTINGS['ai_provider'])
    except RuntimeError:
        logger.warning(f"[{request_id}] Could not access session for settings, using defaults")
        settings = DEFAULT_SETTINGS.copy()
        ai_provider = settings.get('ai_provider', 'perplexity')
    
    logger.info(f"[{request_id}] Fallback using AI provider preference: {ai_provider}")
    
    # Check if the message is specifically about tariffs or risk
    is_risk_question = need_risk_data
    
    # Enhanced system prompt for tariff/risk questions
    system_prompt = (
        "You are a professional stock portfolio analyst assistant. "
        "Provide clear, concise analysis about stock transactions and portfolio performance. "
        "When analyzing trades, consider entry points, exit points, and market timing. "
        "You can refer to the transaction history provided to give context-specific advice. "
    )
    
    # Add tariff-specific instructions if needed
    if is_risk_question:
        logger.info(f"[{request_id}] Using risk-specific system prompt")
        system_prompt += (
            "Focus especially on tariff and trade policy risks in your analysis. "
            "Consider how supply chain disruptions, increased import costs, and "
            "market access restrictions might impact different holdings. "
            "Provide specific insights on how to mitigate these risks through portfolio adjustments. "
            "Use the tariff risk data provided to give targeted recommendations. "
        )
    
    # Build user prompt with appropriate context
    user_prompt = f"User question: {message}\n\n"
    
    if transaction_context:
        user_prompt = f"Transaction context:\n{transaction_context}\n\n" + user_prompt
    
    if is_risk_question and risk_context:
        user_prompt = f"Risk analysis context:\n{risk_context}\n\n" + user_prompt
    
    logger.debug(f"[{request_id}] Prompt size - System: {len(system_prompt)} chars, User: {len(user_prompt)} chars")
    
    # Try to use Perplexity first if configured
    if ai_provider == 'perplexity' and perplexity_client:
        logger.info(f"[{request_id}] Attempting to use Perplexity API in fallback mode")
        try:
            model = settings.get('perplexity_model', DEFAULT_PERPLEXITY_MODEL)
            logger.debug(f"[{request_id}] Using Perplexity model: {model}")
            
            start_time = time.time()
            response = perplexity_client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7
            )
            elapsed_time = time.time() - start_time
            logger.info(f"[{request_id}] Perplexity API call in fallback mode successful in {elapsed_time:.2f}s")
            
            return {
                "response": response.choices[0].message.content,
                "provider": "Perplexity",
                "model": model
            }
        except Exception as e:
            logger.error(f"[{request_id}] Error with Perplexity API in fallback mode: {str(e)}")
            logger.error(f"[{request_id}] Perplexity fallback error details: {traceback.format_exc()}")
            # Fall back to OpenAI if available
    
    # Use OpenAI if Perplexity failed or not configured
    if openai_client:
        logger.info(f"[{request_id}] Attempting to use OpenAI API in fallback mode")
        try:
            start_time = time.time()
            response = openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7
            )
            elapsed_time = time.time() - start_time
            logger.info(f"[{request_id}] OpenAI API call in fallback mode successful in {elapsed_time:.2f}s")
            
            return {
                "response": response.choices[0].message.content,
                "provider": "OpenAI",
                "model": "gpt-3.5-turbo"
            }
        except Exception as e:
            logger.error(f"[{request_id}] Error with OpenAI API in fallback mode: {str(e)}")
            logger.error(f"[{request_id}] OpenAI fallback error details: {traceback.format_exc()}")
    
    # If both APIs failed, return a helpful error message
    logger.warning(f"[{request_id}] All API attempts failed, returning default response")
    if is_risk_question:
        default_response = "I'm sorry, I couldn't access the AI services to analyze your portfolio risk. From the available data, stocks in technology and consumer electronics sectors are generally most affected by tariffs due to supply chain dependencies on China. Consider diversifying your portfolio to reduce exposure to these sectors."
    else:
        default_response = "I'm sorry, there was an error processing your request. Please try again later or check your API settings."
    
    return {
        "response": default_response,
        "provider": "Fallback",
        "model": "Internal"
    }

def get_stock_sector(symbol):
    """
    Get the sector information for a given stock symbol using yfinance.
    Returns the sector string or "Unknown" if not available.
    """
    try:
        stock = yf.Ticker(symbol)
        info = stock.info
        
        # Check for sector information in different possible fields
        sector = info.get('sector') or info.get('industryDisp')
        
        if not sector and 'info' in dir(stock) and callable(getattr(stock, 'info')):
            # Try refreshing info
            refreshed_info = stock.info
            sector = refreshed_info.get('sector') or refreshed_info.get('industryDisp')
        
        return sector or "Unknown"
    except Exception as e:
        print(f"Error getting sector for {symbol}: {e}")
        return "Unknown"

def assess_tariff_risk(symbol, sector):
    """
    Assess the tariff risk for a given stock based on its symbol and sector.
    Returns a dictionary with risk assessment.
    """
    # High-risk sectors for tariffs
    high_risk_sectors = [
        "Technology", "Consumer Electronics", "Semiconductors", 
        "Automotive", "Consumer Cyclical"
    ]
    
    # Medium-risk sectors
    medium_risk_sectors = [
        "Industrials", "Manufacturing", "Materials", 
        "Consumer Discretionary", "Communication Services"
    ]
    
    # High-risk companies regardless of sector
    high_risk_symbols = ['AAPL', 'NVDA', 'TSLA', 'NIO', 'AMD', 'MU']
    medium_risk_symbols = ['MSFT', 'INTC', 'AMZN', 'QCOM', 'AMAT', 'LRCX']
    
    risk_level = "low"
    risk_score = 0.3
    
    # Check symbol first
    if symbol in high_risk_symbols:
        risk_level = "high"
        risk_score = 0.9
    elif symbol in medium_risk_symbols:
        risk_level = "medium"
        risk_score = 0.6
    
    # Then check sector if not already high risk
    elif sector in high_risk_sectors:
        risk_level = "high"
        risk_score = 0.8
    elif sector in medium_risk_sectors:
        risk_level = "medium"
        risk_score = 0.5
    
    assessment = ""
    if risk_level == "high":
        assessment = "High exposure to tariffs due to significant supply chain dependencies or direct manufacturing in impacted regions."
    elif risk_level == "medium":
        assessment = "Moderate exposure to tariffs with some supply chain vulnerabilities but potential to adapt."
    else:
        assessment = "Limited exposure to tariffs with diversified supply chains or primarily domestic operations."
    
    return {
        "risk_level": risk_level,
        "risk_score": risk_score,
        "assessment": assessment
    }

def init_db():
    """Initialize the database with transactions table and thesis_jobs table"""
    # First drop existing tables to ensure a clean start
    conn = sqlite3.connect('stock_transactions.db')
    c = conn.cursor()
    
    # Drop tables if they exist to ensure clean schema
    c.execute('DROP TABLE IF EXISTS transactions')
    c.execute('DROP TABLE IF EXISTS thesis_jobs')
    c.execute('DROP TABLE IF EXISTS earnings_jobs')
    c.execute('DROP TABLE IF EXISTS earnings_calendar')
    
    # Create transactions table if it doesn't exist - using TEXT for all fields to prevent type issues
    c.execute('''
    CREATE TABLE IF NOT EXISTS transactions (
        Id TEXT,
        Date TEXT,
        Time TEXT,
        Symbol TEXT,
        Name TEXT,
        Type TEXT,
        Side TEXT,
        AveragePrice TEXT,  -- Store as TEXT to avoid type conversion issues
        Qty TEXT,           -- Store as TEXT to avoid type conversion issues
        State TEXT,
        Fees TEXT
    )
    ''')
    
    # Create thesis_jobs table if it doesn't exist
    c.execute('''
    CREATE TABLE IF NOT EXISTS thesis_jobs (
        job_id TEXT PRIMARY KEY,
        thesis TEXT NOT NULL,
        status TEXT NOT NULL,
        created_at TEXT NOT NULL,
        completed_at TEXT,
        result TEXT
    )
    ''')
    
    # Create earnings_jobs table for storing earnings research requests
    c.execute('''
    CREATE TABLE IF NOT EXISTS earnings_jobs (
        job_id TEXT PRIMARY KEY,
        symbol TEXT NOT NULL,
        earnings_date TEXT NOT NULL,
        status TEXT NOT NULL,
        created_at TEXT NOT NULL,
        completed_at TEXT,
        result TEXT
    )
    ''')
    
    # Create earnings_calendar table for storing upcoming earnings dates
    c.execute('''
    CREATE TABLE IF NOT EXISTS earnings_calendar (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        symbol TEXT NOT NULL,
        company_name TEXT,
        earnings_date TEXT NOT NULL,
        time_of_day TEXT,
        eps_estimate TEXT,  -- Store as TEXT to avoid type conversion issues
        last_updated TEXT NOT NULL
    )
    ''')
    
    conn.commit()
    
    # Load data from CSV if the table is empty
    c.execute('SELECT COUNT(*) FROM transactions')
    if c.fetchone()[0] == 0:
        with open('stock_orders.csv', 'r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                try:
                    # Convert date format from MM/DD/YYYY to YYYY-MM-DD
                    date_obj = datetime.strptime(row['Date'], '%m/%d/%Y')
                    date_str = date_obj.strftime('%Y-%m-%d')
                    
                    # Generate a unique ID if not present in the CSV
                    transaction_id = row.get('Id', str(uuid.uuid4()))
                    
                    # Store all values as strings in the database to avoid type issues
                    c.execute('''
                    INSERT INTO transactions VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        transaction_id,
                        date_str,
                        row['Time'],
                        row['Symbol'],
                        row['Name'],
                        row['Type'],
                        row['Side'],
                        row['AveragePrice'],  # Store as text
                        row['Qty'],           # Store as text
                        row['State'],
                        row['Fees']
                    ))
                except Exception as e:
                    print(f"Error processing row: {row}")
                    print(f"Error: {e}")
                    continue
            conn.commit()
    
    conn.close()
    print("Database initialized successfully!")

def create_thesis_job(thesis):
    """Create a new thesis validation job in the database"""
    job_id = str(uuid.uuid4())
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
    INSERT INTO thesis_jobs (job_id, thesis, status, created_at)
    VALUES (?, ?, ?, ?)
    ''', (job_id, thesis, 'pending', datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    
    conn.commit()
    conn.close()
    return job_id

def get_thesis_job(job_id):
    """Get a specific thesis job by ID"""
    conn = get_db_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM thesis_jobs WHERE job_id = ?', (job_id,))
    job = cursor.fetchone()
    
    conn.close()
    return dict(job) if job else None

def get_thesis_jobs():
    """Get all thesis jobs from the database"""
    conn = get_db_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM thesis_jobs ORDER BY created_at DESC')
    jobs = cursor.fetchall()
    
    conn.close()
    return [dict(job) for job in jobs]

def update_thesis_job(job_id, status, result=None):
    """Update the status and result of a thesis job"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if result:
        cursor.execute('''
        UPDATE thesis_jobs 
        SET status = ?, result = ?, completed_at = ?
        WHERE job_id = ?
        ''', (status, result, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), job_id))
    else:
        cursor.execute('''
        UPDATE thesis_jobs 
        SET status = ?
        WHERE job_id = ?
        ''', (status, job_id))
    
    conn.commit()
    conn.close()

def process_thesis_validation(job_id, thesis):
    """Background task to process the thesis validation"""
    try:
        # Update job status to processing
        update_thesis_job(job_id, 'processing')
        
        # Get settings
        settings = DEFAULT_SETTINGS
        
        # Get Perplexity client
        perplexity_api_key = os.getenv('PERPLEXITY_API_KEY')
        if not perplexity_api_key:
            update_thesis_job(job_id, 'failed', "Perplexity API key not configured")
            return
        
        perplexity_client = OpenAI(
            api_key=perplexity_api_key,
            base_url="https://api.perplexity.ai"
        )
        
        # Use sonar-deep-research model specifically for thesis validation
        model = 'sonar-deep-research'
        
        # Create a prompt for the thesis validation
        prompt = f"""Analyze the following investment thesis: "{thesis}"
        
        Provide a detailed analysis with:
        1. Expert opinions supporting the thesis
        2. Expert opinions refuting the thesis
        3. Recent market data and trends relevant to this thesis
        4. Key risk factors to consider
        5. Potential investment opportunities related to this thesis
        
        Include specific citations, references, and links to sources for all claims. 
        Format your response using proper Markdown syntax:
        - Use ## for section headings (h2)
        - Use ### for subsection headings (h3)
        - Use **bold** for emphasis
        - Use *italic* for secondary emphasis
        - Use [text](url) format for links
        - Use > for blockquotes
        - Use properly formatted lists with - or 1. 
        - Include a "Sources" section at the end with numbered references
        
        Be balanced in your analysis, considering both supporting and contradicting evidence.
        """
        
        # Call Perplexity API using the OpenAI client interface
        response = perplexity_client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are an expert financial advisor who provides comprehensive, well-researched investment thesis validations with specific citations and references. Format your response with clear Markdown syntax including proper headers, lists, links, and citations."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
            max_tokens=4000
        )
        
        if response and response.choices and len(response.choices) > 0:
            result = response.choices[0].message.content
            
            # Ensure the result contains proper markdown formatting
            # Add a main heading if not present
            if not result.startswith('# '):
                result = f"# Analysis of Investment Thesis: {thesis}\n\n{result}"
            
            # Ensure sources are properly formatted
            if "Sources:" in result and not "\n## Sources" in result:
                result = result.replace("Sources:", "\n## Sources\n")
            
            update_thesis_job(job_id, 'completed', result)
        else:
            update_thesis_job(job_id, 'failed', "No response received from the AI model")
    
    except Exception as e:
        print(f"Error processing thesis validation job {job_id}: {str(e)}")
        update_thesis_job(job_id, 'failed', f"Error: {str(e)}")

@app.route('/thesis-validation', methods=['GET', 'POST'])
def thesis_validation():
    # Get current settings
    settings = get_settings()
    
    # Check if Perplexity API is available
    perplexity_available = bool(os.getenv('PERPLEXITY_API_KEY'))
    if not perplexity_available:
        flash("Perplexity API is required for thesis validation. Please set your API key in settings.", "warning")
        return redirect(url_for('settings'))
    
    # Get connection to database
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get user's portfolio (stocks with positive current shares)
    cursor.execute('''
        SELECT 
            Symbol, 
            Name,
            SUM(CASE WHEN Side = 'buy' THEN Qty ELSE -Qty END) as CurrentShares,
            SUM(CASE WHEN Side = 'buy' THEN Qty * AveragePrice ELSE 0 END) / 
            NULLIF(SUM(CASE WHEN Side = 'buy' THEN Qty ELSE 0 END), 0) as AverageCost
        FROM 
            transactions
        GROUP BY 
            Symbol
        HAVING 
            SUM(CASE WHEN Side = 'buy' THEN Qty ELSE -Qty END) > 0
        ORDER BY 
            Symbol
    ''')
    
    portfolio = cursor.fetchall()
    
    # Get current prices
    current_prices = {}
    for stock in portfolio:
        symbol = stock['Symbol']
        if symbol not in current_prices:
            price_data = get_stock_price(symbol)
            if price_data and 'current_price' in price_data and price_data['current_price'] is not None:
                current_prices[symbol] = price_data['current_price']
            else:
                current_prices[symbol] = 0
    
    # Portfolio summary
    portfolio_summary = {
        'total_stocks': len(portfolio),
        'total_value': sum(stock['CurrentShares'] * current_prices.get(stock['Symbol'], 0) for stock in portfolio),
        'total_investment': sum(stock['CurrentShares'] * stock['AverageCost'] for stock in portfolio if stock['AverageCost'] is not None),
    }
    
    portfolio_summary['total_gain_loss'] = portfolio_summary['total_value'] - portfolio_summary['total_investment']
    if portfolio_summary['total_investment'] > 0:
        portfolio_summary['total_gain_loss_percentage'] = (portfolio_summary['total_gain_loss'] / portfolio_summary['total_investment']) * 100
    else:
        portfolio_summary['total_gain_loss_percentage'] = 0
    
    # Get all thesis jobs
    thesis_jobs = get_thesis_jobs()
    
    # Handle thesis analysis request
    selected_thesis = None
    job_id = None
    
    if request.method == 'POST':
        selected_thesis = request.form.get('thesis')
        
        if selected_thesis:
            # Create a new job in the database
            job_id = create_thesis_job(selected_thesis)
            
            # Start the thesis validation in a background thread
            thread = threading.Thread(
                target=process_thesis_validation,
                args=(job_id, selected_thesis)
            )
            thread.daemon = True
            thread.start()
            
            flash(f"Thesis validation job created. Check back later for results. Job ID: {job_id}", "success")
            return redirect(url_for('thesis_validation'))
    
    # Close database connection
    conn.close()
    
    return render_template(
        'thesis_validation.html',
        portfolio=portfolio,
        current_prices=current_prices,
        portfolio_summary=portfolio_summary,
        investment_theses=INVESTMENT_THESES,
        thesis_jobs=thesis_jobs,
        selected_thesis=selected_thesis,
        job_id=job_id,
        settings=settings
    )

@app.route('/thesis-job/<job_id>')
def thesis_job(job_id):
    """Route to get a specific thesis job"""
    job = get_thesis_job(job_id)
    
    if not job:
        flash("Job not found", "error")
        return redirect(url_for('thesis_validation'))
    
    return render_template(
        'thesis_job.html',
        job=job,
        settings=get_settings()
    )

@app.route('/api/thesis-job/<job_id>', methods=['GET'])
def api_thesis_job(job_id):
    """API endpoint to get the status of a thesis job"""
    job = get_thesis_job(job_id)
    
    if not job:
        return jsonify({"error": "Job not found"}), 404
    
    return jsonify(job)

# Earnings Calendar Helper Functions
def get_earnings_calendar(start_date=None, end_date=None, symbol=None):
    """
    Get earnings calendar from the database, with optional filtering by date range or symbol.
    
    Args:
        start_date (str): Filter earnings after this date (inclusive)
        end_date (str): Filter earnings before this date (inclusive)
        symbol (str): Filter by specific stock symbol
        
    Returns:
        list: Earnings calendar entries matching the criteria
    """
    conn = get_db_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    query = 'SELECT * FROM earnings_calendar'
    params = []
    
    # Add filtering conditions
    conditions = []
    if start_date:
        conditions.append('earnings_date >= ?')
        params.append(start_date)
    
    if end_date:
        conditions.append('earnings_date <= ?')
        params.append(end_date)
    
    if symbol:
        conditions.append('symbol = ?')
        params.append(symbol)
    
    if conditions:
        query += ' WHERE ' + ' AND '.join(conditions)
    
    query += ' ORDER BY earnings_date ASC'
    
    cursor.execute(query, params)
    earnings = cursor.fetchall()
    
    # Process earnings data to ensure eps_estimate is properly handled
    processed_earnings = []
    for entry in earnings:
        entry_dict = dict(entry)
        
        # Handle eps_estimate
        if entry_dict.get('eps_estimate') is not None:
            # Try to convert to float if possible
            try:
                entry_dict['eps_estimate'] = float(entry_dict['eps_estimate'])
            except (ValueError, TypeError):
                # Keep as string if conversion fails
                pass
        
        processed_earnings.append(entry_dict)
    
    conn.close()
    return processed_earnings

def update_earnings_calendar():
    """
    Update the earnings calendar with latest data using Yahoo Finance API.
    Focuses on the user's portfolio stocks first, then adds other major stocks.
    
    Returns:
        bool: Success status
    """
    try:
        # Get current date
        today = datetime.now().date()
        
        # Get the next 90 days range (increased from 30 days)
        end_date = (today + timedelta(days=90)).strftime('%Y-%m-%d')
        
        # Get user's portfolio stocks
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT DISTINCT Symbol, Name
            FROM transactions
            WHERE Symbol IN (
                SELECT Symbol
                FROM transactions
                GROUP BY Symbol
                HAVING SUM(CASE WHEN Side = 'buy' THEN Qty ELSE -Qty END) > 0
            )
        ''')
        
        portfolio_stocks = cursor.fetchall()
        
        # Also get some major indices and popular stocks to add to the calendar
        major_stocks = [
            # MAG7 Stocks (if not in portfolio)
            ('AAPL', 'Apple Inc.'),
            ('MSFT', 'Microsoft Corporation'),
            ('GOOGL', 'Alphabet Inc.'),
            ('AMZN', 'Amazon.com Inc.'),
            ('META', 'Meta Platforms Inc.'),
            ('NVDA', 'NVIDIA Corporation'),
            ('TSLA', 'Tesla Inc.'),
            
            # Other popular stocks
            ('AMD', 'Advanced Micro Devices, Inc.'),
            ('INTC', 'Intel Corporation'),
            ('V', 'Visa Inc.'),
            ('JPM', 'JPMorgan Chase & Co.'),
            ('NFLX', 'Netflix Inc.'),
            ('DIS', 'The Walt Disney Company'),
            ('ADBE', 'Adobe Inc.'),
            ('CRM', 'Salesforce, Inc.')
        ]
        
        # Get today's date as string
        today_str = today.strftime('%Y-%m-%d')
        
        # Open database connection for updates
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # List of common ETFs that don't report earnings
        common_etfs = ['SPY', 'QQQ', 'VOO', 'IVV', 'VTI', 'TQQQ', 'SQQQ', 'DIA', 'IJR', 'EFA', 'XLF', 'XLE', 'XLK', 'XLV', 'ARKK']
        
        # Track processed symbols
        processed_symbols = set()
        
        # Process each stock in the portfolio first
        for stock in portfolio_stocks:
            symbol = stock['Symbol']
            name = stock['Name']
            
            # Skip common ETFs that don't report earnings
            if symbol in common_etfs or is_etf(symbol, name):
                continue
                
            processed_symbols.add(symbol)
            
            try:
                # Check if we already have recent data for this stock
                cursor.execute('''
                    SELECT * FROM earnings_calendar 
                    WHERE symbol = ? AND earnings_date >= ? AND last_updated >= date('now', '-7 days')
                ''', (symbol, today_str))
                
                existing_entry = cursor.fetchone()
                if existing_entry:
                    # Already have fresh data, skip
                    continue
                
                # Get earnings data using yfinance
                stock_data = yf.Ticker(symbol)
                earnings_dates = stock_data.calendar
                
                if earnings_dates and hasattr(earnings_dates, 'loc') and 'Earnings Date' in earnings_dates:
                    earnings_date = earnings_dates.loc['Earnings Date']
                    
                    # Convert to datetime if it's a timestamp
                    if isinstance(earnings_date, pd.Timestamp):
                        earnings_date = earnings_date.date().strftime('%Y-%m-%d')
                    else:
                        earnings_date = str(earnings_date)
                    
                    # Get time of day (BMO = Before Market Open, AMC = After Market Close)
                    time_of_day = 'Unknown'
                    earnings_time = stock_data.calendar.loc['Earnings Time'] if 'Earnings Time' in stock_data.calendar else None
                    if earnings_time:
                        if 'bmo' in str(earnings_time).lower():
                            time_of_day = 'BMO'
                        elif 'amc' in str(earnings_time).lower():
                            time_of_day = 'AMC'
                    
                    # Get EPS estimate
                    eps_estimate = None
                    if 'EPS Estimate' in stock_data.calendar:
                        eps_estimate = stock_data.calendar.loc['EPS Estimate']
                        # Safely handle various types of EPS estimate values
                        if pd.isna(eps_estimate):
                            eps_estimate = None
                        elif isinstance(eps_estimate, (int, float)):
                            eps_estimate = str(round(eps_estimate, 2))
                        else:
                            # Convert any other type to string
                            eps_estimate = str(eps_estimate)
                    
                    # Upsert into database
                    cursor.execute('''
                        INSERT OR REPLACE INTO earnings_calendar 
                        (symbol, company_name, earnings_date, time_of_day, eps_estimate, last_updated)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (
                        symbol, 
                        name, 
                        earnings_date,
                        time_of_day,
                        eps_estimate,
                        today_str
                    ))
                
            except Exception as e:
                print(f"Error fetching earnings for {symbol}: {e}")
                continue
        
        # Now process major stocks that aren't in the portfolio
        for symbol, name in major_stocks:
            # Skip if already processed or if it's an ETF
            if symbol in processed_symbols or symbol in common_etfs:
                continue
                
            processed_symbols.add(symbol)
            
            try:
                # Check if we already have recent data for this stock
                cursor.execute('''
                    SELECT * FROM earnings_calendar 
                    WHERE symbol = ? AND earnings_date >= ? AND last_updated >= date('now', '-7 days')
                ''', (symbol, today_str))
                
                existing_entry = cursor.fetchone()
                if existing_entry:
                    # Already have fresh data, skip
                    continue
                
                # Get earnings data using yfinance
                stock_data = yf.Ticker(symbol)
                earnings_dates = stock_data.calendar
                
                if earnings_dates and hasattr(earnings_dates, 'loc') and 'Earnings Date' in earnings_dates:
                    earnings_date = earnings_dates.loc['Earnings Date']
                    
                    # Convert to datetime if it's a timestamp
                    if isinstance(earnings_date, pd.Timestamp):
                        earnings_date = earnings_date.date().strftime('%Y-%m-%d')
                    else:
                        earnings_date = str(earnings_date)
                    
                    # Get time of day (BMO = Before Market Open, AMC = After Market Close)
                    time_of_day = 'Unknown'
                    earnings_time = stock_data.calendar.loc['Earnings Time'] if 'Earnings Time' in stock_data.calendar else None
                    if earnings_time:
                        if 'bmo' in str(earnings_time).lower():
                            time_of_day = 'BMO'
                        elif 'amc' in str(earnings_time).lower():
                            time_of_day = 'AMC'
                    
                    # Get EPS estimate
                    eps_estimate = None
                    if 'EPS Estimate' in stock_data.calendar:
                        eps_estimate = stock_data.calendar.loc['EPS Estimate']
                        # Safely handle various types of EPS estimate values
                        if pd.isna(eps_estimate):
                            eps_estimate = None
                        elif isinstance(eps_estimate, (int, float)):
                            eps_estimate = str(round(eps_estimate, 2))
                        else:
                            # Convert any other type to string
                            eps_estimate = str(eps_estimate)
                    
                    # Upsert into database
                    cursor.execute('''
                        INSERT OR REPLACE INTO earnings_calendar 
                        (symbol, company_name, earnings_date, time_of_day, eps_estimate, last_updated)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (
                        symbol, 
                        name, 
                        earnings_date,
                        time_of_day,
                        eps_estimate,
                        today_str
                    ))
                
            except Exception as e:
                print(f"Error fetching earnings for {symbol}: {e}")
                continue
        
        # Clean up old entries
        cursor.execute('''
            DELETE FROM earnings_calendar 
            WHERE earnings_date < ?
        ''', (today_str,))
        
        # Commit changes
        conn.commit()
        conn.close()
        return True
    
    except Exception as e:
        print(f"Error updating earnings calendar: {e}")
        return False

def is_etf(symbol, name=None):
    """
    Determine if a security is likely an ETF based on its symbol or name
    
    Args:
        symbol (str): The stock symbol to check
        name (str): The name of the security, if available
        
    Returns:
        bool: True if the security is likely an ETF, False otherwise
    """
    # Common ETF keywords in names
    etf_keywords = ['ETF', 'FUND', 'INDEX', 'TRUST', 'SHARES', 'ISHARES', 'VANGUARD', 'SPDR']
    
    # Check if name contains ETF keywords
    if name:
        upper_name = name.upper()
        if any(keyword in upper_name for keyword in etf_keywords):
            return True
            
    # Check if typical ETF pattern (3-4 letters, often ends with specific letters)
    if len(symbol) <= 4 and any(symbol.endswith(suffix) for suffix in ['X', 'Q', 'S']):
        # Additional verification with yfinance if needed
        try:
            stock = yf.Ticker(symbol)
            info = stock.info
            if 'quoteType' in info and info['quoteType'] in ['ETF', 'MUTUALFUND', 'INDEX']:
                return True
        except:
            # If we can't verify, just continue with other checks
            pass
            
    return False

def create_earnings_research_job(symbol, earnings_date):
    """Create a new earnings research job in the database"""
    job_id = str(uuid.uuid4())
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
    INSERT INTO earnings_jobs (job_id, symbol, earnings_date, status, created_at)
    VALUES (?, ?, ?, ?, ?)
    ''', (job_id, symbol, earnings_date, 'pending', datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    
    conn.commit()
    conn.close()
    return job_id

def get_earnings_job(job_id):
    """Get a specific earnings research job by ID"""
    conn = get_db_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM earnings_jobs WHERE job_id = ?', (job_id,))
    job = cursor.fetchone()
    
    conn.close()
    return dict(job) if job else None

def get_earnings_jobs(symbol=None):
    """Get all earnings research jobs, optionally filtering by symbol"""
    conn = get_db_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    if symbol:
        cursor.execute('SELECT * FROM earnings_jobs WHERE symbol = ? ORDER BY created_at DESC', (symbol,))
    else:
        cursor.execute('SELECT * FROM earnings_jobs ORDER BY created_at DESC')
    
    jobs = cursor.fetchall()
    
    conn.close()
    return [dict(job) for job in jobs]

def update_earnings_job(job_id, status, result=None):
    """Update the status and result of an earnings research job"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if result:
        cursor.execute('''
        UPDATE earnings_jobs 
        SET status = ?, result = ?, completed_at = ?
        WHERE job_id = ?
        ''', (status, result, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), job_id))
    else:
        cursor.execute('''
        UPDATE earnings_jobs 
        SET status = ?
        WHERE job_id = ?
        ''', (status, job_id))
    
    conn.commit()
    conn.close()

def process_earnings_research(job_id, symbol, earnings_date, perplexity_model):
    """Background task to process the earnings research request"""
    try:
        # Update job status to processing
        update_earnings_job(job_id, 'processing')
        
        # Get company name and any position info from user's portfolio
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT Name FROM transactions WHERE Symbol = ? LIMIT 1', (symbol,))
        result = cursor.fetchone()
        company_name = result['Name'] if result else symbol
        
        # Get user's position in this stock if any
        cursor.execute('''
            SELECT 
                SUM(CASE WHEN Side = 'buy' THEN Qty ELSE -Qty END) as CurrentShares,
                SUM(CASE WHEN Side = 'buy' THEN Qty * AveragePrice ELSE 0 END) / 
                NULLIF(SUM(CASE WHEN Side = 'buy' THEN Qty ELSE 0 END), 0) as AverageCost
            FROM 
                transactions
            WHERE 
                Symbol = ?
        ''', (symbol,))
        
        position = cursor.fetchone()
        has_position = position and position['CurrentShares'] is not None and position['CurrentShares'] > 0
        
        # Get earnings history for this stock
        cursor.execute('''
            SELECT * FROM earnings_calendar 
            WHERE symbol = ? AND earnings_date < ?
            ORDER BY earnings_date DESC
            LIMIT 4
        ''', (symbol, earnings_date))
        
        past_earnings = cursor.fetchall()
        conn.close()
        
        # Get Perplexity client
        perplexity_api_key = os.getenv('PERPLEXITY_API_KEY')
        if not perplexity_api_key:
            update_earnings_job(job_id, 'failed', "Perplexity API key not configured")
            return
        
        perplexity_client = OpenAI(
            api_key=perplexity_api_key,
            base_url="https://api.perplexity.ai"
        )
        
        # Always use sonar-deep-research for earnings analysis
        model = 'sonar-deep-research'
        
        # Get current date for context
        current_date = datetime.now().strftime('%Y-%m-%d')
        
        # Build investor context based on portfolio position
        investor_context = ""
        if has_position:
            avg_cost = position['AverageCost'] if position['AverageCost'] is not None else 0
            current_shares = position['CurrentShares'] if position['CurrentShares'] is not None else 0
            
            # Get current price
            price_data = get_stock_price(symbol)
            current_price = price_data.get('current_price', 0) if price_data else 0
            
            if current_price and avg_cost:
                gain_loss_pct = ((current_price - avg_cost) / avg_cost) * 100
                investor_context = f"""
                The investor currently owns {int(current_shares)} shares of {symbol} at an average cost basis of ${avg_cost:.2f}.
                The current price is ${current_price:.2f}, representing a {'gain' if gain_loss_pct >= 0 else 'loss'} of {abs(gain_loss_pct):.1f}%.
                The investor would likely be particularly interested in how upcoming earnings might affect their position.
                """
        
        # Create a prompt for the earnings research with emphasis on rich visualizations and sources
        prompt = f"""Generate a comprehensive earnings preview research report for {symbol} ({company_name}) ahead of its earnings report on {earnings_date}.

Today's date is {current_date}, so this is forward-looking research to prepare an investor for the upcoming earnings announcement.

{investor_context}

Please structure your analysis with the following sections and provide visualization-friendly data wherever possible:

## Company Overview
- Brief business description
- Key products/services and revenue sources
- Recent major developments (last 3-6 months)

## Previous Earnings Performance
- Results from the last quarter
- Year-over-year growth metrics
- Stock price reaction to previous earnings announcements
- PROVIDE SPECIFIC NUMERICAL DATA for EPS estimates vs. actuals for the past 4 quarters that can be visualized in charts

## Current Quarter Expectations
- Consensus EPS and revenue estimates
- Whisper numbers and analyst sentiment
- Key metrics investors should focus on
- Include specific numerical forecasts with confidence intervals where possible

## Industry & Competitive Landscape
- Industry trends affecting the company
- Competitive positioning with market share percentages if available
- Market share changes
- INCLUDE NUMERICAL RANKINGS or scores for the company vs. competitors that can be visualized

## Recent News & Events
- Material news since last earnings
- Management commentary and guidance
- Analyst ratings changes
- Include exact dates for significant events

## Potential Catalysts & Risk Factors
- Specific things to watch for in this earnings report
- Upside and downside catalysts
- Potential areas of concern
- Quantify potential impacts where possible

## Technical Analysis
- Current price trends and key levels
- Volume patterns leading into earnings
- Historical price movements around earnings
- INCLUDE SPECIFIC PRICE POINTS and percentage moves for support/resistance

## Investment Thesis
- Bull case: What could drive outperformance
- Bear case: What could cause disappointment
- Expected impact on the stock price in various scenarios
- Include probability estimates for different outcomes

## Sources
- List ALL sources of information used in this analysis
- Include direct links to analyst reports, earnings call transcripts, SEC filings, and news articles
- Cite specific pages or sections of longer documents
- Provide publication dates for all sources

Format your response using proper Markdown syntax with clear section headings, bullet points, and emphasis where appropriate. Provide specific numbers, dates, and data points whenever possible. Be objective and balanced in presenting both bullish and bearish perspectives.

IMPORTANT: For visualizations, provide exact numerical data that can be rendered into interactive charts. The frontend will display your data as:
1. Price history chart with earnings dates marked
2. EPS estimates vs. actuals comparison chart
3. Investment sentiment pie chart
4. Industry comparison radar chart

Make sure to include all relevant numerical data for these visualizations.
"""
        
        # Call Perplexity API using the OpenAI client interface
        response = perplexity_client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are an expert financial analyst specializing in earnings previews. You provide comprehensive, well-researched analysis with specific data points, clear insights for investors, and properly sourced information. Always include extensive sources that are properly formatted and provide visualization-friendly data for interactive charts."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
            max_tokens=4000
        )
        
        if response and response.choices and len(response.choices) > 0:
            result = response.choices[0].message.content
            
            # Ensure the result contains proper markdown formatting
            # Add a main heading if not present
            if not result.startswith('# '):
                result = f"# Earnings Preview: {symbol} ({company_name}) - {earnings_date}\n\n{result}"
            
            # Ensure sources are properly formatted
            if "Sources:" in result and not "\n## Sources" in result:
                result = result.replace("Sources:", "\n## Sources\n")
            
            update_earnings_job(job_id, 'completed', result)
        else:
            update_earnings_job(job_id, 'failed', "No response received from the AI model")
    
    except Exception as e:
        print(f"Error processing earnings research job {job_id}: {str(e)}")
        update_earnings_job(job_id, 'failed', f"Error: {str(e)}")

@app.route('/earnings-companion', methods=['GET', 'POST'])
def earnings_companion():
    """Earnings Season Companion page"""
    # Get current settings
    settings = get_settings()
    
    # Store user's original model selection
    original_model = settings.get('perplexity_model', DEFAULT_PERPLEXITY_MODEL)
    
    # Force deep research model for earnings analysis
    settings['perplexity_model'] = 'sonar-deep-research'
    session['settings'] = settings
    
    # Check if Perplexity API is available
    perplexity_available = bool(os.getenv('PERPLEXITY_API_KEY'))
    if not perplexity_available:
        flash("Perplexity API is required for earnings analysis. Please set your API key in settings.", "warning")
        return redirect(url_for('settings'))
    
    # Process form submission for earnings research
    if request.method == 'POST':
        symbol = request.form.get('symbol')
        earnings_date = request.form.get('earnings_date')
        
        if symbol and earnings_date:
            # Create a job for the earnings research
            job_id = create_earnings_research_job(symbol, earnings_date)
            
            # Start a background thread to process the job
            thread = threading.Thread(
                target=process_earnings_research,
                args=(job_id, symbol, earnings_date, settings['perplexity_model'])
            )
            thread.daemon = True
            thread.start()
            
            flash(f"Earnings research job created for {symbol}. Check back in a minute for results.", "success")
            return redirect(url_for('earnings_companion'))
    
    # Get today's date
    today = datetime.now().date()
    
    # Get the earnings calendar for the next 90 days (increased from 30 days)
    end_date = (today + timedelta(days=90)).strftime('%Y-%m-%d')
    earnings_calendar = get_earnings_calendar(
        start_date=today.strftime('%Y-%m-%d'),
        end_date=end_date
    )
    
    # If calendar is empty, try to update it with API data first
    if not earnings_calendar:
        update_earnings_calendar()
        earnings_calendar = get_earnings_calendar(
            start_date=today.strftime('%Y-%m-%d'),
            end_date=end_date
        )
        
        # If still empty after update, try to populate with sample data
        if not earnings_calendar:
            try:
                from populate_earnings_data import populate_sample_earnings_data
                populate_sample_earnings_data()
                # Get the calendar data again after populating
                earnings_calendar = get_earnings_calendar(
                    start_date=today.strftime('%Y-%m-%d'),
                    end_date=end_date
                )
                if earnings_calendar:
                    flash("Earnings calendar has been populated with sample data.", "info")
            except Exception as e:
                flash(f"Could not populate earnings calendar: {str(e)}", "warning")
    
    # Get user's portfolio to highlight stocks
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT 
            Symbol,
            SUM(CASE WHEN Side = 'buy' THEN Qty ELSE -Qty END) as CurrentShares
        FROM 
            transactions
        GROUP BY 
            Symbol
        HAVING 
            CurrentShares > 0
    ''')
    
    portfolio_symbols = {row['Symbol']: row['CurrentShares'] for row in cursor.fetchall()}
    conn.close()
    
    # Mark portfolio stocks in the earnings calendar
    for entry in earnings_calendar:
        entry['in_portfolio'] = entry['symbol'] in portfolio_symbols
        if entry['in_portfolio']:
            entry['shares'] = portfolio_symbols[entry['symbol']]
    
    # Organize earnings by week
    earnings_by_week = {}
    
    for entry in earnings_calendar:
        # Parse earnings date
        earnings_date = datetime.strptime(entry['earnings_date'], '%Y-%m-%d').date()
        
        # Calculate week of year
        week_num = earnings_date.isocalendar()[1]
        year = earnings_date.year
        
        # Generate week ID
        week_id = f"Week {week_num}, {year}"
        
        # Add to appropriate week
        if week_id not in earnings_by_week:
            earnings_by_week[week_id] = []
        
        earnings_by_week[week_id].append(entry)
    
    # Get recent earnings research jobs
    earnings_jobs = get_earnings_jobs()
    
    # Restore user's original model selection before rendering
    settings['perplexity_model'] = original_model
    session['settings'] = settings
    
    return render_template(
        'earnings_companion.html',
        earnings_calendar=earnings_calendar,
        earnings_by_week=earnings_by_week,
        portfolio_symbols=portfolio_symbols,
        earnings_jobs=earnings_jobs,
        settings=settings,
        today=today
    )

@app.route('/earnings-job/<job_id>')
def earnings_job(job_id):
    """View earnings research job"""
    # Get current settings
    settings = get_settings()
    
    # Store user's original model selection
    original_model = settings.get('perplexity_model', DEFAULT_PERPLEXITY_MODEL)
    
    # Force deep research model for earnings research display
    settings['perplexity_model'] = 'sonar-deep-research'
    session['settings'] = settings
    
    job = get_earnings_job(job_id)
    if not job:
        flash('Job not found.', 'danger')
        return redirect(url_for('earnings_companion'))
    
    # If job is completed, convert markdown to HTML
    if job['status'] == 'completed' and job['result']:
        # Use the Python markdown library to convert markdown to HTML
        import markdown
        try:
            job['result'] = markdown.markdown(
                job['result'], 
                extensions=['tables', 'fenced_code', 'nl2br', 'extra']
            )
        except Exception as e:
            logger.error(f"Error converting markdown: {e}")
    
    # Restore user's original model selection before rendering
    settings['perplexity_model'] = original_model
    session['settings'] = settings
    
    return render_template(
        'earnings_job.html',
        job=job,
        settings=settings
    )

@app.route('/api/earnings-job/<job_id>', methods=['GET'])
def api_earnings_job(job_id):
    """API endpoint to get the status of an earnings research job"""
    job = get_earnings_job(job_id)
    
    if not job:
        return jsonify({"error": "Job not found"}), 404
    
    return jsonify(job)

@app.route('/api/earnings/calendar/update', methods=['POST'])
def api_update_earnings_calendar():
    """API endpoint to force update the earnings calendar"""
    success = update_earnings_calendar()
    
    if success:
        return jsonify({"status": "success", "message": "Earnings calendar updated successfully"})
    else:
        return jsonify({"status": "error", "message": "Failed to update earnings calendar"}), 500

def get_market_events(start_date=None, end_date=None, event_types=None, symbol=None):
    """
    Get market events like earnings releases, FOMC meetings, CPI releases, and stock splits
    filtered by date range, event types, and/or symbol.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Build the query with parameters
    query = "SELECT * FROM market_events WHERE 1=1"
    params = []
    
    if start_date:
        query += " AND event_date >= ?"
        params.append(start_date)
    
    if end_date:
        query += " AND event_date <= ?"
        params.append(end_date)
    
    if event_types:
        # Convert single string to list if needed
        if isinstance(event_types, str):
            event_types = [event_types]
        
        placeholders = ', '.join(['?' for _ in event_types])
        query += f" AND event_type IN ({placeholders})"
        params.extend(event_types)
    
    if symbol:
        query += " AND (symbol = ? OR symbol IS NULL)"
        params.append(symbol.upper())
    
    query += " ORDER BY event_date, event_time"
    
    cursor.execute(query, params)
    events = cursor.fetchall()
    
    # Convert to list of dictionaries for easier use in template
    event_list = []
    for event in events:
        event_dict = {
            'id': event['id'],
            'date': event['event_date'],
            'time': event['event_time'],
            'type': event['event_type'],
            'symbol': event['symbol'],
            'title': event['title'],
            'subtitle': event['subtitle'],
            'description': event['description'],
            'impact': event['impact_level']
        }
        event_list.append(event_dict)
    
    conn.close()
    return event_list

def get_fomc_meetings(start_date, end_date):
    """
    Fetch FOMC meeting dates from database or external API
    This is a placeholder function that would be replaced with actual
    implementation to fetch FOMC meeting dates from a reliable source
    """
    # For now, we'll hard-code some sample FOMC meetings
    # In a real implementation, you would fetch this from an API
    fomc_meetings = [
        {
            'date': '2025-01-29',
            'time': '14:00',
            'title': 'FOMC Interest Rate Decision',
            'subtitle': 'January 2025 Meeting',
            'description': 'The Federal Reserve announces its decision on interest rates after its two-day meeting.',
            'impact': 'high'
        },
        {
            'date': '2025-03-19',
            'time': '14:00',
            'title': 'FOMC Interest Rate Decision',
            'subtitle': 'March 2025 Meeting',
            'description': 'The Federal Reserve announces its decision on interest rates after its two-day meeting.',
            'impact': 'high'
        },
        {
            'date': '2025-05-07',
            'time': '14:00',
            'title': 'FOMC Interest Rate Decision',
            'subtitle': 'May 2025 Meeting',
            'description': 'The Federal Reserve announces its decision on interest rates after its two-day meeting.',
            'impact': 'high'
        }
    ]
    
    # Filter by date range
    start = datetime.strptime(start_date, '%Y-%m-%d').date()
    end = datetime.strptime(end_date, '%Y-%m-%d').date()
    
    filtered_meetings = [
        meeting for meeting in fomc_meetings 
        if start <= datetime.strptime(meeting['date'], '%Y-%m-%d').date() <= end
    ]
    
    return filtered_meetings

def get_cpi_releases(start_date, end_date):
    """
    Fetch CPI release dates from database or external API
    This is a placeholder function that would be replaced with actual
    implementation to fetch CPI release dates from a reliable source
    """
    # For now, we'll hard-code some sample CPI releases
    # In a real implementation, you would fetch this from an API
    cpi_releases = [
        {
            'date': '2025-01-14',
            'time': '08:30',
            'title': 'CPI Data Release',
            'subtitle': 'December 2024 Inflation Data',
            'description': 'The Bureau of Labor Statistics releases the Consumer Price Index data for December 2024.',
            'impact': 'high'
        },
        {
            'date': '2025-02-13',
            'time': '08:30',
            'title': 'CPI Data Release',
            'subtitle': 'January 2025 Inflation Data',
            'description': 'The Bureau of Labor Statistics releases the Consumer Price Index data for January 2025.',
            'impact': 'high'
        },
        {
            'date': '2025-03-12',
            'time': '08:30',
            'title': 'CPI Data Release',
            'subtitle': 'February 2025 Inflation Data',
            'description': 'The Bureau of Labor Statistics releases the Consumer Price Index data for February 2025.',
            'impact': 'high'
        }
    ]
    
    # Filter by date range
    start = datetime.strptime(start_date, '%Y-%m-%d').date()
    end = datetime.strptime(end_date, '%Y-%m-%d').date()
    
    filtered_releases = [
        release for release in cpi_releases 
        if start <= datetime.strptime(release['date'], '%Y-%m-%d').date() <= end
    ]
    
    return filtered_releases

def assess_impact_level(symbol, event_type):
    """
    Determines the impact level of an event on a particular stock
    This would use historical data and analytics in a real implementation
    """
    # Placeholder logic - in a real system this would be more sophisticated
    
    # For earnings announcements, use a simple baseline plus adjustments
    if event_type == 'earnings':
        # Baseline: All earnings have medium impact
        impact = 'medium'
        
        # Special cases for major companies
        if symbol in MAG7_STOCKS:
            impact = 'high'  # MAG7 earnings have high impact
            
        return impact
    
    # For stock splits, impact depends on the split ratio (not implemented here)
    elif event_type == 'split':
        return 'medium'
    
    # FOMC and CPI are typically high impact for the broader market
    elif event_type in ['fomc', 'cpi']:
        return 'high'
    
    # Default to medium impact if we can't determine
    return 'medium'

def update_market_events():
    """
    Updates the market_events table with the latest events
    This would run on a scheduled basis in a production environment
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Get earnings data from earnings_calendar table
    # This assumes the earnings_calendar is kept up to date
    cursor.execute('''
    SELECT symbol, company_name, earnings_date, time_of_day 
    FROM earnings_calendar 
    WHERE earnings_date >= date('now')
    ORDER BY earnings_date
    ''')
    earnings_events = cursor.fetchall()
    
    # Process earnings events
    for event in earnings_events:
        symbol = event['symbol']
        event_date = event['earnings_date']
        event_time = '16:00' if event['time_of_day'] == 'amc' else '09:30' if event['time_of_day'] == 'bmo' else '12:00'
        
        # Check if this event already exists
        cursor.execute('''
        SELECT id FROM market_events 
        WHERE event_date = ? AND event_type = 'earnings' AND symbol = ?
        ''', (event_date, symbol))
        existing = cursor.fetchone()
        
        if existing:
            # Update existing event
            cursor.execute('''
            UPDATE market_events 
            SET event_time = ?, 
                title = ?, 
                subtitle = ?, 
                description = ?, 
                impact_level = ?, 
                updated_at = ?
            WHERE id = ?
            ''', (
                event_time,
                f"{symbol} Earnings Release",
                f"{event['company_name']} Q4 2024 Earnings",
                f"{event['company_name']} ({symbol}) reports quarterly financial results.",
                assess_impact_level(symbol, 'earnings'),
                now,
                existing['id']
            ))
        else:
            # Insert new event
            cursor.execute('''
            INSERT INTO market_events 
            (event_date, event_time, event_type, symbol, title, subtitle, description, impact_level, source, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                event_date,
                event_time,
                'earnings',
                symbol,
                f"{symbol} Earnings Release",
                f"{event['company_name']} Q4 2024 Earnings",
                f"{event['company_name']} ({symbol}) reports quarterly financial results.",
                assess_impact_level(symbol, 'earnings'),
                'internal_earnings_calendar',
                now,
                now
            ))
    
    # Get stock splits
    # In a real implementation, you would query this from a reliable source or API
    # For now we'll use some placeholder data
    
    # Get FOMC meetings and add them to the database
    start_date = datetime.now().strftime('%Y-%m-%d')
    end_date = (datetime.now() + timedelta(days=180)).strftime('%Y-%m-%d')
    
    fomc_meetings = get_fomc_meetings(start_date, end_date)
    for meeting in fomc_meetings:
        # Check if this event already exists
        cursor.execute('''
        SELECT id FROM market_events 
        WHERE event_date = ? AND event_type = 'fomc'
        ''', (meeting['date'],))
        existing = cursor.fetchone()
        
        if existing:
            # Update existing event
            cursor.execute('''
            UPDATE market_events 
            SET event_time = ?, 
                title = ?, 
                subtitle = ?, 
                description = ?, 
                impact_level = ?, 
                updated_at = ?
            WHERE id = ?
            ''', (
                meeting['time'],
                meeting['title'],
                meeting['subtitle'],
                meeting['description'],
                meeting['impact'],
                now,
                existing['id']
            ))
        else:
            # Insert new event
            cursor.execute('''
            INSERT INTO market_events 
            (event_date, event_time, event_type, symbol, title, subtitle, description, impact_level, source, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                meeting['date'],
                meeting['time'],
                'fomc',
                None,  # FOMC events affect all stocks
                meeting['title'],
                meeting['subtitle'],
                meeting['description'],
                meeting['impact'],
                'fomc_calendar',
                now,
                now
            ))
    
    # Get CPI releases and add them to the database
    cpi_releases = get_cpi_releases(start_date, end_date)
    for release in cpi_releases:
        # Check if this event already exists
        cursor.execute('''
        SELECT id FROM market_events 
        WHERE event_date = ? AND event_type = 'cpi'
        ''', (release['date'],))
        existing = cursor.fetchone()
        
        if existing:
            # Update existing event
            cursor.execute('''
            UPDATE market_events 
            SET event_time = ?, 
                title = ?, 
                subtitle = ?, 
                description = ?, 
                impact_level = ?, 
                updated_at = ?
            WHERE id = ?
            ''', (
                release['time'],
                release['title'],
                release['subtitle'],
                release['description'],
                release['impact'],
                now,
                existing['id']
            ))
        else:
            # Insert new event
            cursor.execute('''
            INSERT INTO market_events 
            (event_date, event_time, event_type, symbol, title, subtitle, description, impact_level, source, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                release['date'],
                release['time'],
                'cpi',
                None,  # CPI events affect all stocks
                release['title'],
                release['subtitle'],
                release['description'],
                release['impact'],
                'economic_calendar',
                now,
                now
            ))
    
    conn.commit()
    conn.close()
    return True

# Add the new route for the Event Risk Calendar
@app.route('/event-risk-calendar')
def event_risk_calendar():
    # Get filter parameters from query string
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    event_types = request.args.getlist('event_types')
    symbol = request.args.get('symbol')
    
    # Set default values if not provided
    today = datetime.now().date()
    
    if not start_date:
        start_date = today.strftime('%Y-%m-%d')
    
    if not end_date:
        # Default to 30 days ahead
        end_date = (today + timedelta(days=30)).strftime('%Y-%m-%d')
    
    if not event_types:
        # Default to all event types
        event_types = ['earnings', 'fomc', 'cpi', 'split']
    
    # Parse dates for formatting in template
    start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
    end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
    
    # Calculate previous and next periods
    period_length = (end_date_obj - start_date_obj).days
    prev_period_start = (start_date_obj - timedelta(days=period_length)).strftime('%Y-%m-%d')
    prev_period_end = (start_date_obj - timedelta(days=1)).strftime('%Y-%m-%d')
    next_period_start = (end_date_obj + timedelta(days=1)).strftime('%Y-%m-%d')
    next_period_end = (end_date_obj + timedelta(days=period_length)).strftime('%Y-%m-%d')
    
    # Format dates for display
    start_date_formatted = start_date_obj.strftime('%b %d, %Y')
    end_date_formatted = end_date_obj.strftime('%b %d, %Y')
    
    # Ensure database is updated with recent events
    update_market_events()
    
    # Get events that match the filters
    events = get_market_events(start_date, end_date, event_types, symbol)
    
    # Render the template with the events and filter parameters
    return render_template(
        'event_risk_calendar.html',
        events=events,
        start_date=start_date,
        end_date=end_date,
        start_date_formatted=start_date_formatted,
        end_date_formatted=end_date_formatted,
        selected_event_types=event_types,
        symbol=symbol,
        prev_period_start=prev_period_start,
        prev_period_end=prev_period_end,
        next_period_start=next_period_start,
        next_period_end=next_period_end
    )

# Add API endpoint to manually trigger event updates
@app.route('/api/events/update', methods=['POST'])
def api_update_events():
    try:
        success = update_market_events()
        if success:
            return jsonify({'status': 'success', 'message': 'Market events updated successfully'})
        else:
            return jsonify({'status': 'error', 'message': 'Failed to update market events'}), 500
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

def get_company_logo(symbol):
    """
    Fetch and cache company logo for a given stock symbol.
    Returns the path to the cached logo or None if unable to fetch.
    """
    symbol = symbol.upper()
    local_path = os.path.join(LOGO_DIR, f"{symbol}.png")
    
    # Check if we already have this logo cached
    if os.path.exists(local_path):
        return url_for('static', filename=f'img/logos/{symbol}.png')
    
    # Try primary source: IEX Cloud API
    try:
        primary_url = f"https://storage.googleapis.com/iex/api/logos/{symbol}.png"
        response = requests.get(primary_url, stream=True, timeout=5)
        if response.status_code == 200:
            with open(local_path, 'wb') as f:
                response.raw.decode_content = True
                shutil.copyfileobj(response.raw, f)
            return url_for('static', filename=f'img/logos/{symbol}.png')
    except Exception as e:
        print(f"Error fetching primary logo for {symbol}: {e}")
    
    # Try alternate source: Fool.com
    try:
        alternate_url = f"https://g.foolcdn.com/art/companylogos/mark/{symbol.lower()}.png"
        response = requests.get(alternate_url, stream=True, timeout=5)
        if response.status_code == 200:
            with open(local_path, 'wb') as f:
                response.raw.decode_content = True
                shutil.copyfileobj(response.raw, f)
            return url_for('static', filename=f'img/logos/{symbol}.png')
    except Exception as e:
        print(f"Error fetching alternate logo for {symbol}: {e}")
    
    # Return a default placeholder if both sources fail
    return url_for('static', filename='img/logo.png')

# Add route to fetch company logo
@app.route('/api/company-logo/<symbol>')
def api_company_logo(symbol):
    """API endpoint to fetch and return a cached company logo"""
    logo_path = get_company_logo(symbol)
    if logo_path:
        return jsonify({'status': 'success', 'logo_url': logo_path})
    return jsonify({'status': 'error', 'message': 'Logo not found'})

# Add route to serve logo files directly
@app.route('/company-logo/<symbol>')
def company_logo(symbol):
    """Serve a company logo from cache or fetch it if not available"""
    symbol = symbol.upper()
    logo_path = get_company_logo(symbol)  # This will fetch and cache the logo if needed
    return redirect(logo_path)

def check_openai_api_health():
    """
    Check the health of the OpenAI API connection and log detailed information.
    Returns a dict with status information.
    """
    request_id = str(uuid.uuid4())[:8]
    logger.info(f"[{request_id}] Checking OpenAI API health")
    
    result = {
        "status": "unknown",
        "latency_ms": None,
        "error": None,
        "api_key_configured": False,
        "models_available": [],
        "details": {}
    }
    
    # Check if API key is configured
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        logger.error(f"[{request_id}] OpenAI API key not configured in environment variables")
        result["status"] = "failed"
        result["error"] = "API key not configured"
        return result
    
    # Mark that API key is configured
    result["api_key_configured"] = True
    
    # Check first 8 chars of API key (safe to log)
    key_prefix = api_key[:8] if len(api_key) >= 8 else "too_short"
    logger.info(f"[{request_id}] Using OpenAI API key with prefix: {key_prefix}...")
    
    # Try a simple API call to check connectivity
    try:
        start_time = time.time()
        
        # Try to list models as a simple API check
        models_response = openai_client.models.list()
        
        # Calculate latency
        latency = (time.time() - start_time) * 1000  # Convert to milliseconds
        result["latency_ms"] = round(latency, 2)
        
        # Get available models
        available_models = [model.id for model in models_response.data]
        result["models_available"] = available_models
        
        # Check if our main model (gpt-3.5-turbo) is available
        if "gpt-3.5-turbo" in available_models:
            result["status"] = "healthy"
            logger.info(f"[{request_id}] OpenAI API health check successful. Latency: {latency:.2f}ms")
            logger.info(f"[{request_id}] Available models: {', '.join(available_models[:5])}...")
        else:
            result["status"] = "degraded"
            result["error"] = "Required model 'gpt-3.5-turbo' not available"
            logger.warning(f"[{request_id}] OpenAI API is reachable but required model not available")
        
        # Now try a simple completion to fully verify API functionality
        start_time = time.time()
        completion = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Say 'API is working' if you can see this message."}
            ],
            max_tokens=20
        )
        
        # Calculate completion latency
        completion_latency = (time.time() - start_time) * 1000  # Convert to milliseconds
        result["details"]["completion_latency_ms"] = round(completion_latency, 2)
        
        # Check if we got a reasonable response
        response_content = completion.choices[0].message.content.strip()
        result["details"]["test_response"] = response_content
        
        if "API is working" in response_content or "working" in response_content.lower():
            result["status"] = "healthy"
            logger.info(f"[{request_id}] OpenAI completion test successful. Latency: {completion_latency:.2f}ms")
        else:
            result["status"] = "degraded"
            result["error"] = "Unexpected response from completion test"
            logger.warning(f"[{request_id}] OpenAI API completion test received unexpected response: {response_content}")
            
        # Add token usage information
        result["details"]["usage"] = {
            "prompt_tokens": completion.usage.prompt_tokens,
            "completion_tokens": completion.usage.completion_tokens,
            "total_tokens": completion.usage.total_tokens
        }
        
    except openai.RateLimitError as e:
        result["status"] = "rate_limited"
        result["error"] = str(e)
        logger.error(f"[{request_id}] OpenAI API rate limit exceeded: {str(e)}")
        
    except openai.APITimeoutError as e:
        result["status"] = "timeout"
        result["error"] = str(e)
        logger.error(f"[{request_id}] OpenAI API timeout error: {str(e)}")
        
    except openai.APIConnectionError as e:
        result["status"] = "connection_error"
        result["error"] = str(e)
        logger.error(f"[{request_id}] OpenAI API connection error: {str(e)}")
        
        # Check if it's a DNS resolution issue
        if "Could not resolve host" in str(e):
            logger.error(f"[{request_id}] DNS resolution issue detected. Cannot reach OpenAI API servers.")
            result["details"]["dns_issue"] = True
            
        # Check if it's a proxy issue
        if "Proxy" in str(e) or "proxy" in str(e):
            logger.error(f"[{request_id}] Possible proxy configuration issue.")
            result["details"]["proxy_issue"] = True
        
    except openai.AuthenticationError as e:
        result["status"] = "auth_error"
        result["error"] = "Authentication error - API key may be invalid"
        logger.error(f"[{request_id}] OpenAI API authentication error: {str(e)}")
        
    except openai.BadRequestError as e:
        result["status"] = "bad_request"
        result["error"] = str(e)
        logger.error(f"[{request_id}] OpenAI API bad request error: {str(e)}")
        
    except openai.APIError as e:
        result["status"] = "api_error"
        result["error"] = str(e)
        logger.error(f"[{request_id}] OpenAI API error: {str(e)}")
        
    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)
        logger.error(f"[{request_id}] Unexpected error checking OpenAI API health: {str(e)}")
        logger.error(f"[{request_id}] Error details: {traceback.format_exc()}")
    
    # Add network connectivity check
    try:
        # Test basic connectivity to OpenAI's domain
        response = requests.get("https://api.openai.com/health", timeout=5)
        result["details"]["network_connectivity"] = {
            "status_code": response.status_code,
            "reachable": True
        }
    except requests.RequestException as e:
        result["details"]["network_connectivity"] = {
            "reachable": False,
            "error": str(e)
        }
        logger.error(f"[{request_id}] Network connectivity issue to OpenAI API: {str(e)}")
    
    # Add system information
    result["details"]["system_info"] = {
        "platform": sys.platform,
        "python_version": sys.version.split()[0],
        "openai_package_version": openai.__version__
    }
    
    return result

@app.route('/api/check_openai', methods=['GET'])
def api_check_openai():
    """API endpoint to check OpenAI API health and return status information"""
    try:
        result = check_openai_api_health()
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error in API health check endpoint: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({
            "status": "error",
            "error": f"Error checking API health: {str(e)}"
        }), 500

if __name__ == '__main__':
    # Make sure the database exists
    init_db()
    
    # Initialize or refresh earnings data
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM earnings_calendar')
    earnings_count = cursor.fetchone()[0]
    
    # Get today's date to check if we have current earnings data
    today = datetime.now().date()
    end_date = (today + timedelta(days=90)).strftime('%Y-%m-%d')
    cursor.execute('SELECT COUNT(*) FROM earnings_calendar WHERE earnings_date BETWEEN ? AND ?', 
                   (today.strftime('%Y-%m-%d'), end_date))
    current_earnings_count = cursor.fetchone()[0]
    conn.close()
    
    # Either no earnings data or no current data in our date range
    if earnings_count == 0 or current_earnings_count == 0:
        try:
            print("Refreshing earnings calendar with sample data...")
            from populate_earnings_data import populate_sample_earnings_data
            populate_sample_earnings_data()
        except Exception as e:
            print(f"Error initializing earnings data: {e}")
    
    # Run the app on port 10000 with increased request timeout
    app.config['TIMEOUT'] = 120  # 2 minute timeout for requests
    app.run(debug=True, port=10000, threaded=True) 