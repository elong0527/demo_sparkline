# Forest Plot Implementation Plan

## Overview
A phased implementation plan for building a production-ready forest plot system for clinical trials with Reactable integration, supporting nested listings and drill-down capabilities.

## Phase 1: Foundation (Week 1-2)

### 1.1 Project Setup
**Goal**: Establish project structure and development environment

- [ ] Initialize project with uv
  ```bash
  uv init forest-plot
  cd forest-plot
  uv add pydantic polars reactable plotly jinja2
  uv add --dev pytest pytest-cov ruff mypy hypothesis
  ```

- [ ] Create project structure
  ```
  forest-plot/
  ├── src/forest_plot/
  │   ├── __init__.py
  │   ├── core/
  │   ├── panels/
  │   ├── exporters/
  │   └── templates/
  ├── tests/
  ├── docs/
  └── pyproject.toml
  ```

- [ ] Configure development tools
  - Setup ruff for linting/formatting
  - Configure mypy for type checking
  - Setup pre-commit hooks
  - Configure pytest

### 1.2 Core Data Models
**Goal**: Implement base classes with Pydantic validation

**Files to create**:
- `src/forest_plot/core/config.py`
  ```python
  from pydantic import BaseModel, Field
  
  class Config(BaseModel):
      figure_width: float | None = None
      figure_height: float | None = None
      sparkline_height: int = 30
      colors: list[str] | None = None
      reference_line_color: str = "#00000050"
      formatters: dict[str, Callable] | None = None
      title: str | None = None
      footnote: str | None = None
      source: str | None = None
  ```

- `src/forest_plot/panels/base.py`
  ```python
  class Panel(BaseModel):
      variables: str | list[str] | None = None
      title: str | None = None
      labels: str | list[str] | None = None
      width: int | list[int] | None = None
      footer: str = ""
  ```

**Tests**:
- `tests/unit/test_config.py`
- `tests/unit/test_panel_base.py`

**Deliverables**:
- ✅ Pydantic models for Config and Panel base
- ✅ Validation rules implemented
- ✅ Unit tests with >95% coverage

## Phase 2: Panel Implementation (Week 2-3)

### 2.1 TextPanel Implementation
**Goal**: Implement TextPanel with grouping and nesting support

**Files**:
- `src/forest_plot/panels/text.py`
  ```python
  class TextPanel(Panel):
      group_by: str | list[str] | None = None
      
      def render(self, data: pl.DataFrame) -> dict:
          """Render panel data for Reactable"""
          pass
      
      def get_required_columns(self) -> set[str]:
          """Get columns required by this panel"""
          pass
  ```

**Features**:
- Single and multiple column support
- Hierarchical grouping with `group_by`
- Column formatting with labels
- Width configuration per column

**Tests**:
- Group by single column
- Group by multiple columns (nested)
- Missing column validation
- Format application

### 2.2 SparklinePanel Implementation
**Goal**: Implement SparklinePanel with error bars and reference lines

**Files**:
- `src/forest_plot/panels/sparkline.py`
- `src/forest_plot/templates/sparkline.js`

**Features**:
- Single and multiple group support
- Error bars (lower/upper)
- Reference line (fixed or column-based)
- Custom colors and dimensions
- JavaScript template generation

**Integration**:
- Plotly.js integration
- React component wrapper
- Dynamic data binding

**Tests**:
- Single estimate rendering
- Multiple groups with labels
- Reference line variations
- Color customization

## Phase 3: Core ForestPlot Class (Week 3-4)

### 3.1 ForestPlot Implementation
**Goal**: Main orchestrator class with validation

**Files**:
- `src/forest_plot/core/forest_plot.py`
  ```python
  class ForestPlot(BaseModel):
      model_config = ConfigDict(arbitrary_types_allowed=True)
      
      data: pl.DataFrame
      panels: list[Panel]
      config: Config = Field(default_factory=Config)
      
      @validator('data')
      def validate_columns(cls, v, values):
          """Validate all panel columns exist"""
          pass
      
      def _prepare_reactable_data(self) -> dict:
          """Prepare data for Reactable with nesting"""
          pass
  ```

### 3.2 Data Validation Layer
**Goal**: Statistical and structural validation

