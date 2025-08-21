#!/bin/bash

# Simple script to render example forest plot documents

echo "Rendering forest plot examples..."
echo ""

# Render each example file
for file in example_*.qmd; do
    if [ -f "$file" ]; then
        echo "[*] Rendering $file..."
        ./render_forest_plot.sh "$file"
        echo ""
    fi
done

echo "Done! HTML files created:"
ls -la *.html 2>/dev/null || echo "No HTML files found"