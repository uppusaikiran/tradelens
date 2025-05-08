# AI Integration in TradeLens

TradeLens integrates artificial intelligence capabilities through the Perplexity API to provide users with intelligent analysis and insights about their stock portfolios. This document explains how AI is integrated into the application and how developers can extend these capabilities.

## AI Provider Integration

TradeLens is designed to work with multiple AI providers, but the primary integration is with Perplexity. The application includes fallback support for OpenAI.

### Configuration

AI provider configuration is managed through environment variables and user settings:

```python
# Initialize Perplexity client
perplexity_client = None
if os.getenv('PERPLEXITY_API_KEY'):
    perplexity_client = OpenAI(
        api_key=os.getenv('PERPLEXITY_API_KEY'),
        base_url="https://api.perplexity.ai"
    )
```

Users can select their preferred AI provider and model through the settings page.

## AI Models

TradeLens supports multiple Perplexity models, each with different capabilities:

| Model | Description | Best Used For |
|-------|-------------|--------------|
| sonar | Fast, general-purpose | Quick portfolio analysis |
| sonar-pro | Enhanced version of sonar | More detailed analysis |
| sonar-reasoning | Better reasoning capabilities | Complex financial decisions |
| sonar-reasoning-pro | Enhanced reasoning | Advanced strategy validation |
| sonar-deep-research | Comprehensive research | In-depth stock analysis |
| r1-1776 | Specialized model | US market analysis |
| llama-3.1-sonar-small | Smaller, faster model | Basic queries |

## AI Features

### 1. Conversational Interface

The chat interface allows users to ask questions about their portfolio in natural language.

**Implementation:**
```python
@app.route('/api/chat', methods=['POST'])
def chat():
    # Extract parameters from request
    data = request.json
    message = data.get('message', '')
    current_stock = data.get('current_stock', None)
    perplexity_model = data.get('perplexity_model', None)
    
    # Process message using AI
    response = process_api_request_with_timeout(message, current_stock, perplexity_model)
    
    return jsonify(response)
```

### 2. Thesis Validation

Users can submit investment theses for AI validation, which analyzes the thesis and provides supporting or contradicting evidence.

**Implementation:**
```python
def process_thesis_validation(job_id, thesis):
    # This function runs in a background thread
    try:
        # Update job status
        update_thesis_job(job_id, 'processing')
        
        # Construct prompt for AI
        prompt = f"""You are a financial expert analyzing the following investment thesis: '{thesis}'
        Please provide a detailed analysis...
        """
        
        # Get response from Perplexity API
        # Process and format the response
        # Update the job with the result
    except Exception as e:
        logger.error(f"Error processing thesis validation: {e}")
        update_thesis_job(job_id, 'failed')
```

### 3. Earnings Research

AI-powered analysis of upcoming earnings announcements, providing insights on what to watch for.

**Implementation:**
```python
def process_earnings_research(job_id, symbol, earnings_date, perplexity_model):
    try:
        # Update job status
        update_earnings_job(job_id, 'processing')
        
        # Construct prompt for AI
        prompt = f"""As a financial analyst, provide a detailed earnings preview for {symbol} 
        with its upcoming earnings release on {earnings_date}...
        """
        
        # Get response from Perplexity API
        # Process and format the response
        # Update the job with the result
    except Exception as e:
        logger.error(f"Error processing earnings research: {e}")
        update_earnings_job(job_id, 'failed')
```

### 4. Risk Assessment

AI analysis of portfolio risks, including tariff impacts, geopolitical factors, and market conditions.

**Implementation:**
```python
def analyze_tariff_risk(current_stock=None):
    # Get unique stocks from transactions if no specific stock provided
    
    # Construct prompt for AI
    prompt = f"""As a trade policy expert, analyze the tariff and supply chain risks 
    for the following stocks: {symbols_list}...
    """
    
    # Get response from Perplexity API
    # Process and structure the response
    # Return formatted risk analysis
```

### 5. Strategy Backtesting

AI-powered validation of investment strategies against historical market conditions.

## Prompt Engineering

TradeLens uses carefully crafted prompts to get the most useful responses from the AI. Effective prompt engineering is critical for the quality of AI features.

### Prompt Structure

Most prompts follow this general structure:

1. **Role definition**: Define the AI's role (financial analyst, trade expert, etc.)
2. **Context**: Provide relevant portfolio information
3. **Task description**: Clearly define what analysis is needed
4. **Output format**: Specify the desired response format
5. **Additional constraints**: Any specific requirements or limitations

### Example Prompt

```
You are a financial analyst specializing in earnings reports. 
I need you to analyze the upcoming earnings for {symbol} on {date}.

Context:
- Current stock price: ${price}
- 52-week range: ${low} - ${high}
- Average analyst EPS estimate: ${eps_estimate}
- Previous quarter EPS: ${prev_eps}

Please provide:
1. Key metrics to watch
2. Potential catalysts
3. Risk factors
4. Your earnings prediction
5. Post-earnings price movement prediction

Format your response in markdown with clear sections.
```

## Error Handling

AI integration includes robust error handling to manage API timeouts, rate limits, and other issues:

```python
def process_api_request_with_timeout():
    try:
        with ThreadPoolExecutor() as executor:
            future = executor.submit(ai_function, *args)
            try:
                return future.result(timeout=30)  # 30-second timeout
            except TimeoutError:
                return {"error": "Request timed out"}
    except Exception as e:
        logger.error(f"API request error: {str(e)}")
        return {"error": f"Error processing request: {str(e)}"}
```

## Extending AI Capabilities

### Adding New AI Features

To add a new AI feature:

1. Create a function to construct the appropriate prompt
2. Implement the API call with proper error handling
3. Add a background processing job if it's a long-running task
4. Create database tables to store results if needed
5. Add API endpoints and UI elements for the feature

### Switching AI Providers

The application is designed to work with different AI providers. To add a new provider:

1. Add appropriate client initialization in app.py
2. Extend the settings page to include the new provider
3. Update the API call functions to support the new provider's format

### Performance Considerations

- Use caching for AI responses to minimize API calls
- Implement request throttling to avoid rate limits
- Use streaming responses for long outputs
- Consider implementing result caching based on input parameters

## Testing AI Integration

When testing AI features:

1. Create mock responses for unit tests
2. Test with real API for integration tests
3. Verify error handling by simulating API failures
4. Test timeout handling with deliberately slow responses

## Security Considerations

- Never expose API keys in client-side code
- Validate and sanitize all user input before sending to AI
- Consider content filtering for AI responses
- Implement rate limiting to prevent abuse

## Resources

- [Perplexity API Documentation](https://docs.perplexity.ai/)
- [OpenAI API Documentation](https://platform.openai.com/docs/api-reference) 