import sqlite3
import csv
from datetime import datetime

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
    
    # Clear existing data
    cursor.execute('DELETE FROM transactions')
    
    # Import data from CSV
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
    
    # Commit changes and close connection
    conn.commit()
    conn.close()
    print("Database initialized successfully!")

if __name__ == '__main__':
    init_db() 