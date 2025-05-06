import sqlite3
import datetime

def check_earnings():
    conn = sqlite3.connect('stock_transactions.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Get earnings count
    cursor.execute('SELECT COUNT(*) FROM earnings_calendar')
    total_count = cursor.fetchone()[0]
    print(f"Total earnings entries: {total_count}")
    
    # Get today's date
    today = datetime.datetime.now().date()
    today_str = today.strftime('%Y-%m-%d')
    
    # Get upcoming earnings
    cursor.execute('SELECT COUNT(*) FROM earnings_calendar WHERE earnings_date >= ?', (today_str,))
    upcoming_count = cursor.fetchone()[0]
    print(f"Upcoming earnings entries: {upcoming_count}")
    
    # Get sample of upcoming earnings
    cursor.execute('''
        SELECT symbol, company_name, earnings_date, time_of_day, eps_estimate
        FROM earnings_calendar
        WHERE earnings_date >= ?
        ORDER BY earnings_date
        LIMIT 10
    ''', (today_str,))
    
    upcoming_earnings = cursor.fetchall()
    
    if upcoming_earnings:
        print("\nSample of upcoming earnings:")
        print(f"{'Symbol':<10} {'Date':<12} {'Time':<8} {'EST EPS':<10} {'Company'}")
        print("-" * 80)
        
        for earning in upcoming_earnings:
            eps = f"${earning['eps_estimate']:.2f}" if earning['eps_estimate'] is not None else "N/A"
            print(f"{earning['symbol']:<10} {earning['earnings_date']:<12} {earning['time_of_day'] or 'Unknown':<8} {eps:<10} {earning['company_name']}")
    else:
        print("\nNo upcoming earnings found!")
    
    # Check for entries by week
    print("\nUpcoming earnings by week:")
    for week_offset in range(0, 5):
        week_start = today + datetime.timedelta(days=week_offset*7)
        week_end = week_start + datetime.timedelta(days=6)
        
        cursor.execute('''
            SELECT COUNT(*) 
            FROM earnings_calendar 
            WHERE earnings_date BETWEEN ? AND ?
        ''', (week_start.strftime('%Y-%m-%d'), week_end.strftime('%Y-%m-%d')))
        
        week_count = cursor.fetchone()[0]
        print(f"Week {week_offset+1} ({week_start.strftime('%Y-%m-%d')} to {week_end.strftime('%Y-%m-%d')}): {week_count} earnings")
    
    # Check last updated timestamps
    cursor.execute('SELECT MIN(last_updated), MAX(last_updated) FROM earnings_calendar')
    min_date, max_date = cursor.fetchone()
    print(f"\nEarnings last updated: Oldest={min_date}, Newest={max_date}")
    
    conn.close()

if __name__ == "__main__":
    check_earnings() 