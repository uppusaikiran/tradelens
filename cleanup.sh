#!/bin/bash

# Script to clean up unwanted files across the repository

echo "Cleaning up database and cache files..."

# Remove the database
rm -f stock_transactions.db

# Clean up any temporary files
find . -name "*.pyc" -delete
find . -name "__pycache__" -exec rm -rf {} +
find . -name ".DS_Store" -delete

# Clean up the logo cache directory
echo "Cleaning up logo cache..."
rm -rf static/img/logos/*

# Remove empty or temporary files
echo "Removing temporary files..."
rm -f temp.html
rm -rf tmp

# Optional: Remove node_modules (uncomment if needed)
# echo "Removing node_modules..."
# rm -rf node_modules

echo "Cleanup complete!" 