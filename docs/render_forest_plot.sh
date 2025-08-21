#!/bin/bash

# Script to render Quarto document with forest plots and inject required JS libraries

# Check if a .qmd file is provided as argument
if [ $# -eq 0 ]; then
    echo "Usage: $0 <file.qmd>"
    echo "Example: $0 example_basic_forest.qmd"
    exit 1
fi

QMD_FILE="$1"
HTML_FILE="${QMD_FILE%.qmd}.html"

# Check if the QMD file exists
if [ ! -f "$QMD_FILE" ]; then
    echo "Error: File '$QMD_FILE' not found"
    exit 1
fi

# Render the Quarto document
echo "Rendering $QMD_FILE..."
quarto render "$QMD_FILE"

# Check if render was successful
if [ $? -ne 0 ]; then
    echo "Error: Quarto render failed"
    exit 1
fi

# Post-process the HTML file to add React and Plotly scripts before the first script tag
echo "Post-processing $HTML_FILE to inject required libraries..."
TEMP_FILE=$(mktemp)

awk '
BEGIN {
    scripts_inserted = 0
}
{
    # When we find the first <script> tag, insert our scripts before it
    if (/<script/ && !scripts_inserted) {
        print "<!-- Essential libraries for forest plot sparklines -->"
        print "<script src=\"https://unpkg.com/react@17/umd/react.production.min.js\"></script>"
        print "<script src=\"https://unpkg.com/react-dom@17/umd/react-dom.production.min.js\"></script>"
        print "<script src=\"https://cdn.plot.ly/plotly-2.18.2.min.js\"></script>"
        print "<!-- End essential libraries -->"
        scripts_inserted = 1
    }
    print $0
}
' "$HTML_FILE" > "$TEMP_FILE"

# Replace the original file with the processed one
mv "$TEMP_FILE" "$HTML_FILE"

echo "✓ Complete! $HTML_FILE has been rendered with forest plot libraries."
echo "Open with: open $HTML_FILE"