# AI-Powered Features

TradeLens leverages advanced AI capabilities through the Perplexity API to provide intelligent insights and analysis for your investment portfolio. This guide explains the AI features available and how to use them effectively.

## AI Provider Options

TradeLens supports multiple AI models, with Perplexity being the primary provider:

![Perplexity Model Selector](../../static/img/dashboard_images/Perplexity%20Model%20selector.png)

### Available Models

| Model | Description | Best For |
|-------|-------------|----------|
| sonar | Fast, versatile model for general queries | Quick portfolio insights |
| sonar-pro | Enhanced version with better analysis capabilities | Detailed financial analysis |
| sonar-reasoning | Better reasoning capabilities for complex questions | Strategic investment decisions |
| sonar-reasoning-pro | Enhanced reasoning for advanced financial analysis | In-depth strategy validation |
| sonar-deep-research | Comprehensive research capabilities | Thorough stock analysis |
| r1-1776 | Specialized for US market analysis | US-focused portfolio analysis |
| llama-3.1-sonar-small | Lightweight, efficient model | Basic queries with faster response |

## Conversational AI Interface

The AI chat interface allows you to interact with TradeLens using natural language:

### Example Queries

- **Portfolio Analysis**: "What are my top 3 performing stocks this year?"
- **Market Insights**: "How might rising interest rates affect my tech stocks?"
- **Investment Advice**: "Given my current portfolio, what sectors am I underexposed to?"
- **Stock Analysis**: "What are the key risks and opportunities for AAPL right now?"
- **Economic Impact**: "How could the recent tariff changes affect my semiconductor holdings?"

### Using the Chat Interface

1. Type your question in the chat input field
2. Select the appropriate AI model for your query type
3. Click Send or press Enter
4. Review the AI's response
5. Ask follow-up questions to dive deeper

The AI maintains context throughout your conversation, so you can refer to previous questions and build on earlier discussions.

## Thesis Validation

The Investment Thesis Validation feature uses AI to evaluate investment hypotheses:

![Investment Thesis](../../static/img/dashboard_images/Investment%20Thesis.png)

### How to Use Thesis Validation

1. Navigate to the Thesis Validation page
2. Enter your investment thesis (e.g., "AI stocks will outperform in Q3 2025")
3. Select your preferred AI model (sonar-deep-research recommended)
4. Click "Validate Thesis"
5. The AI will analyze your thesis and provide:
   - Overall assessment (Supported, Partially Supported, Not Supported)
   - Supporting evidence and arguments
   - Counterarguments and risks
   - Related factors to consider
   - Suggested modifications to the thesis

### Example Theses

TradeLens provides example theses you can select from the dropdown, including:

- "AI stocks will outperform in Q3 2025"
- "Renewable energy sector will see growth due to recent policy changes"
- "Semiconductor stocks will face headwinds from supply chain disruptions"
- "Fintech companies will benefit from rising interest rates"

## Earnings Analysis

The Earnings Analysis feature provides AI-powered insights for upcoming earnings announcements:

![Earnings Calendar](../../static/img/dashboard_images/Earnings%20calandar%20using%20deep%20research.png)

![Earnings Research](../../static/img/dashboard_images/Earnings%20research%20using%20sonar%20deepresearch.png)

### Earnings Calendar

The earnings calendar shows upcoming earnings announcements for stocks in your portfolio:

1. Navigate to the Earnings Companion page
2. View upcoming earnings events for your holdings
3. Click on a stock to initiate earnings research

### Earnings Research

The AI provides detailed analysis for upcoming earnings:

1. Select a stock from your portfolio
2. View the upcoming earnings date
3. Click "Research Earnings"
4. The AI will generate a comprehensive report including:
   - Key metrics to watch
   - Analyst expectations
   - Recent company developments
   - Potential catalysts
   - Risk factors
   - Historical earnings performance
   - Post-earnings price movement predictions

## Risk Assessment

The AI-powered Risk Assessment tool analyzes potential risks in your portfolio:

![Risk Analysis](../../static/img/dashboard_images/Risk%20Analysis.png)

### Risk Analysis Features

1. **Tariff and Supply Chain Risk**: Analysis of how trade policies and supply chain issues might impact your holdings
2. **Sector-Specific Risks**: Identification of risks unique to different sectors in your portfolio
3. **Geopolitical Risk Assessment**: Evaluation of how global events might affect your investments
4. **Concentration Risk**: Analysis of over-exposure to specific stocks, sectors, or regions
5. **Volatility Analysis**: Assessment of portfolio volatility and suggestions for stabilization

### Using Risk Assessment

1. Navigate to the Risk Review page
2. View the AI-generated risk overview for your entire portfolio
3. Select specific stocks to see detailed risk analysis
4. Review recommendations for risk mitigation

## Strategy Backtesting

The Strategy Backtesting feature uses AI to simulate how your portfolio would perform under various historical market conditions:

![Strategy Backtesting](../../static/img/dashboard_images/Strategy%20Backtracking.png)

### Available Scenarios

- **COVID-19 Recovery**: How your current portfolio would have performed during the pandemic recovery
- **2020 Market Crash**: Simulation of your portfolio during the March 2020 crash
- **AI Tech Boom**: Performance during the recent AI technology boom
- **2023 Banking Crisis**: Reaction to banking sector instability

### Using Strategy Backtesting

1. Navigate to the Strategy Backtesting page
2. Select a historical scenario from the dropdown
3. Click "Run Simulation"
4. Review the AI-generated analysis showing:
   - Simulated portfolio performance
   - Individual stock reactions
   - Key lessons from the scenario
   - Suggestions to improve resilience

## Event Risk Calendar

The Event Risk Calendar uses AI to track market-moving events that could impact your portfolio:

![Event Risk Calendar](../../static/img/dashboard_images/Event%20risk%20calandar.png)

### Calendar Features

1. **Personalized Impact Assessment**: AI-calculated impact level for each event based on your holdings
2. **Event Categories**: Economic releases, Fed meetings, earnings, geopolitical events, etc.
3. **Automatic Updates**: Calendar is regularly refreshed with new events
4. **Filtering Options**: Filter by date range, event type, or impact level

### Using the Event Calendar

1. Navigate to the Event Risk Calendar page
2. View upcoming events relevant to your portfolio
3. Click on events to see detailed AI analysis
4. Set notification preferences for high-impact events

## AI Model Selection Tips

- **For quick insights**: Use sonar or llama-3.1-sonar-small
- **For in-depth analysis**: Use sonar-deep-research or sonar-reasoning-pro
- **For strategic decision making**: Use sonar-reasoning or sonar-reasoning-pro
- **For US market focus**: Use r1-1776
- **For the most detailed research**: Use sonar-deep-research

## Troubleshooting AI Features

- **Slow responses**: Try switching to a lighter model like sonar or llama-3.1-sonar-small
- **Vague analysis**: Provide more specific questions and select a more advanced model
- **Error messages**: Check your API key in settings and verify you haven't exceeded usage limits
- **Inconsistent results**: Try reformulating your question with more context about your portfolio

For more information on the technical implementation of AI features, see the [AI Integration](../development/ai_integration.md) documentation. 