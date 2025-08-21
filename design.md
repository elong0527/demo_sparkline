# Forest Plot System

## Executive Summary
A forest plot system that takes pre-calculated statistics and generates publication-ready visualizations.

Common Use Case 
   - safety assessment.
   - efficacy assessment especially subgroup analysis.

## 1. Core API Design

### 1.1 Primary Class Structure

```python
class ForestPlot:
    """Main class for creating forest plots from clinical trial data"""
    
    def __init__(
        self,
        data: pl.DataFrame,
        panels: list[Panel],
        config: Config | None = None
    ):
        self.data = self._validate_data(data)
        self.panels = panels  # Each panel defines its own column mappings
        self.config = config or Config()
```

### 1.2 Configuration Class

```python
@dataclass
class Config:
    """Configuration for forest plot display and documentation"""
    
    # Display settings
    figure_width: float | None = None
    figure_height: float | None = None
    sparkline_height: int = 30  # Height for all sparkline plots
    
    # Visual styling
    colors: list[str] | None = None  # Color scheme for plots (by position)
    reference_line_color: str = "#00000050"  # Color for reference lines
    
    # Column formatters (optional)
    formatters: dict[str, Callable] | None = None  # {"column_name": format_function}
    
    # Documentation (optional)
    title: str | None = None
    footnote: str | None = None
    source: str | None = None
```

## 2. Panel System

### 2.1 Base Panel Architecture
```python
class Panel:
    """Base class for display panels"""
    
    def __init__(
        self,
        variables: str | list[str] | dict[str, str] | None = None,
        title: str | None = None,
        labels: str | list[str] | None = None,
        width: int | list[int] | None = None,
        footer: str = ""
    ):
        self.variables = variables
        self.title = title
        self.labels = labels
        self.width = width
        self.footer = footer
```

### 2.2 Panel Types

```python
class TextPanel(Panel):
    """Display one or more text/numeric columns"""
    
    def __init__(
        self,
        variables: str | list[str],
        group_by: str | list[str] | None = None
        title: str | None = None,
        labels: str | list[str] | None = None,
        width: int | list[int] | None = None,
        footer: str = "",
    ):
        super().__init__(variables=variables, title=title, labels=labels, width=width, footer=footer)
        self.group_by = group_by

class SparklinePanel(Panel):
    """Display point estimates with error bars"""
    
    def __init__(
        self,
        variables: str | list[str],
        lower: str | list[str] | None = None,
        upper: str | list[str] | None = None,
        title: str | None = None,
        labels: str | list[str] | None = None,
        width: int | None = None,
        footer: str = "",
        reference_line: float | str | None = None,
        reference_line_color: str | None = None,
        xlim: tuple[float, float] | None = None
    ):
        super().__init__(variables=variables, title=title, labels=labels, width=width, footer=footer)
        self.lower = lower
        self.upper = upper
        self.reference_line = reference_line
        self.reference_line_color = reference_line_color
        self.xlim = xlim

```

## 3. Data Input Specifications

### 3.1 Standard Data Structure 

```python
# Expected DataFrame structure for efficacy analysis
efficacy_data = pl.DataFrame({
    # Subgroup identifiers
    "group": ["Overall", "Age <65", "Age >=65", "Male", "Female"],
    "group_category": ["Overall", "Age", "Age", "Sex", "Sex"],
    
    # Treatment effect statistics
    "hazard_ratio": [0.72, 0.68, 0.81, 0.69, 0.75],
    "hr_ci_lower": [0.58, 0.51, 0.62, 0.52, 0.57],
    "hr_ci_upper": [0.89, 0.91, 1.05, 0.92, 0.98],
    "p_value": [0.003, 0.012, 0.089, 0.015, 0.042],
    
    # Events by subgroup
    "treatment_events": [45, 24, 21, 23, 22],
    "control_events": [62, 35, 27, 33, 29],

    "reference_value": [1.0, 1.0, 1.0, 1.0, 1.0]  # Could vary by subgroup
})

# Expected DataFrame structure for safety analysis
safety_data = pl.DataFrame({
    # Adverse event identifiers
    "ae_term": ["Nausea", "Fatigue", "Diarrhea"],
    "soc": ["GI Disorders", "General", "GI Disorders"],
    
    # Multiple treatment groups (wide format)
    "placebo_events": [5, 8, 3],
    "placebo_rate": [5.0, 8.0, 3.0],
    
    "treatment_events": [12, 15, 8],
    "treatment_rate": [11.8, 14.7, 7.8],
    
    # Risk differences vs placebo
    "risk_diff": [6.8, 6.7, 4.8],
    "rd_ci_lower": [0.5, 0.2, 0.1],
    "rd_ci_upper": [13.1, 13.2, 9.5]
})
```

