# TradeLens - AI-Powered Stock Portfolio Analysis

<div align="left">
  <img src="static/img/logos/tradelens-logo.svg" alt="TradeLens Logo" width="150" height="150">
</div>

TradeLens emerged as a solution to the challenges faced by investors in navigating the complexities of tariffs, market volatility, and the constant need to sift through news for portfolio-related information. This sophisticated web-based tool leverages advanced AI capabilities from Perplexity to provide a comprehensive platform for analyzing and visualizing stock portfolios. By uploading your stock transactions, you can gain valuable insights through interactive visualizations, risk assessments, and AI-driven analysis, making it easier to manage and optimize your investments amidst ever-changing market conditions.

## 📸 Screenshots & Features

### Dashboard Overview
![TradeLens Dashboard](static/img/dashboard_images/Dashboard%20Page.png)
The main dashboard provides a comprehensive view of your portfolio performance, with interactive charts, transaction summaries, and key metrics to help you monitor your investments at a glance.

### Stock Performance Visualization
![Stock Buy and Sell Plot](static/img/dashboard_images/Stock%20Buy%20and%20Sell%20Plot.png)
Visualize your stock transactions with an interactive chart showing buy and sell points plotted against historical price data, making it easy to evaluate your trading decisions.

### Transaction History
![Transactions](static/img/dashboard_images/Transactions.png)
A detailed view of all your transactions with sortable columns, allowing you to track your investment history and analyze your trading patterns over time.

### Perplexity AI Integration
![Perplexity Model Selector](static/img/dashboard_images/Perplexity%20Model%20selector.png)
Choose from various Perplexity AI models to power your analysis. Each model offers different capabilities, from quick answers to deep financial reasoning.

### Earnings Analysis
![Earnings Calendar](static/img/dashboard_images/Earnings%20calandar%20using%20deep%20research.png)
Track upcoming earnings announcements relevant to your portfolio with AI-enhanced insights on expected performance and potential impacts.

![Earnings Research](static/img/dashboard_images/Earnings%20research%20using%20sonar%20deepresearch.png)
Get detailed AI-powered research on company earnings, helping you make informed decisions before and after earnings releases.

### Risk Assessment
![Risk Analysis](static/img/dashboard_images/Risk%20Analysis.png)
Comprehensive risk analysis for your portfolio, identifying potential vulnerabilities and providing AI-powered recommendations to optimize your risk-return profile.

### Event Risk Calendar
![Event Risk Calendar](static/img/dashboard_images/Event%20risk%20calandar.png)
Stay ahead of market-moving events that might impact your portfolio. The calendar highlights critical dates and provides AI-generated insights about potential market impacts.

### Investment Thesis Validation
![Investment Thesis](static/img/dashboard_images/Investment%20Thesis.png)
Test and validate your investment hypotheses with AI analysis, providing deeper insights into your investment rationale.

### Strategy Backtesting
![Strategy Backtesting](static/img/dashboard_images/Strategy%20Backtracking.png)
Test investment strategies against historical data to evaluate performance and refine your approach before committing capital.

### Provider Settings
![Settings Page](static/img/dashboard_images/Settings%20page%20for%20Provider%20.png)
Configure your API providers and settings to customize the platform according to your needs and preferences.

## Key Features

### Core Functionality
- 📊 **Interactive Visualizations**: Dynamic stock price charts with buy/sell indicators
- 📈 **Transaction History**: Comprehensive view of all your trades with performance metrics
- 🔍 **Smart Filtering**: Categorize and analyze stocks by groups (MAG7, Other, Unlisted)
- 💼 **Portfolio Composition**: Visual breakdown of asset allocation and sector exposure

### AI-Powered Analysis
- 🤖 **Perplexity API Integration**: Leveraging advanced financial analysis capabilities
  - Deep market research for investment decisions
  - Real-time financial data analysis
  - Multiple model options (sonar, sonar-pro, sonar-reasoning, etc.)
- 💡 **Investment Thesis Validation**: Test your investment hypotheses with AI analysis
- 📊 **Earnings Season Companion**: AI-driven earnings preparation and analysis
- ⚠️ **Portfolio Risk Assessment**: Identify and analyze risk factors

### Advanced Features
- 📅 **Event Risk Calendar**: Track market-moving events that could impact your portfolio  
- 📈 **Strategy Backtesting**: Test investment strategies against historical data
- 🌐 **Tariff & Geopolitical Risk Analysis**: Assess external factors affecting your holdings
- 🤔 **Natural Language Queries**: Ask questions about your portfolio in plain English

## Getting Started

### Prerequisites

- Python 3.8 or higher
- pip (Python package installer)
- Perplexity API key (set in .env file)

### Installation

1. Clone the repository
```bash
git clone https://github.com/yourusername/tradelens.git
cd tradelens
```

2. Create and activate a virtual environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows, use: venv\Scripts\activate
```

3. Install dependencies
```bash
pip install -r requirements.txt
```

4. Set up your environment variables
```bash
cp .env.example .env
# Edit .env to add your Perplexity API key
```

### Running the Application

1. Start the server
```bash
./run_server.sh
```

2. Open your browser and navigate to:
```
http://localhost:5000
```

3. Upload your transaction data and start exploring your portfolio with AI-powered insights

## Technology Stack

- **Backend**: Python, Flask
- **Frontend**: HTML, CSS, JavaScript, Chart.js
- **AI Integration**: Perplexity API
- **Data Storage**: SQLite
- **Data Processing**: Pandas, NumPy

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.