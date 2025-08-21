# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Core Purpose

This repository implements interactive sparkline visualizations for Python's reactable-py tables using Plotly.js. The sparklines display data points with error bars and can be embedded in reactable table cells.

## Key Commands

### Rendering Quarto Documents with Sparklines
```bash
# Primary render command - renders QMD and injects required JS libraries
./quarto_render_sparkline.sh <file.qmd>

# Example
./quarto_render_sparkline.sh example_reactable.qmd
```

The `quarto_render_sparkline.sh` script:
1. Renders the Quarto document via `quarto render`
2. Post-processes the HTML to inject React and Plotly libraries before all other scripts
3. This ensures proper loading order for reactable widgets with Plotly sparklines

### Manual Rendering (if needed)
```bash
# Standard Quarto render (without library injection)
quarto render example_reactable.qmd

# Open rendered HTML
open example_reactable.html
```

## Architecture

### Sparkline Generation Pipeline

1. **sparkline_point.py**: Core Python module that generates JavaScript code for Plotly sparklines
   - Takes a Polars DataFrame and column specifications
   - Generates parameterized JavaScript using template substitution
   - Handles error bars, colors, vertical lines, and hover text
   - Returns JS code string to be used in reactable Column definitions

2. **sparkline.js**: JavaScript template for Plotly visualization
   - React component that renders Plotly charts
   - Uses template variables substituted by Python (${js_x}, ${js_y}, etc.)
   - Handles both createPlotlyComponent and fallback React implementation
   - Configures Plotly layout with margins, axes, and styling

3. **Integration with reactable-py**:
   - Use `Column(cell=JS(sparkline_js))` to embed sparklines in table cells
   - The JS code accesses row data via `cell.row["column_name"]`
   - Requires React, React-DOM, and Plotly libraries loaded in HTML

### Critical Dependencies

The reactable widgets with Plotly sparklines require these libraries loaded in order:
1. React 17 (https://unpkg.com/react@17/umd/react.production.min.js)
2. React-DOM 17 (https://unpkg.com/react-dom@17/umd/react-dom.production.min.js)  
3. Plotly 2.18.2 (https://cdn.plot.ly/plotly-2.18.2.min.js)

The `quarto_render_sparkline.sh` script automatically handles this injection.

## Common Development Patterns

### Creating a Sparkline Column
```python
from reactable import Reactable, Column, JS
from sparkline_point import sparkline_point_js
import polars as pl

# Generate sparkline JS
sparkline_js = sparkline_point_js(
    tbl=df,
    x='measurement',
    x_lower='error',  # Lower error bar
    x_upper='error',  # Upper error bar
    xlim=(4, 6),
    height=30,
    width=150,
    color='#FFD700',
    vline=5.0  # Reference line
)

# Add to reactable
Reactable(
    data=df,
    columns=[
        Column(
            id="measurement",
            cell=JS(sparkline_js)
        )
    ]
)
```

## Known Issues

1. **Reactable widgets may not render interactively in Quarto** - The table shows as text representation instead of interactive widget. This is a limitation of reactable-py's widget implementation in Quarto environments.

2. **Library loading order is critical** - React and Plotly must be loaded before reactable attempts to render. Use `quarto_render_sparkline.sh` to ensure proper ordering.

3. **embed_css() is required** - Must call `embed_css()` from reactable to include necessary CSS for table styling.