## 4. Usage Examples

### 4.1 Efficacy Subgroup Analysis
```python
# Create efficacy forest plot for oncology trial
efficacy_forest = ForestPlot(
    data=efficacy_data,
    panels=[
        # Subgroup labels with nesting
        TextPanel(
            variables="group",
            group_by="group_category",
            width=180
        ),
        
        # Events  
        TextPanel(
            variables="treatment_events",
            title="Treatment (N=150)",
            width=80
        ),
        
        TextPanel(
            variables="control_events",
            title="Control (N=148)",
            width=80
        ),
        
        # Forest plot
        SparklinePanel(
            variables="hazard_ratio",
            lower="hr_ci_lower",
            upper="hr_ci_upper",
            title="Hazard Ratio (95% CI)",
            reference_line="reference_value",
            xlim=(0.4, 1.2),
            width=250
        ),
        
        # Formatted statistics
        TextPanel(
            variables="hr_formatted",
            title="HR (95% CI)",
            width=120
        ),
        
        # P-values
        TextPanel(
            variables="p_value",
            title="P-value",
            width=80
        )
    ],
    config=Config(
        title="Overall Survival Subgroup Analysis",
        footnote="Stratified Cox proportional hazards model adjusted for Age, ECOG PS, and Prior therapy",
        source="Study STUDY-001, ITT Population, Data cutoff: 2024-01-01",
        colors=["#FF6B35", "#4A90E2"],
        sparkline_height=35,
        formatters={
            "p_value": lambda x: f"{x:.3f}" if x >= 0.001 else "<0.001",
            "hazard_ratio": lambda x: f"{x:.2f}",
            "hr_ci_lower": lambda x: f"{x:.2f}",
            "hr_ci_upper": lambda x: f"{x:.2f}"
        }
    )
)

# Generate outputs
efficacy_forest.to_reactable()  # Interactive review
efficacy_forest.to_rtf("Table_14_2_1_OS_Subgroup.rtf")  # For CSR
efficacy_forest.to_plotnine().save("fig_os_subgroup.png")  # Static figure
```

### 4.2 Safety Forest Plot with Multiple Groups
```python
# Create safety forest plot comparing multiple doses
safety_forest = ForestPlot(
    data=safety_data,
    panels=[
        # AE terms
        TextPanel(
            variables="ae_term",
            title="Adverse Event",
            width=200
        ),
        
        # AE rates for each group
        TextPanel(
            variables="placebo_rate",
            title="Placebo Rate (%)",
            width=80
        ),
        TextPanel(
            variables="treatment_rate",
            title="Treatment Rate (%)",
            width=80
        ),
        
        # Risk difference plot
        SparklinePanel(
            variables="risk_diff",
            lower="rd_ci_lower",
            upper="rd_ci_upper",
            title="Risk Difference (%) vs Placebo",
            reference_line=0,
            xlim=(-5, 15),
            width=250
        ),
        
        # Sample sizes
        TextPanel(
            variables=["placebo_events", "placebo_rate"],
            title="Placebo (N=100)",
            labels=["n", "(%)"],
            width=100
        ),
        TextPanel(
            variables=["treatment_events", "treatment_rate"],
            title="Treatment (N=102)",
            labels=["n", "(%)"],
            width=100
        )
    ],
    config=Config(
        title="Adverse Events by Treatment Group",
        footnote="Risk difference calculated as Treatment % - Placebo %"
    )
)
```

