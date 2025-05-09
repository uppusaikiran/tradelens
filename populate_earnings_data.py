import sqlite3
import random
from datetime import datetime, timedelta, date
import calendar

def populate_sample_earnings_data():
    """
    Populate the earnings_calendar table with sample data for testing the earnings companion.
    This creates a realistic earnings calendar with proper distribution of earnings dates
    clustering in specific weeks of the earnings season.
    """
    # Connect to the database
    conn = sqlite3.connect('stock_transactions.db')
    cursor = conn.cursor()
    
    # Get today's date
    today = datetime.now()
    
    # First clear existing data
    cursor.execute('DELETE FROM earnings_calendar')
    
    # Define sector-based stock groups for realistic clustering
    sector_stocks = {
        'Technology': [
            ('AAPL', 'Apple Inc.'),
            ('MSFT', 'Microsoft Corporation'),
            ('GOOGL', 'Alphabet Inc.'),
            ('AMZN', 'Amazon.com Inc.'),
            ('META', 'Meta Platforms Inc.'),
            ('NVDA', 'NVIDIA Corporation'),
            ('AMD', 'Advanced Micro Devices, Inc.'),
            ('INTC', 'Intel Corporation'),
            ('CSCO', 'Cisco Systems, Inc.'),
            ('ORCL', 'Oracle Corporation'),
            ('IBM', 'International Business Machines'),
            ('ADBE', 'Adobe Inc.'),
            ('CRM', 'Salesforce, Inc.'),
            ('PYPL', 'PayPal Holdings, Inc.'),
            ('NFLX', 'Netflix Inc.')
        ],
        'Consumer': [
            ('TSLA', 'Tesla Inc.'),
            ('DIS', 'The Walt Disney Company'),
            ('WMT', 'Walmart Inc.'),
            ('COST', 'Costco Wholesale Corporation'),
            ('TGT', 'Target Corporation'),
            ('HD', 'The Home Depot, Inc.'),
            ('SBUX', 'Starbucks Corporation'),
            ('MCD', 'McDonald\'s Corporation'),
            ('NKE', 'Nike, Inc.'),
            ('AMZN', 'Amazon.com Inc.')
        ],
        'Financial': [
            ('JPM', 'JPMorgan Chase & Co.'),
            ('BAC', 'Bank of America Corporation'),
            ('MS', 'Morgan Stanley'),
            ('GS', 'The Goldman Sachs Group, Inc.'),
            ('C', 'Citigroup Inc.'),
            ('WFC', 'Wells Fargo & Company'),
            ('V', 'Visa Inc.'),
            ('MA', 'Mastercard Incorporated'),
            ('AXP', 'American Express Company')
        ],
        'Healthcare': [
            ('JNJ', 'Johnson & Johnson'),
            ('PFE', 'Pfizer Inc.'),
            ('ABBV', 'AbbVie Inc.'),
            ('MRK', 'Merck & Co., Inc.'),
            ('UNH', 'UnitedHealth Group Incorporated'),
            ('CVS', 'CVS Health Corporation'),
            ('AMGN', 'Amgen Inc.'),
            ('MDT', 'Medtronic plc')
        ],
        'Communication': [
            ('T', 'AT&T Inc.'),
            ('VZ', 'Verizon Communications Inc.'),
            ('CMCSA', 'Comcast Corporation'),
            ('NFLX', 'Netflix Inc.'),
            ('DIS', 'The Walt Disney Company')
        ],
        'Energy': [
            ('XOM', 'Exxon Mobil Corporation'),
            ('CVX', 'Chevron Corporation'),
            ('COP', 'ConocoPhillips'),
            ('EOG', 'EOG Resources, Inc.'),
            ('SLB', 'Schlumberger Limited')
        ],
        'Industrial': [
            ('BA', 'The Boeing Company'),
            ('GE', 'General Electric Company'),
            ('CAT', 'Caterpillar Inc.'),
            ('UPS', 'United Parcel Service, Inc.'),
            ('HON', 'Honeywell International Inc.')
        ]
    }
    
    # Add some ETFs to exclude later
    etfs = [
        'SPY', 'QQQ', 'VOO', 'IVV', 'VTI', 'TQQQ', 'SQQQ', 'DIA', 'IJR', 'EFA', 
        'XLF', 'XLE', 'XLK', 'XLV', 'ARKK'
    ]
    
    # First try to get actual stocks from the database
    try:
        cursor.execute('''
            SELECT DISTINCT Symbol, Name
            FROM transactions
            GROUP BY Symbol
            HAVING SUM(CASE WHEN Side = 'buy' THEN Qty ELSE -Qty END) > 0
        ''')
        
        portfolio_stocks = cursor.fetchall()
        if portfolio_stocks:
            # Convert to list of tuples
            portfolio_stocks = [(row[0], row[1]) for row in portfolio_stocks]
        else:
            portfolio_stocks = []
    except:
        # If error, fall back to empty portfolio
        portfolio_stocks = []
    
    # Create a list of all stocks, prioritizing portfolio stocks
    all_stocks = []
    
    # Add all portfolio stocks first (if not ETFs)
    for symbol, name in portfolio_stocks:
        if symbol not in etfs:
            all_stocks.append((symbol, name))
    
    # Then add sector stocks (if not already added and not ETFs)
    for sector, stocks in sector_stocks.items():
        for symbol, name in stocks:
            if symbol not in etfs and symbol not in [s[0] for s in all_stocks]:
                all_stocks.append((symbol, name))
    
    # Define weeks of the earnings season
    # Calculate the start of the current quarter's earnings season
    today = date.today()
    today_month = today.month
    
    # Determine which quarter we're in
    if today_month in [1, 2, 3]:
        # Q4 earnings (Jan-Mar)
        earnings_quarter = "Q4"
        quarter_start_month = 1
    elif today_month in [4, 5, 6]:
        # Q1 earnings (Apr-Jun)
        earnings_quarter = "Q1"
        quarter_start_month = 4
    elif today_month in [7, 8, 9]:
        # Q2 earnings (Jul-Sep)
        earnings_quarter = "Q2"
        quarter_start_month = 7
    else:
        # Q3 earnings (Oct-Dec)
        earnings_quarter = "Q3"
        quarter_start_month = 10
    
    # If we're late in the quarter, move to next quarter's earnings
    days_left_in_quarter = 0
    if quarter_start_month == 1 and today_month == 3:
        days_left_in_quarter = 31 - today.day
    elif quarter_start_month == 4 and today_month == 6:
        days_left_in_quarter = 30 - today.day
    elif quarter_start_month == 7 and today_month == 9:
        days_left_in_quarter = 30 - today.day
    elif quarter_start_month == 10 and today_month == 12:
        days_left_in_quarter = 31 - today.day
    
    if days_left_in_quarter < 15:
        # Move to next quarter
        quarter_start_month = (quarter_start_month + 3) % 12
        if quarter_start_month == 0:
            quarter_start_month = 1
            
        if quarter_start_month == 1:
            earnings_quarter = "Q4"
        elif quarter_start_month == 4:
            earnings_quarter = "Q1"
        elif quarter_start_month == 7:
            earnings_quarter = "Q2"
        else:
            earnings_quarter = "Q3"
    
    # Set the start date to the 2nd week of the first month of the quarter
    # This is when earnings season typically begins
    earnings_season_year = today.year
    if today_month == 12 and quarter_start_month == 1:
        earnings_season_year += 1
        
    # Find the first Monday of the month
    first_day = date(earnings_season_year, quarter_start_month, 1)
    first_monday = first_day + timedelta(days=(calendar.MONDAY - first_day.weekday()) % 7)
    
    # Earnings season start is usually second week (first_monday + 7 days)
    earnings_season_start = first_monday + timedelta(days=7)
    
    # Define the weeks of earnings season (4 weeks total)
    earnings_weeks = [
        (earnings_season_start, earnings_season_start + timedelta(days=4)),  # Week 1 (Mon-Fri)
        (earnings_season_start + timedelta(days=7), earnings_season_start + timedelta(days=11)),  # Week 2 (Mon-Fri)
        (earnings_season_start + timedelta(days=14), earnings_season_start + timedelta(days=18)),  # Week 3 (Mon-Fri)
        (earnings_season_start + timedelta(days=21), earnings_season_start + timedelta(days=25)),  # Week 4 (Mon-Fri)
    ]
    
    # Financial companies typically report first
    sector_weeks = {
        'Financial': 0,  # First week
        'Healthcare': 1,  # Second week
        'Technology': 2,  # Third week
        'Consumer': 2,    # Third week
        'Communication': 2,  # Third week
        'Industrial': 3,  # Fourth week
        'Energy': 3       # Fourth week
    }
    
    # Dictionary to store assigned dates to avoid duplicates on same day
    assigned_dates = {}
    
    # Distribute stocks across the earnings season weeks based on sector
    for symbol, name in all_stocks:
        # Find which sector this stock belongs to
        stock_sector = None
        for sector, stocks in sector_stocks.items():
            if (symbol, name) in stocks or symbol in [s[0] for s in stocks]:
                stock_sector = sector
                break
        
        # If no sector found, assign randomly
        if not stock_sector:
            stock_sector = random.choice(list(sector_weeks.keys()))
        
        # Get the assigned week for this sector
        week_idx = sector_weeks[stock_sector]
        
        # Get the date range for this week
        week_start, week_end = earnings_weeks[week_idx]
        
        # Choose a random weekday within this week
        day_offset = random.randint(0, 4)  # 0-4 for Mon-Fri
        earnings_date = week_start + timedelta(days=day_offset)
        
        # Ensure we don't assign too many companies to the same day
        # This creates a more realistic distribution
        date_key = earnings_date.strftime('%Y-%m-%d')
        if date_key not in assigned_dates:
            assigned_dates[date_key] = 0
        
        # If too many companies on this day, try to find another day
        if assigned_dates[date_key] >= 4:  # Limit per day
            # Try another day in this week
            attempts = 0
            while attempts < 5:
                day_offset = random.randint(0, 4)
                earnings_date = week_start + timedelta(days=day_offset)
                date_key = earnings_date.strftime('%Y-%m-%d')
                
                if date_key not in assigned_dates:
                    assigned_dates[date_key] = 0
                    break
                    
                if assigned_dates[date_key] < 4:
                    break
                    
                attempts += 1
        
        assigned_dates[date_key] = assigned_dates.get(date_key, 0) + 1
        
        # Convert to string format for database
        earnings_date_str = earnings_date.strftime('%Y-%m-%d')
        
        # Assign time of day (BMO = Before Market Open, AMC = After Market Close)
        # Most companies report AMC (after market close)
        time_of_day = 'BMO' if random.random() < 0.3 else 'AMC'
        
        # Generate a reasonable EPS estimate based on stock price pattern
        # Higher stock symbols often have higher prices and higher EPS
        if symbol in ['AMZN', 'GOOGL', 'GOOG', 'AAPL', 'MSFT', 'META', 'NVDA']:
            eps_estimate = round(random.uniform(1.50, 5.00), 2)
        else:
            eps_estimate = round(random.uniform(0.25, 2.50), 2)
        
        cursor.execute('''
        INSERT INTO earnings_calendar (
            symbol, company_name, earnings_date, time_of_day, eps_estimate, last_updated
        ) VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            symbol, 
            name, 
            earnings_date_str, 
            time_of_day, 
            eps_estimate,
            today.strftime('%Y-%m-%d %H:%M:%S')
        ))
    
    # Commit changes
    conn.commit()
    conn.close()
    
    print(f"Sample earnings data created for {len(all_stocks)} stocks for {earnings_quarter} earnings season!")

if __name__ == "__main__":
    populate_sample_earnings_data() 