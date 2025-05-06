import sqlite3
import csv
from datetime import datetime
import uuid

def safe_float(value):
    try:
        return float(value) if value and value.lower() != 'null' else 0.0
    except ValueError:
        return 0.0

def init_db():
    # Connect to SQLite database (creates it if it doesn't exist)
    conn = sqlite3.connect('stock_transactions.db')
    cursor = conn.cursor()
    
    # Create transactions table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        Date DATE,
        Time TEXT,
        Symbol TEXT,
        Name TEXT,
        Type TEXT,
        Side TEXT,
        AveragePrice REAL,
        Qty REAL,
        State TEXT,
        Fees REAL
    )
    ''')
    
    # Create thesis_jobs table if it doesn't exist
    cursor.execute('''
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
    cursor.execute('''
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
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS earnings_calendar (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        symbol TEXT NOT NULL,
        company_name TEXT,
        earnings_date TEXT NOT NULL,
        time_of_day TEXT,
        eps_estimate REAL,
        last_updated TEXT NOT NULL
    )
    ''')
    
    # Create market_events table for storing important financial events
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS market_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_date DATE NOT NULL,
        event_time TEXT,
        event_type TEXT NOT NULL, 
        symbol TEXT,
        title TEXT NOT NULL,
        subtitle TEXT,
        description TEXT,
        impact_level TEXT NOT NULL,
        source TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    ''')
    
    # Clear existing transaction data if specified
    # cursor.execute('DELETE FROM transactions')
    
    # Try to import data if CSV exists and transactions table is empty
    cursor.execute('SELECT COUNT(*) FROM transactions')
    if cursor.fetchone()[0] == 0:
        try:
            with open('stock_orders.csv', 'r') as file:
                csv_reader = csv.DictReader(file)
                for row in csv_reader:
                    try:
                        # Convert date string to SQLite date format
                        date_obj = datetime.strptime(row['Date'], '%m/%d/%Y')
                        date_str = date_obj.strftime('%Y-%m-%d')
                        
                        cursor.execute('''
                        INSERT INTO transactions (Date, Time, Symbol, Name, Type, Side, AveragePrice, Qty, State, Fees)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            date_str,
                            row['Time'],
                            row['Symbol'],
                            row['Name'],
                            row['Type'],
                            row['Side'],
                            safe_float(row['AveragePrice']),
                            safe_float(row['Qty']),
                            row['State'],
                            safe_float(row['Fees'])
                        ))
                    except Exception as e:
                        print(f"Error processing row: {row}")
                        print(f"Error: {e}")
                        continue
        except FileNotFoundError:
            print("No CSV file found. Created empty database.")
    else:
        print("Transactions table already contains data, skipping import.")
    
    # Commit changes and close connection
    conn.commit()
    conn.close()
    print("Database initialized successfully!")

if __name__ == '__main__':
    init_db() 