### 4.3 Multiple Groups in Single Sparkline
```python
# Data with multiple treatment arms
multi_arm_data = pl.DataFrame({
    "subgroup": ["Overall", "Age <65", "Age ≥65"],
    
    # Treatment Arm 1
    "hr_trt1": [0.72, 0.68, 0.81],
    "hr_trt1_lower": [0.58, 0.51, 0.62],
    "hr_trt1_upper": [0.89, 0.91, 1.05],
    
    # Treatment Arm 2
    "hr_trt2": [0.65, 0.60, 0.70],
    "hr_trt2_lower": [0.52, 0.45, 0.53],
    "hr_trt2_upper": [0.81, 0.80, 0.92]
})

# Create forest plot with multiple groups
multi_forest = ForestPlot(
    data=multi_arm_data,
    panels=[
        TextPanel(variables="subgroup", title="Subgroup"),
        
        # Single sparkline showing both treatment arms
        SparklinePanel(
            variables=["hr_trt1", "hr_trt2"],
            lower=["hr_trt1_lower", "hr_trt2_lower"],
            upper=["hr_trt1_upper", "hr_trt2_upper"],
            title="Hazard Ratios",
            labels=["Treatment 1", "Treatment 2"],
            reference_line=1.0,
            xlim=(0.4, 1.2)
        )
    ],
    config=Config(
        colors=["#FF6B35", "#4A90E2"]  # Colors for each group by position
    )
)
```

### 4.4 Quick Start with Defaults
```python
# Minimal configuration with single sparkline panel
forest = ForestPlot(
    data=efficacy_data,
    panels=[
        TextPanel(variables="group"),
        SparklinePanel(
            variables="hazard_ratio",
            lower="hr_ci_lower",
            upper="hr_ci_upper",
            title="HR (95% CI)",
            reference_line=1.0
        ),
        TextPanel(variables="p_value", title="P-value")
    ]
)
forest.to_reactable()  # Uses default Config()
```

## 5. Export Methods

```python
class ForestPlot:
    def to_reactable(self) -> Reactable:
        """Generate interactive Reactable table"""
        pass
    
    def to_plotnine(self) -> ggplot:
        """Generate static plot using plotnine"""
        pass
    
    def to_gt(self) -> GT:
        """Generate GT table"""
        pass
    
    def to_rtf(self, filename: str, **kwargs):
        """Export to RTF for regulatory submissions"""
        pass
    
    def to_dataframe(self) -> pl.DataFrame:
        """Export processed DataFrame"""
        pass
```

## 6. Key Design Principles

1. **Pre-calculated Statistics**: Assumes input data contains calculated estimates and CIs
2. **Panel-Based Layout**: Flexible arrangement of text and visual elements
3. **Regulatory Focus**: Built-in support for CSR requirements
5. **Progressive Disclosure**: Simple API with advanced options available

## 7. Implementation Priorities

### Phase 1 (MVP)
- Core `ForestPlot` class
- Basic panels (Text, Sparkline)
- Reactable output
- Single group support

### Phase 2
- Multi-group panels
- RTF export
- Plotnine static plots
- Interaction testing display

### Phase 3
- GT table export
- Custom themes
- Advanced statistical annotations
- Validation suite for regulatory compliance

## 8. Benefits

- **Simplicity**: Biostatisticians can create forest plots with minimal code
- **Flexibility**: Panel system allows custom layouts
- **Compliance**: Built-in regulatory metadata and formatting
- **Reusability**: Same code works for safety and efficacy analyses
- **Integration**: Works with existing ADaM datasets and workflows

## 9. Requirements 

- using Pydantic v2 for strong typing 
- using pytest for unit test 
- using uv for environment management 
- using quarto for documentation 
- using polars for data frame (do not depends on pandas)
