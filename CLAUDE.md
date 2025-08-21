# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Core Purpose

This repository is developing a production-ready forest plot system for clinical trials with interactive Reactable tables, supporting nested listings and drill-down capabilities. The system uses a panel-based architecture for flexible layouts and supports multiple export formats for regulatory submissions.

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

### Forest Plot System Design

1. **Panel-Based Architecture**:
   - **TextPanel**: Display text/numeric columns with hierarchical grouping support
   - **SparklinePanel**: Display point estimates with confidence intervals
   - Panels define their own column mappings and rendering logic

2. **Core Components**:
   - **ForestPlot**: Main orchestrator class with Pydantic validation
   - **Config**: Centralized configuration for styling, formatting, and metadata
   - **Exporters**: Plugin-based system for multiple output formats (Reactable, RTF, static plots)

3. **Data Structure**:
   - Uses Polars DataFrames (no pandas dependency)
   - Follows `{group}_{variable}` naming convention (e.g., `treatment_events`)
   - Supports hierarchical grouping for nested displays

4. **Validation Layer**:
   - Pydantic v2 for all data models
   - Statistical consistency checks (CI contains estimate)
   - Column existence validation
   - Hierarchical structure validation

### Critical Dependencies

The reactable widgets with Plotly sparklines require these libraries loaded in order:
1. React 17 (https://unpkg.com/react@17/umd/react.production.min.js)
2. React-DOM 17 (https://unpkg.com/react-dom@17/umd/react-dom.production.min.js)  
3. Plotly 2.18.2 (https://cdn.plot.ly/plotly-2.18.2.min.js)

The `quarto_render_sparkline.sh` script automatically handles this injection.

## Development Guidelines

### Key Design Documents
- **design.md**: Complete system design and API specification
- **plan.md**: Detailed 8-phase implementation plan with milestones

### Implementation Priorities
1. **Phase 1-2**: Foundation with Pydantic models and base panels
2. **Phase 3-4**: Core ForestPlot class and Reactable integration with nested listings
3. **Phase 5**: Export formats (RTF, static plots)
4. **Phase 6-8**: Testing, documentation, and production readiness

### Code Standards
- Type hints required (Python 3.10+ union syntax with `|`)
- Pydantic v2 for all data models
- No inline comments in production code
- Consistent parameter ordering: `variables` first in panels
- >90% test coverage target

## Common Development Patterns

### Creating a Forest Plot with Nested Grouping
```python
from forest_plot import ForestPlot, TextPanel, SparklinePanel, Config
import polars as pl

# Create forest plot with hierarchical grouping
forest = ForestPlot(
    data=efficacy_data,
    panels=[
        TextPanel(
            variables="subgroup",
            group_by=["study", "category"],  # Multi-level nesting
            width=200
        ),
        SparklinePanel(
            variables="hazard_ratio",
            lower="hr_ci_lower",
            upper="hr_ci_upper",
            reference_line=1.0,
            xlim=(0.5, 2.0)
        ),
        TextPanel(
            variables="p_value",
            title="P-value"
        )
    ],
    config=Config(
        title="Efficacy Subgroup Analysis",
        colors=["#FF6B35", "#4A90E2"]
    )
)

# Export to interactive Reactable with drill-down
reactable = forest.to_reactable()

# Export to RTF for regulatory submission
forest.to_rtf("forest_plot.rtf")
```

### Nested Listings for Drill-Down
```python
# Enable hierarchical data exploration
TextPanel(
    variables="ae_term",
    group_by=["soc", "pt"],  # SOC → Preferred Term hierarchy
    width=300
)

# Reactable will automatically create expandable/collapsible groups
# Users can drill down from System Organ Class to individual AEs
```

## Testing Strategy

### Unit Testing
```bash
# Run all tests
uv run pytest tests/

# Run with coverage
uv run pytest --cov=forest_plot --cov-report=html

# Run specific test file
uv run pytest tests/unit/test_panels.py -v
```

### Key Test Areas
- **Nested data structures**: Test 3+ level hierarchies
- **Edge cases**: Empty groups, single rows, missing data
- **Validation**: Statistical consistency, column existence
- **Performance**: Benchmark with 1000-5000 row datasets

## Known Issues & Solutions

1. **Reactable widgets may not render interactively in Quarto** 
   - Solution: Use `quarto_render_sparkline.sh` for proper library injection

2. **Library loading order is critical** 
   - Solution: React and Plotly must load before reactable

3. **Nested grouping complexity**
   - Solution: Start with 2-level hierarchy, expand gradually
   - Test with realistic clinical trial data early

## Performance Targets

- **Typical dataset (1000 rows)**: <1 second
- **Nested hierarchy (3 levels)**: <2 seconds  
- **RTF export**: <5 seconds
- **Memory usage**: <500MB for 5000 rows

## Next Steps for Development

1. **Set up environment**: 
   ```bash
   uv init forest-plot
   cd forest-plot
   uv add pydantic polars reactable plotly
   ```

2. **Review key documents**:
   - Read `design.md` for API specification
   - Follow `plan.md` for implementation phases

3. **Start Phase 1**:
   - Create project structure
   - Implement Pydantic models
   - Set up testing framework

4. **Focus on nested listings** (Phase 4):
   - Critical feature for clinical trial reporting
   - Test drill-down capabilities early
   - Validate with hierarchical safety data

5. **Validate with real data**:
   - Use ADaM-compliant datasets
   - Test with actual clinical trial outputs
   - Ensure regulatory compliance