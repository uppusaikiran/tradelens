#!/bin/bash

# Templates to update
TEMPLATES=(
  "strategy_backtesting.html"
  "earnings_job.html"
  "thesis_job.html"
  "thesis_validation.html"
  "earnings_companion.html"
  "event_risk_calendar.html"
  "settings.html"
)

# For each template file
for template in "${TEMPLATES[@]}"; do
  echo "Processing $template..."
  
  # Check if file exists
  if [ ! -f "templates/$template" ]; then
    echo "File templates/$template not found, skipping."
    continue
  fi
  
  # Check if script is already included
  if grep -q "sidebar\.js" "templates/$template"; then
    echo "sidebar.js already included in $template, skipping."
    continue
  fi
  
  # Add the script tag before the closing body tag
  sed -i '' -e '/<\/body>/i\
    <script src="{{ url_for('\''static'\'', filename='\''js/sidebar.js'\'') }}"></script>
' "templates/$template"
  
  echo "Added sidebar.js to $template"
done

echo "Done!"