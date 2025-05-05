#!/bin/bash

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check if Python is installed
if ! command_exists python3; then
    echo "Error: Python 3 is not installed. Please install Python 3 first."
    exit 1
fi

# Check if the OPENAI_API_KEY environment variable is set
if [ -z "$OPENAI_API_KEY" ]; then
    echo "Warning: OPENAI_API_KEY environment variable is not set."
    echo "The chatbot will fall back to static responses."
    echo "To enable ChatGPT integration, run: ./setup_env.sh YOUR_OPENAI_API_KEY"
    echo ""
fi

# Check if virtualenv is installed
if ! command_exists virtualenv; then
    echo "Installing virtualenv..."
    pip3 install virtualenv
fi

# Create and activate virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install requirements
echo "Installing dependencies..."
pip install -r requirements.txt

# Remove any existing database
echo "Removing any existing database..."
rm -f stock_transactions.db

# Ensure database is initialized
echo "Initializing database structure..."
python init_db.py

# Update earnings data
echo "Updating earnings calendar data..."
python populate_earnings_data.py

# Run Flask server
echo "Starting Flask server..."
echo "You can now upload your CSV file through the web interface."
export FLASK_APP=app.py
export FLASK_ENV=development
export FLASK_DEBUG=1
flask run --host=0.0.0.0 --port=10000