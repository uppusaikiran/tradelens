import sqlite3
import datetime
import random

def fix_earnings_dates():
    conn = sqlite3.connect('stock_transactions.db')
    cursor = conn.cursor()
    
    # Get today's date
    today = datetime.datetime.now().date()
    
    # Calculate a range of dates for the next 30 days
    future_dates = []
    for i in range(1, 31):
        future_date = today + datetime.timedelta(days=i)
        # Only include weekdays (Monday to Friday)
        if future_date.weekday() < 5:  # 0-4 are Mon-Fri
            future_dates.append(future_date.strftime('%Y-%m-%d'))
    
    # Get all earnings
    cursor.execute('SELECT id, symbol, earnings_date FROM earnings_calendar')
    all_earnings = cursor.fetchall()
    
    print(f"Updating {len(all_earnings)} earnings entries...")
    
    # Update each earnings entry with a random future date
    for id, symbol, old_date in all_earnings:
        new_date = random.choice(future_dates)
        
        cursor.execute(
            'UPDATE earnings_calendar SET earnings_date = ? WHERE id = ?',
            (new_date, id)
        )
        
        print(f"Updated {symbol}: {old_date} -> {new_date}")
    
    # Update the last_updated timestamp
    today_str = today.strftime('%Y-%m-%d')
    cursor.execute('UPDATE earnings_calendar SET last_updated = ?', (today_str,))
    
    # Commit changes
    conn.commit()
    
    print(f"\nUpdated all earnings dates to be within the next 30 days.")
    print(f"Distribution of earnings by date:")
    
    # Show distribution
    cursor.execute('''
        SELECT earnings_date, COUNT(*) 
        FROM earnings_calendar 
        GROUP BY earnings_date 
        ORDER BY earnings_date
    ''')
    
    for date, count in cursor.fetchall():
        print(f"{date}: {count} earnings")
    
    conn.close()

if __name__ == "__main__":
    fix_earnings_dates() 