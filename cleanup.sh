#!/bin/bash

# Script to clean up unwanted files across the repository

echo "Cleaning up repository..."

# Remove Python cache files
echo "Removing Python cache files..."
find . -name "__pycache__" -type d -exec rm -rf {} +
find . -name "*.pyc" -delete
find . -name "*.pyo" -delete
find . -name "*.pyd" -delete

# Remove empty or temporary files
echo "Removing temporary files..."
rm -f temp.html
rm -rf tmp

# Optional: Remove node_modules (uncomment if needed)
# echo "Removing node_modules..."
# rm -rf node_modules

echo "Cleanup complete!" 