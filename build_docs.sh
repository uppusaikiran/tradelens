#!/bin/bash

# Check if MkDocs is installed
if ! command -v mkdocs &> /dev/null; then
    echo "MkDocs is not installed. Installing now..."
    pip install mkdocs mkdocs-material mkdocstrings-python pymdown-extensions
fi

# Build the documentation
echo "Building TradeLens documentation..."
mkdocs build

# Check if build was successful
if [ $? -eq 0 ]; then
    echo "Documentation built successfully! The site is available in the 'site' directory."
    echo "To view the documentation locally, run: mkdocs serve"
else
    echo "Error building documentation. Please check the error messages above."
fi 