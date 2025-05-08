# TradeLens API Documentation

TradeLens provides a set of API endpoints that allow you to interact with the application programmatically. This document outlines all available endpoints, their parameters, and response formats.

## Base URL

All API endpoints are relative to the base URL of your TradeLens instance:

```
http://localhost:5000
```

## Authentication

Currently, the API does not require authentication as it's designed for local use. If deploying in a production environment, consider implementing proper authentication mechanisms.

## API Endpoints

### Stock Data

#### GET `/api/stock_chart/<symbol>`

Retrieves historical stock data for charting.

**Parameters:**
- `symbol` (path parameter): Stock symbol (e.g., AAPL)
- `start_date` (query parameter, optional): Start date in YYYY-MM-DD format
- `end_date` (query parameter, optional): End date in YYYY-MM-DD format

**Response:**
```json
{
  "dates": ["2023-01-01", "2023-01-02", ...],
  "prices": [150.23, 152.45, ...],
  "volumes": [28000000, 30000000, ...],
  "transactions": [
    {
      "date": "2023-01-15",
      "price": 155.50,
      "qty": 10,
      "side": "Buy"
    },
    ...
  ]
}
```

### AI Chat

#### POST `/api/chat`

Sends a message to the AI assistant for analysis.

**Request Body:**
```json
{
  "message": "Analyze the risk in my portfolio",
  "current_stock": "AAPL",
  "perplexity_model": "sonar-deep-research"
}
```

**Response:**
```json
{
  "response": "Based on your portfolio...",
  "model_used": "sonar-deep-research"
}
```

### Risk Analysis

#### GET `/api/risk/tariff`

Analyzes tariff risks for stocks in the portfolio.

**Parameters:**
- `symbol` (query parameter, optional): Stock symbol to analyze

**Response:**
```json
{
  "analysis": [
    {
      "symbol": "AAPL",
      "risk_level": "Medium",
      "risk_factors": ["Supply chain exposure to China", ...],
      "recommendations": ["Consider hedging with...", ...]
    },
    ...
  ]
}
```

### Thesis Validation

#### GET `/api/thesis-job/<job_id>`

Retrieves the status and results of a thesis validation job.

**Parameters:**
- `job_id` (path parameter): The ID of the thesis validation job

**Response:**
```json
{
  "job_id": "12345",
  "thesis": "AI stocks will outperform in Q3 2025",
  "status": "completed",
  "result": {
    "analysis": "Based on recent trends...",
    "validation": "Partially supported",
    "supporting_evidence": ["Recent AI chip demand", ...],
    "counter_evidence": ["Regulatory concerns", ...]
  }
}
```

### Earnings Analysis

#### GET `/api/earnings-job/<job_id>`

Retrieves the status and results of an earnings research job.

**Parameters:**
- `job_id` (path parameter): The ID of the earnings research job

**Response:**
```json
{
  "job_id": "67890",
  "symbol": "MSFT",
  "earnings_date": "2023-10-25",
  "status": "completed",
  "result": {
    "analysis": "Microsoft is expected to report...",
    "key_metrics": ["Cloud revenue growth", ...],
    "sentiment": "Positive",
    "risks": ["Competition from AWS", ...]
  }
}
```

#### POST `/api/earnings/calendar/update`

Triggers an update of the earnings calendar.

**Response:**
```json
{
  "status": "success",
  "message": "Earnings calendar update initiated",
  "job_id": "update-12345"
}
```

### Event Calendar

#### POST `/api/events/update`

Triggers an update of the market events calendar.

**Response:**
```json
{
  "status": "success",
  "message": "Market events update initiated",
  "job_id": "events-67890"
}
```

### Company Logos

#### GET `/api/company-logo/<symbol>`

Retrieves the logo for a company.

**Parameters:**
- `symbol` (path parameter): Stock symbol

**Response:**
Binary image data with the appropriate content type.

### API Health

#### GET `/api/check_openai`

Checks the health of the OpenAI/Perplexity API connection.

**Response:**
```json
{
  "status": "healthy",
  "provider": "perplexity",
  "model": "sonar"
}
```

## Error Handling

All API endpoints return standard HTTP status codes:

- 200: Success
- 400: Bad request (missing or invalid parameters)
- 404: Resource not found
- 500: Server error

Error responses include a JSON body with additional information:

```json
{
  "error": "Invalid stock symbol",
  "code": "INVALID_SYMBOL",
  "status": 400
}
```

## Rate Limiting

The API does not currently implement rate limiting, but be mindful of the underlying service limits, especially for API calls to Perplexity or other external services. 