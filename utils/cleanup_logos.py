#!/usr/bin/env python3
"""
Cleanup script for the company logo cache.
This script removes logos that are no longer used by any stocks in the portfolio
or earnings calendar to keep the cache size manageable.
"""

import os
import sqlite3
import time

# Path to logo directory
LOGO_DIR = os.path.join('static', 'img', 'logos')

def get_active_symbols():
    """Get all symbols currently in use in the database"""
    active_symbols = set()
    
    # Connect to database
    conn = sqlite3.connect('stock_transactions.db')
    cursor = conn.cursor()
    
    # Get symbols from transactions
    cursor.execute('SELECT DISTINCT Symbol FROM transactions')
    active_symbols.update(row[0].upper() for row in cursor.fetchall() if row[0])
    
    # Get symbols from earnings calendar
    cursor.execute('SELECT DISTINCT symbol FROM earnings_calendar')
    active_symbols.update(row[0].upper() for row in cursor.fetchall() if row[0])
    
    # Get symbols from market events
    cursor.execute('SELECT DISTINCT symbol FROM market_events WHERE symbol IS NOT NULL')
    active_symbols.update(row[0].upper() for row in cursor.fetchall() if row[0])
    
    conn.close()
    return active_symbols

def cleanup_logo_cache(keep_inactive_days=30):
    """
    Clean up the logo cache, removing logos that are:
    1. Not used by any active symbols
    2. Have not been accessed in the specified number of days
    """
    if not os.path.exists(LOGO_DIR):
        print(f"Logo directory {LOGO_DIR} does not exist. Nothing to clean up.")
        return
    
    # Get all active symbols
    active_symbols = get_active_symbols()
    print(f"Found {len(active_symbols)} active symbols in the database")
    
    # Get current time for comparing file access times
    current_time = time.time()
    time_threshold = current_time - (keep_inactive_days * 24 * 60 * 60)  # Convert days to seconds
    
    # Count statistics
    total_logos = 0
    removed_logos = 0
    kept_logos = 0
    
    # Check all logo files
    for filename in os.listdir(LOGO_DIR):
        if not filename.endswith(".png"):
            continue
        
        total_logos += 1
        filepath = os.path.join(LOGO_DIR, filename)
        symbol = os.path.splitext(filename)[0].upper()
        
        # Check if symbol is active
        if symbol in active_symbols:
            kept_logos += 1
            continue
        
        # Check when file was last accessed
        last_access_time = os.path.getatime(filepath)
        if last_access_time < time_threshold:
            print(f"Removing unused logo: {filename}")
            os.remove(filepath)
            removed_logos += 1
        else:
            kept_logos += 1
            
    print(f"Logo cleanup complete:")
    print(f"  Total logos: {total_logos}")
    print(f"  Kept logos: {kept_logos}")
    print(f"  Removed logos: {removed_logos}")

if __name__ == "__main__":
    print("Starting logo cache cleanup...")
    cleanup_logo_cache()
    print("Cleanup complete.") 