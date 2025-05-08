#!/bin/bash

echo "Cleaning up the environment..."

# Stop any running Flask processes
echo "Stopping any running Flask servers..."
pkill -f "flask run"

# Remove the database
echo "Removing database..."
rm -f stock_transactions.db

# Remove Python cache files
echo "Removing Python cache files..."
find . -type d -name "__pycache__" -exec rm -r {} +
find . -type f -name "*.pyc" -delete

# Remove any log files if they exist
echo "Removing log files..."
rm -f *.log

# Remove stock orders CSV file
echo "Removing stock orders CSV file..."
rm -f stock_orders.csv

echo "Cleanup complete! You can now run ./run_server.sh to start fresh." 