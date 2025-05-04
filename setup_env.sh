#!/bin/bash

# Check if API key is provided as an argument
if [ -z "$1" ]; then
    echo "Usage: ./setup_env.sh YOUR_OPENAI_API_KEY [YOUR_PERPLEXITY_API_KEY]"
    exit 1
fi

# Set the OpenAI API key environment variable
export OPENAI_API_KEY=$1

# Set Perplexity API key if provided
if [ ! -z "$2" ]; then
    export PERPLEXITY_API_KEY=$2
    echo "Environment set up with your OpenAI and Perplexity API keys"
else
    echo "Environment set up with your OpenAI API key (no Perplexity API key provided)"
fi

# Run the Flask application
echo "You can now run the application with: ./run_server.sh" 