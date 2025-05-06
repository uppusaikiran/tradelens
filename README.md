# TradeLens - AI-Powered Stock Portfolio Analysis

<div align="left">
  <img src="static/img/logo.png" alt="TradeLens Logo" width="150" height="150">
</div>

TradeLens emerged as a solution to the challenges faced by investors in navigating the complexities of tariffs, market volatility, and the constant need to sift through news for portfolio-related information. This sophisticated web-based tool leverages advanced AI capabilities from Perplexity to provide a comprehensive platform for analyzing and visualizing stock portfolios. By uploading your stock transactions, you can gain valuable insights through interactive visualizations, risk assessments, and AI-driven analysis, making it easier to manage and optimize your investments amidst ever-changing market conditions.

## 📸 Screenshot

![Application Screenshot](Screenshot.png)

## Key Features

### Core Functionality
- 📊 Interactive stock price charts with buy/sell indicators
- 📈 Transaction history visualization with detailed metrics
- 🔍 Smart filtering by stock categories (MAG7, Other, Unlisted)
- 💼 Portfolio composition analysis

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

## Getting Started

### Prerequisites

- Python 3.8 or higher
- pip (Python package installer)

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

### Running the Application

1. Start the server
```bash
./run_server.sh
```

2. Open your browser and navigate to:
```
http://localhost:5000
```

3. Configure your Perplexity API key for enhanced AI features:
```bash
./setup_env.sh [YOUR_PERPLEXITY_API_KEY]
```

### Data Format

Upload your stock orders CSV file with the following columns:
- Symbol
- Name
- AveragePrice
- Qty
- Type
- Side
- Fees
- State
- Date (MM/DD/YYYY)
- Time

### Clean Up

To clean the environment and start fresh:
```bash
./clean.sh
```

## Problem & Inspiration

### The Challenge

Individual investors face several critical challenges:
- Information overload from various financial sources
- Difficulty in validating investment theses with reliable data
- Limited tools to assess portfolio risks from various angles
- Lack of preparation for company earnings and market events

### Our Solution

TradeLens was created to democratize advanced portfolio analysis for individual investors. By combining financial data visualization with Perplexity's AI capabilities, we've built a platform that provides:

1. Data-driven insights previously available only to institutional investors
2. Easy-to-understand visualizations of complex financial information
3. AI-powered analysis that goes beyond standard metrics
4. Proactive tools for earnings seasons and market events

## Perplexity AI Integration

TradeLens extensively uses Perplexity AI for several advanced financial analysis features:

### 1. Investment Thesis Validation
- Evaluates custom investment theses against current market data
- Uses Perplexity's reasoning capabilities to identify supporting and contradicting evidence
- Provides actionable insights on thesis viability

### 2. Earnings Season Companion
- Prepares deep-dive research on upcoming earnings announcements
- Analyzes historical earnings patterns and market expectations
- Provides comprehensive risk assessments specific to earnings events

### 3. Event Risk Calendar
- Utilizes Perplexity to assess the potential impact of upcoming market events
- Analyzes how FOMC meetings, CPI releases, and other events might affect specific holdings
- Provides personalized risk ratings based on portfolio composition

### 4. Portfolio Chat Assistant
- Allows natural language queries about portfolio performance
- Answers complex questions about stock fundamentals, market trends, and investment strategies
- Provides contextual financial analysis specific to user holdings

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [Perplexity AI](https://www.perplexity.ai/) for the powerful AI capabilities
- [ApexCharts.js](https://apexcharts.com/) for the interactive charts
- [Bootstrap](https://getbootstrap.com/) for the responsive design
- [Flask](https://flask.palletsprojects.com/) for the web framework