**Features**:
- Column existence validation
- Statistical consistency checks (CI contains estimate)
- P-value and CI alignment
- Missing data handling
- Group hierarchy validation

**Files**:
- `src/forest_plot/core/validators.py`
  ```python
  def validate_confidence_intervals(data: pl.DataFrame):
      """Validate CI consistency"""
      pass
  
  def validate_grouping_structure(data: pl.DataFrame, group_cols: list[str]):
      """Validate hierarchical grouping"""
      pass
  ```

## Phase 4: Reactable Integration (Week 4-5)

### 4.1 Basic Reactable Export
**Goal**: Generate interactive Reactable tables

**Files**:
- `src/forest_plot/exporters/reactable.py`
  ```python
  class ReactableExporter:
      def export(self, forest_plot: ForestPlot) -> Reactable:
          """Export to Reactable with panels"""
          pass
      
      def _create_columns(self, panels: list[Panel]) -> list[Column]:
          """Create Reactable columns from panels"""
          pass
      
      def _apply_nesting(self, data: pl.DataFrame, group_by: list[str]) -> dict:
          """Apply hierarchical nesting for drill-down"""
          pass
  ```

### 4.2 Nested Listings & Drill-Down
**Goal**: Enable hierarchical data exploration

**Features**:
- Expandable/collapsible groups
- Multi-level nesting (e.g., SOC → PT → Patient)
- Row details with patient-level data
- Custom row expanders
- State management for expanded rows

**Implementation**:
```python
def create_nested_reactable(data: pl.DataFrame, hierarchy: list[str]) -> Reactable:
    """Create Reactable with nested structure"""
    return Reactable(
        data,
        groupBy=hierarchy[0] if hierarchy else None,
        columns=[
            Column(
                id=col,
                aggregated=lambda x: f"n={len(x)}" if col in hierarchy else None,
                details=create_details_renderer(col)
            )
        ],
        details=lambda row_info: create_drill_down_view(row_info)
    )
```

### 4.3 Sparkline Integration
**Goal**: Embed interactive sparklines in Reactable cells

**Features**:
- JavaScript function generation
- React component integration
- Dynamic data binding
- Hover interactions
- Click-through to detailed view

## Phase 5: Export Formats (Week 5-6)

### 5.1 RTF Export
**Goal**: Regulatory-compliant RTF output

**Files**:
- `src/forest_plot/exporters/rtf.py`
- `src/forest_plot/templates/rtf_template.jinja2`

**Features**:
- Table formatting with borders
- Footnotes and titles
- Page headers/footers
- Landscape orientation support
- Statistical annotations

### 5.2 Static Plot Export
**Goal**: Publication-ready static plots

**Files**:
- `src/forest_plot/exporters/plotnine.py`
- `src/forest_plot/exporters/matplotlib.py`

**Features**:
- High-resolution output
- Journal-specific themes
- Annotation support
- Multi-panel layouts

### 5.3 DataFrame Export
**Goal**: Processed data export for further analysis

**Features**:
- Flattened structure option
- Hierarchical structure preservation
- Metadata inclusion
- Format options (CSV, Parquet, SAS)

## Phase 6: Testing & Documentation (Week 6-7)

### 6.1 Comprehensive Testing
**Goal**: Achieve >90% test coverage

**Test Categories**:
- Unit tests for all components
- Integration tests for workflows
- Property-based testing with Hypothesis
- Performance benchmarks
- Regression test suite

**Special Focus Areas**:
- Nested data structures
- Edge cases (empty groups, single row)
- Large hierarchies (3+ levels)
- Missing data handling

### 6.2 Documentation
**Goal**: Complete user and developer documentation

**Deliverables**:
- API reference (autodoc)
- User guide with examples
- Clinical trial use cases
- Quarto-based tutorials
- Migration guide from other tools

### 6.3 Example Gallery
**Goal**: Comprehensive examples for common use cases

**Examples**:
- Efficacy subgroup analysis
- Safety forest plot with SOC/PT hierarchy
- Multi-arm trial comparison
- Biomarker analysis with cutpoints
- Time-to-event forest plots
- Nested drill-down demonstrations

## Phase 7: Advanced Features (Week 7-8)

### 7.1 Template System
**Goal**: Pre-built templates for common analyses

