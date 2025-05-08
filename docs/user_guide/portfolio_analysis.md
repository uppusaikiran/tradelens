# Portfolio Analysis

TradeLens provides powerful portfolio analysis tools to help you understand your investments, track performance, and make informed decisions.

## Portfolio Overview

The portfolio overview gives you a high-level summary of your investment portfolio:

- **Total Value**: The current market value of all your holdings
- **Total Cost Basis**: The amount you've invested
- **Total Gain/Loss**: The difference between current value and cost basis
- **Performance Metrics**: Return on investment, annualized returns, etc.

## Holdings Breakdown

![Portfolio Composition](../../static/img/dashboard_images/Strategy%20Backtracking.png)

The holdings breakdown section provides detailed information about each stock in your portfolio:

| Metric | Description |
|--------|-------------|
| Current Value | The current market value of your position |
| Cost Basis | The total amount you paid for the position |
| Gain/Loss | The difference between current value and cost basis |
| Gain/Loss % | The percentage gain or loss on the position |
| Allocation | The percentage of your portfolio the position represents |
| Sector | The market sector of the stock |
| Category | Whether the stock is part of MAG7 or other categories |

## Performance Analysis

The performance analysis section shows how your portfolio has performed over time:

- **Time-weighted Returns**: Performance metrics that eliminate the distorting effects of cash flows
- **Benchmark Comparison**: How your portfolio performs compared to major indices
- **Sector Performance**: How stocks in different sectors are performing in your portfolio

## Diversification Analysis

The diversification analysis helps you understand if your portfolio is properly diversified:

- **Sector Allocation**: Distribution of your investments across market sectors
- **Geographic Exposure**: Distribution across different countries/regions
- **Market Cap Exposure**: Distribution across large, mid, and small-cap stocks
- **MAG7 vs. Other Allocation**: The portion of your portfolio in MAG7 stocks vs. other stocks

## Advanced Metrics

For more sophisticated analysis, TradeLens provides:

- **Volatility Measurement**: Standard deviation of your portfolio returns
- **Sharpe Ratio**: Risk-adjusted return metric
- **Beta Calculation**: Portfolio sensitivity to market movements
- **Correlation Analysis**: How your holdings move in relation to each other

## Using the Analysis Tools

### Filtering Data

You can filter the portfolio data by:

1. Date range (1D, 1W, 1M, 3M, 6M, 1Y, YTD, All)
2. Stock category (MAG7, Other)
3. Sector (Technology, Healthcare, etc.)
4. Transaction type (Buy, Sell)

### Sorting Results

Click on column headers in the tables to sort by different metrics:

- Sort by value to see your largest positions
- Sort by gain/loss to see your best and worst performers
- Sort by allocation to understand portfolio concentration

### Exporting Data

While TradeLens doesn't currently have a built-in export feature, you can:

1. Take screenshots of the charts and tables
2. Access the underlying data directly from the SQLite database
3. Use browser tools to copy table data for use in spreadsheets

## AI-Powered Analysis

You can enhance your portfolio analysis using TradeLens's AI capabilities:

- Ask specific questions about your portfolio composition
- Request analysis of sector-specific performance
- Get suggestions for portfolio rebalancing
- Analyze correlation between holdings

Example query: "How diversified is my portfolio across sectors?"

For more information on the AI features, see the [AI-Powered Features](ai_features.md) guide.

## Next Steps

Once you've analyzed your portfolio, you may want to:

- [Assess potential risks](risk_assessment.md) in your portfolio
- [Test investment strategies](strategy_backtesting.md) against historical data
- [Track upcoming earnings](earnings_analysis.md) for your holdings 