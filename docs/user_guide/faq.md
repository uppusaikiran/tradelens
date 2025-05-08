# Frequently Asked Questions (FAQ)

## General Questions

### What is TradeLens?
TradeLens is an AI-powered stock portfolio analysis tool that helps investors track, analyze, and optimize their investments. It uses advanced AI capabilities from Perplexity to provide insights and visualizations for your stock portfolio.

### Is TradeLens free to use?
TradeLens itself is free and open-source. However, to use the AI features, you need a Perplexity API key, which may require a subscription from Perplexity.

### What are the system requirements?
TradeLens requires:
- Python 3.8 or higher
- Modern web browser
- Internet connection for AI features
- Approximately 100MB of disk space

## Data and Privacy

### Is my financial data secure?
Yes. TradeLens is designed to run locally on your machine. Your financial data is stored in a local SQLite database and is not sent to external servers (except when needed for AI analysis through the Perplexity API).

### Does TradeLens store my API keys?
API keys are stored in your local `.env` file. They are never sent to any server other than the respective API provider (Perplexity).

### Can I export my data from TradeLens?
Currently, there's no built-in export functionality, but since your data is stored in a SQLite database, you can access it directly or query it using SQLite tools.

## Features and Usage

### How do I add stocks to my portfolio?
Upload a CSV file containing your stock transactions. The file should include columns for Date, Symbol, Name, Type, Side (Buy/Sell), AveragePrice, Qty, etc.

### Can TradeLens predict stock prices?
TradeLens is not designed to predict stock prices. While the AI features can provide analysis and insights based on historical data and current trends, they should not be considered as investment advice or price predictions.

### How accurate is the AI analysis?
The AI analysis is based on information available to the Perplexity models up to their training cutoff date. The quality of analysis depends on the model used and the specificity of your questions. Always verify information through other sources before making investment decisions.

### Can I use TradeLens without the AI features?
Yes, many features of TradeLens work without the AI integration, including portfolio tracking, visualization, and basic analysis. However, the advanced insights and natural language query capabilities require the AI integration.

## Troubleshooting

### The application won't start. What should I check?
1. Verify Python is installed and is version 3.8 or higher
2. Check that all dependencies are installed (`pip install -r requirements.txt`)
3. Look at the app.log file for error messages
4. Ensure the database file (stock_transactions.db) exists and isn't corrupted

### Why am I getting API errors?
If you're seeing errors related to the Perplexity API:
1. Check that your API key is correct in the .env file
2. Verify you haven't exceeded your API rate limits
3. Check if the Perplexity service is experiencing any outages
4. Try a different AI model in the settings

### My stock data isn't displaying correctly. How can I fix it?
1. Verify your CSV file format matches the expected format
2. Check the database directly to see if the data was imported correctly
3. Try rebuilding the database with the rebuild_db.sh script
4. If problems persist, try manually entering some transactions through the database

### Why does the application run slowly?
1. On first load, TradeLens might be fetching data for multiple stocks
2. Large transaction histories can slow down processing
3. AI-powered features require API calls that may take a few seconds
4. Limited system resources (RAM, CPU) can impact performance

## Development and Customization

### Can I contribute to TradeLens?
Yes! TradeLens is open-source and contributions are welcome. See the [Development Guide](../development/index.md) for more information.

### How can I extend TradeLens with additional features?
You can modify the codebase to add new features. The application is written in Python using Flask, so knowledge of these technologies is helpful. See the [Project Structure](../development/project_structure.md) document for guidance.

### Is there an API I can use to integrate with other tools?
TradeLens provides a set of API endpoints that you can use to interact with the application programmatically. See the [API Documentation](../api/index.md) for details. 