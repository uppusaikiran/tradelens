# Getting Started with TradeLens

This guide walks you through the process of installing, configuring, and starting to use TradeLens.

## Prerequisites

Before you begin, make sure you have the following:

- Python 3.8 or higher installed
- pip (Python package installer)
- A Perplexity API key (for AI-powered features)
- Your stock transaction data in CSV format

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/tradelens.git
cd tradelens
```

### 2. Create and Activate a Virtual Environment

```bash
python -m venv venv
```

On macOS/Linux:
```bash
source venv/bin/activate
```

On Windows:
```bash
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Set Up Environment Variables

Create a `.env` file in the root directory with the following content:

```
PERPLEXITY_API_KEY=your_perplexity_api_key
OPENAI_API_KEY=your_openai_api_key (optional)
```

Replace `your_perplexity_api_key` with your actual Perplexity API key.

## Initial Setup

### 1. Initialize the Database

```bash
python init_db.py
```

This will create the SQLite database that stores transaction data and other information.

### 2. Start the Server

```bash
./run_server.sh
```

Or on Windows:
```bash
python app.py
```

### 3. Access the Application

Open your web browser and navigate to:
```
http://localhost:5000
```

## Uploading Transaction Data

1. Prepare your transaction data in CSV format with the following columns:
   - Date (MM/DD/YYYY)
   - Time
   - Symbol
   - Name
   - Type
   - Side (Buy/Sell)
   - AveragePrice
   - Qty
   - State
   - Fees

2. From the TradeLens dashboard, click on the "Upload Transactions" button.

3. Select your CSV file and click "Upload."

4. Once uploaded, your transaction data will be processed and displayed on the dashboard.

## Configuring Settings

1. Navigate to the Settings page by clicking on the gear icon in the navigation bar.

2. Set your preferred AI provider (Perplexity is recommended).

3. Choose your default Perplexity model based on your needs:
   - sonar: Fast responses for general queries
   - sonar-pro: Enhanced analysis capabilities
   - sonar-reasoning: Better reasoning for complex financial questions
   - sonar-deep-research: In-depth research and comprehensive analysis

4. Save your settings.

## Next Steps

Once you've completed the setup and uploaded your transaction data, you can:

- [Explore the dashboard](dashboard.md) to visualize your portfolio
- [Analyze your portfolio composition](portfolio_analysis.md)
- [Use AI features](ai_features.md) to gain investment insights
- [Track upcoming earnings](earnings_analysis.md) for your stocks
- [Assess portfolio risks](risk_assessment.md)

## Troubleshooting

If you encounter any issues during setup or usage:

1. Check the application logs (`app.log`) for error messages
2. Verify that your API keys are correctly set in the `.env` file
3. Ensure your transaction CSV file is properly formatted
4. Make sure all dependencies are installed correctly 