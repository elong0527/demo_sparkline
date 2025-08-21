# Forestly

A production-ready forest plot system for clinical trials with interactive Reactable tables, supporting nested listings and drill-down capabilities.

## Installation

```bash
pip install -e .
```

## Quick Start

```python
from forestly import ForestPlot, TextPanel, SparklinePanel, Config
import polars as pl

# Create forest plot
forest = ForestPlot(
    data=efficacy_data,
    panels=[
        TextPanel(variables="subgroup"),
        SparklinePanel(
            variables="hazard_ratio",
            lower="hr_ci_lower",
            upper="hr_ci_upper",
            reference_line=1.0
        ),
        TextPanel(variables="p_value", title="P-value")
    ]
)

# Export to interactive Reactable
forest.to_reactable()
```

## Features

- Panel-based architecture for flexible layouts
- Interactive Reactable tables with drill-down capabilities
- Multiple export formats (RTF, static plots)
- Pydantic validation for data integrity
- Support for hierarchical data structures

## Development

```bash
# Install development dependencies
uv add --dev pytest pytest-cov ruff mypy hypothesis

# Run tests
pytest

# Format code
ruff format .

# Type check
mypy src/
```