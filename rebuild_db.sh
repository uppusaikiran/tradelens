#!/bin/bash

echo "Rebuilding the database..."

# Backup the existing database if it exists
if [ -f "stock_transactions.db" ]; then
    echo "Backing up existing database..."
    timestamp=$(date +"%Y%m%d_%H%M%S")
    cp stock_transactions.db "stock_transactions_backup_$timestamp.db"
    echo "Backup created: stock_transactions_backup_$timestamp.db"
fi

# Initialize the database with all tables
echo "Creating database structure..."
python3 init_db.py

# Populate sample earnings data
echo "Adding sample earnings data..."
python3 populate_earnings_data.py

echo "Database rebuilt successfully!"
echo "You can now run the application with: python3 app.py" 