**Templates**:
```python
def create_efficacy_subgroup_plot(
    data: pl.DataFrame,
    subgroup_col: str = "SUBGROUP",
    estimate_col: str = "AVAL",
    lower_col: str = "AVAL_CI_LO",
    upper_col: str = "AVAL_CI_HI"
) -> ForestPlot:
    """Template for standard efficacy subgroup analysis"""
    pass

def create_safety_forest_plot(
    data: pl.DataFrame,
    hierarchy: list[str] = ["AESOC", "AEDECOD"],
    treatment_groups: list[str] = None
) -> ForestPlot:
    """Template for hierarchical safety analysis"""
    pass
```

### 7.2 Statistical Enhancements
**Goal**: Built-in statistical utilities

**Features**:
- Interaction test integration
- Heterogeneity statistics
- Multiplicity adjustments
- Meta-analysis capabilities

### 7.3 Interactive Features
**Goal**: Enhanced interactivity for data exploration

**Features**:
- Filter panels dynamically
- Sort by effect size or p-value
- Highlight significant results
- Export selected subgroups
- Linked brushing across panels

## Phase 8: Production Readiness (Week 8)

### 8.1 Performance Optimization
**Goal**: Optimize for typical dataset sizes

**Optimizations**:
- Lazy evaluation with Polars
- Caching computed results
- Efficient nesting algorithms
- JavaScript bundle optimization

### 8.2 Error Handling & Logging
**Goal**: Robust error handling and debugging

**Features**:
- Comprehensive error messages
- Validation error reports
- Debug mode with detailed logging
- Performance profiling

### 8.3 CI/CD Setup
**Goal**: Automated testing and deployment

**Setup**:
- GitHub Actions workflow
- Automated testing on PR
- Coverage reporting
- Documentation building
- Package publishing to PyPI

## Milestones & Deliverables

### MVP (End of Phase 3)
- ✅ Core ForestPlot class
- ✅ TextPanel and SparklinePanel
- ✅ Basic validation
- ✅ Data preparation

### Beta Release (End of Phase 5)
- ✅ Reactable export with nesting
- ✅ RTF export
- ✅ Static plots
- ✅ Documentation

### v1.0 Release (End of Phase 8)
- ✅ All features implemented
- ✅ >90% test coverage
- ✅ Complete documentation
- ✅ Performance optimized
- ✅ Production ready

## Risk Mitigation

### Technical Risks
1. **Reactable nesting complexity**
   - Mitigation: Early prototype in Phase 1
   - Fallback: Simplified grouping without drill-down

2. **JavaScript integration issues**
   - Mitigation: Test early with minimal example
   - Fallback: Server-side rendering option

3. **Performance with nested structures**
   - Mitigation: Profile with realistic data early
   - Fallback: Pagination or virtualization

### Schedule Risks
1. **Scope creep**
   - Mitigation: Strict phase boundaries
   - Regular stakeholder reviews

2. **Testing complexity**
   - Mitigation: Test-driven development
   - Continuous integration from Phase 1

## Success Criteria

### Technical
- [ ] All panels render correctly in Reactable
- [ ] Nested drill-down works to 3+ levels
- [ ] Export formats validated against requirements
- [ ] Performance <1s for typical datasets (1000 rows)
- [ ] Test coverage >90%

### User Experience
- [ ] Biostatisticians can create plots in <10 lines of code
- [ ] Clear error messages for data issues
- [ ] Intuitive API matching domain concepts
- [ ] Interactive exploration capabilities
- [ ] Regulatory-compliant outputs

## Dependencies & Prerequisites

### Required Knowledge
- Python 3.10+ features
- Pydantic v2 validation
- Polars DataFrame operations
- React/JavaScript basics (for sparklines)
- Reactable-py API

### External Dependencies
- Reactable-py >=0.4.0
- Polars >=0.20.0
- Pydantic >=2.5.0
- Plotly.js (CDN or bundled)

## Notes

### Priority Adjustments
- Nested listings are HIGH priority (Phase 4)
- Large dataset handling is DEPRIORITIZED
- Focus on usability over performance initially

### Key Design Decisions
- Pydantic for all validation
- Polars-only (no pandas dependency)
- Plugin architecture for exporters
- Template-based JavaScript generation

This plan provides a clear 8-week roadmap from foundation to production-ready system with emphasis on nested data exploration capabilities.