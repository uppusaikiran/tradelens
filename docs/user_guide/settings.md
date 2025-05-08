# Settings and Configuration

TradeLens provides various configuration options to customize your experience. This guide explains all available settings and how to configure them.

## Accessing Settings

To access the settings page:

1. Click on the gear icon (⚙️) in the top navigation bar
2. Navigate to the Settings page

![Settings Page](../../static/img/dashboard_images/Settings%20page%20for%20Provider%20.png)

## AI Provider Settings

TradeLens uses AI capabilities for analysis and insights. You can configure the AI provider settings:

### AI Provider Selection

Choose your preferred AI provider:

- **Perplexity (Recommended)**: Primary AI provider with various models
- **OpenAI (Alternative)**: Secondary option if configured

### Perplexity API Configuration

To set up Perplexity API:

1. Obtain a Perplexity API key from [Perplexity AI](https://www.perplexity.ai)
2. Enter your API key in the field provided
3. Test the connection using the "Test Connection" button
4. Save your settings

### Model Selection

Choose your default Perplexity model:

| Model | Description | Best For |
|-------|-------------|----------|
| sonar | Fast, versatile model for general queries | Quick portfolio insights |
| sonar-pro | Enhanced version with better analysis capabilities | Detailed financial analysis |
| sonar-reasoning | Better reasoning capabilities for complex questions | Strategic investment decisions |
| sonar-reasoning-pro | Enhanced reasoning for advanced financial analysis | In-depth strategy validation |
| sonar-deep-research | Comprehensive research capabilities | Thorough stock analysis |
| r1-1776 | Specialized for US market analysis | US-focused portfolio analysis |
| llama-3.1-sonar-small | Lightweight, efficient model | Basic queries with faster response |

### Usage Settings

Configure how the AI is used:

- **Response Detail Level**: Basic, Standard, or Detailed
- **Include Market Context**: Whether to include current market conditions in AI queries
- **Save Chat History**: Whether to save your conversation history
- **Auto-Suggestions**: Enable or disable AI-generated suggestion prompts

## Data Settings

Configure how TradeLens handles your data:

### Transaction Data

- **Auto-Refresh**: How often to refresh stock price data (15m, 30m, 1h, 4h, Daily)
- **Transaction Import Format**: Set default CSV format settings
- **Data Retention**: How long to keep historical data

### Stock Data Source

- **Primary Data Source**: Yahoo Finance (default)
- **Backup Data Source**: If primary source is unavailable
- **Extended Hours Data**: Include pre-market and after-hours data

### Cache Settings

- **Cache Duration**: How long to cache stock data (1h, 4h, 1d, 1w)
- **Clear Cache**: Button to manually clear cached data
- **Offline Mode**: Enable to use cached data when offline

## Display Settings

Customize how TradeLens displays information:

### Dashboard Layout

- **Default View**: Choose your preferred default dashboard layout
- **Widgets**: Enable/disable specific dashboard widgets
- **Chart Style**: Candlestick, Line, or OHLC

### Chart Settings

- **Default Time Range**: Set the default chart timeframe (1D, 1W, 1M, 3M, 6M, 1Y, YTD, All)
- **Include Volume**: Show volume data on charts
- **Show Indicators**: Select technical indicators to display
- **Transaction Markers**: Show buy/sell points on charts

### Theme Settings

- **Color Theme**: Light, Dark, or System
- **Accent Color**: Choose your preferred accent color
- **Font Size**: Small, Medium, or Large
- **Compact Mode**: Reduce spacing for more information density

## Notification Settings

Control how TradeLens notifies you about important events:

### Earnings Alerts

- **Earnings Announcements**: Get notified before earnings for stocks you own
- **Advance Notice**: How far in advance to be notified (1d, 3d, 1w)
- **Results Notification**: Be notified when earnings results are released

### Economic Events

- **FOMC Meetings**: Notifications for Federal Reserve meetings
- **CPI Reports**: Notifications for inflation data releases
- **Jobs Reports**: Notifications for employment data releases
- **Other Economic Data**: Select which other reports to receive notifications for

### Portfolio Alerts

- **Large Price Movements**: Set threshold for price movement alerts
- **Unusual Volume**: Be notified of unusual trading volume
- **Analyst Changes**: Notifications for rating or price target changes
- **News Alerts**: Important news regarding your holdings

## Advanced Settings

Additional configuration options for advanced users:

### Database Management

- **Database Location**: View or change database file location
- **Backup Settings**: Configure automatic database backups
- **Import/Export**: Import or export your transaction data

### Performance Settings

- **Processing Priority**: Allocate more resources to specific features
- **Background Tasks**: Control how background tasks are processed
- **Memory Usage**: Adjust memory allocation for large portfolios

### Developer Options

- **Debug Mode**: Enable additional logging for troubleshooting
- **API Access**: Configure local API access settings
- **Custom Scripts**: Enable running custom scripts (advanced)

## Account Management

Manage your TradeLens account settings:

### API Keys

- **View Keys**: View your currently configured API keys
- **Reset Keys**: Reset or regenerate API keys
- **Permissions**: Manage what connected services can access

### Privacy Settings

- **Data Sharing**: Control what data is shared with AI services
- **Analytics**: Enable/disable usage analytics
- **Local Storage**: Manage locally stored data

## Saving Changes

After adjusting your settings:

1. Click the "Save Changes" button at the bottom of the page
2. Your new settings will be applied immediately
3. Some changes may require a refresh of the application

## Restoring Defaults

To restore default settings:

1. Click the "Restore Defaults" button at the bottom of the page
2. Confirm that you want to reset all settings
3. Your settings will be reset to the application defaults

## Troubleshooting

If you encounter issues with your settings:

### Settings Not Saving

1. Check that you have proper permissions to modify the configuration file
2. Ensure you're clicking the "Save Changes" button after making changes
3. Verify that your browser allows cookies and local storage

### API Connection Issues

1. Verify your API key is correct
2. Check that the API service is operational
3. Ensure your internet connection is stable
4. Test the connection using the "Test Connection" button

### Display Problems

1. Try switching between themes
2. Clear your browser cache
3. Adjust your zoom level if elements appear misaligned
4. Ensure your browser is up to date

For persistent issues, check the application logs or contact support with details about your problem. 