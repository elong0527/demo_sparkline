#!/bin/bash

# Script to render example forest plot documents with proper environment

echo "Rendering forest plot examples..."
echo ""

# Get the parent directory (project root)
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Check if virtual environment exists
if [ ! -d "$PROJECT_ROOT/.venv" ]; then
    echo "[ERROR] Virtual environment not found at $PROJECT_ROOT/.venv"
    echo "Please run 'uv venv' from the project root first"
    exit 1
fi

# Activate virtual environment and set Python path
source "$PROJECT_ROOT/.venv/bin/activate"
PYTHON_PATH="$(which python)"

echo "[INFO] Using Python: $PYTHON_PATH"
echo ""

# Clear any existing cache directories
echo "[INFO] Clearing cache directories..."
rm -rf _freeze .jupyter_cache
echo "[OK] Cache cleared"
echo ""

# Function to inject libraries into HTML
inject_libraries() {
    local html_file="$1"
    local temp_file="${html_file}.tmp"
    
    awk '
    BEGIN {scripts_inserted = 0}
    {
        if (/<script/ && !scripts_inserted) {
            print "<!-- Essential libraries for forest plot sparklines -->"
            print "<script src=\"https://unpkg.com/react@17/umd/react.production.min.js\"></script>"
            print "<script src=\"https://unpkg.com/react-dom@17/umd/react-dom.production.min.js\"></script>"
            print "<script src=\"https://cdn.plot.ly/plotly-2.18.2.min.js\"></script>"
            print "<!-- End essential libraries -->"
            scripts_inserted = 1
        }
        print $0
    }' "$html_file" > "$temp_file"
    
    mv "$temp_file" "$html_file"
}

# Render each example file
for file in example_*.qmd; do
    if [ -f "$file" ]; then
        echo "[*] Rendering $file..."
        
        # Use Quarto with the virtual environment Python (without cache)
        QUARTO_PYTHON="$PYTHON_PATH" quarto render "$file" --no-cache
        
        if [ $? -eq 0 ]; then
            # Get the output HTML file name
            html_file="_site/${file%.qmd}.html"
            
            # Check if HTML was created
            if [ -f "$html_file" ]; then
                echo "[*] Injecting required libraries into $html_file..."
                inject_libraries "$html_file"
                echo "[OK] Successfully rendered and processed: $file"
            else
                echo "[WARN] HTML file not found: $html_file"
            fi
        else
            echo "[ERROR] Failed to render: $file"
        fi
        echo ""
    fi
done

echo "Done! HTML files created:"
ls -la _site/*.html 2>/dev/null || echo "No HTML files found"