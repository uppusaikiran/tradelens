import os
import csv
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, jsonify, flash
import pandas as pd
import sqlite3
import yfinance as yf
import time

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Needed for flash messages

# In-memory cache for chart data
chart_cache = {}
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

def get_stock_price(symbol):
    try:
        stock = yf.Ticker(symbol)
        info = stock.info
        current_price = info.get('currentPrice', None)
        previous_close = info.get('previousClose', None)
        change = current_price - previous_close if current_price and previous_close else None
        change_percent = (change / previous_close * 100) if change and previous_close else None
        return {
            'current_price': current_price,
            'change': change,
            'change_percent': change_percent,
            'previous_close': previous_close,
            'error': None
        }
    except Exception as e:
        print(f"Error fetching stock price: {e}")
        return {
            'current_price': None,
            'change': None,
            'change_percent': None,
            'previous_close': None,
            'error': str(e)
        }

def get_stock_chart(symbol, start_date=None, range_='all'):
    try:
        stock = yf.Ticker(symbol)
        if range_ == 'all' or range_ == 'max':
            hist = stock.history(period="max")
        elif start_date:
            hist = stock.history(start=start_date)
        else:
            hist = stock.history(period="1mo")
        dates = hist.index.strftime('%Y-%m-%d').tolist()
        prices = hist['Close'].tolist()
        return {
            'dates': dates,
            'prices': prices,
            'error': None
        }
    except Exception as e:
        print(f"Error fetching stock chart: {e}")
        return {
            'dates': [],
            'prices': [],
            'error': str(e)
        }

def process_transactions(transactions):
    processed = []
    for t in transactions:
        date_obj = datetime.strptime(t['Date'], '%Y-%m-%d')
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
            'Fees': t['Fees']
        })
    return processed

@app.route('/api/stock_chart/<symbol>')
def api_stock_chart(symbol):
    range_ = request.args.get('range', 'ytd')
    today = datetime.today()
    if range_ == 'ytd':
        start_date = datetime(today.year, 1, 1)
    elif range_ == '1y':
        start_date = today - timedelta(days=365)
    elif range_ == '2y':
        start_date = today - timedelta(days=2*365)
    elif range_ == '5y':
        start_date = today - timedelta(days=5*365)
    elif range_ == 'max' or range_ == 'all':
        start_date = None
    else:
        start_date = today - timedelta(days=30)
    
    # Get transactions for this symbol
    conn = get_db_connection()
    query = 'SELECT Id, Date, Time, Side, AveragePrice, Qty FROM transactions WHERE Symbol = ?'
    params = [symbol]
    if start_date:
        query += ' AND Date >= ?'
        params.append(start_date.strftime('%Y-%m-%d'))
    
    cursor = conn.cursor()
    cursor.execute(query, params)
    transactions = cursor.fetchall()
    conn.close()
    
    # Process transactions for charting
    buy_transactions = []
    sell_transactions = []
    
    print(f"Found {len(transactions)} transactions for {symbol}")
    
    for tx in transactions:
        # Format date properly - it's stored as YYYY-MM-DD in SQLite
        date_str = tx['Date']
        # Skip if no price
        if not tx['AveragePrice']:
            continue
        try:
            # Format to match the chart date format
            price = float(tx['AveragePrice'])
            # Create a point
            point = {
                'id': tx['Id'],
                'date': date_str,
                'time': tx['Time'],
                'price': price,
                'qty': tx['Qty']  # Include exact quantity
            }
            if tx['Side'].lower() == 'buy':
                buy_transactions.append(point)
            else:
                sell_transactions.append(point)
        except (ValueError, TypeError) as e:
            print(f"Error processing transaction: {tx}, Error: {e}")
            continue
    
    print(f"Processed {len(buy_transactions)} buy and {len(sell_transactions)} sell transactions")
    
    # Get chart data
    chart_data = get_stock_chart(symbol, start_date=start_date.strftime('%Y-%m-%d') if start_date else None, range_=range_)
    
    # Add transaction data
    chart_data['buy_transactions'] = buy_transactions
    chart_data['sell_transactions'] = sell_transactions
    
    # Cache only the chart prices, not transactions (to ensure fresh transaction data)
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
    processed_transactions = process_transactions(transactions)
    return render_template('index.html', 
                         transactions=processed_transactions,
                         stocks=stocks,
                         page=page,
                         total_pages=total_pages,
                         current_filter=None)

@app.route('/stock/<symbol>')
def stock_detail(symbol):
    page = request.args.get('page', 1, type=int)
    per_page = 20
    side = request.args.get('side', 'all')
    range_ = request.args.get('range', 'ytd')
    today = datetime.today()
    if range_ == 'ytd':
        start_date = datetime(today.year, 1, 1)
    elif range_ == '1y':
        start_date = today - timedelta(days=365)
    elif range_ == '2y':
        start_date = today - timedelta(days=2*365)
    elif range_ == '5y':
        start_date = today - timedelta(days=5*365)
    elif range_ == 'max' or range_ == 'all':
        start_date = None
    else:
        start_date = today - timedelta(days=30)
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT DISTINCT Name FROM transactions WHERE Symbol = ?', (symbol,))
    stock_name = cursor.fetchone()[0]
    query = 'SELECT * FROM transactions WHERE Symbol = ?'
    params = [symbol]
    if side in ['buy', 'sell']:
        query += ' AND LOWER(Side) = ?'
        params.append(side)
    if start_date:
        query += ' AND Date >= ?'
        params.append(start_date.strftime('%Y-%m-%d'))
    cursor.execute(f'SELECT COUNT(*) FROM ({query})', params)
    total_transactions = cursor.fetchone()[0]
    total_pages = (total_transactions + per_page - 1) // per_page
    offset = (page - 1) * per_page
    query += ' ORDER BY Date DESC, Time DESC LIMIT ? OFFSET ?'
    params += [per_page, offset]
    cursor.execute(query, params)
    transactions = cursor.fetchall()
    cursor.execute('SELECT DISTINCT Symbol, Name FROM transactions ORDER BY Symbol')
    stocks = cursor.fetchall()
    conn.close()
    processed_transactions = process_transactions(transactions)
    # Only fetch price, not chart
    price_data = get_stock_price(symbol)
    return render_template('index.html', 
                         transactions=processed_transactions,
                         stocks=stocks,
                         current_filter=symbol,
                         stock_name=stock_name,
                         page=page,
                         total_pages=total_pages,
                         price_data=price_data,
                         selected_side=side,
                         selected_range=range_)

@app.route('/upload_csv', methods=['POST'])
def upload_csv():
    file = request.files['csvfile']
    if file and file.filename.endswith('.csv'):
        file.save('stock_orders.csv')
        flash('CSV uploaded successfully!', 'success')
    else:
        flash('Invalid file type.', 'danger')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True) 