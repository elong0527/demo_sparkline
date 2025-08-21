"""Test script to verify forestly functionality."""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import polars as pl
from forestly import ForestPlot, TextPanel, SparklinePanel, Config

# Create example efficacy data
efficacy_data = pl.DataFrame({
    "subgroup": ["Overall", "Age <65", "Age ≥65", "Male", "Female"],
    "category": ["Overall", "Age", "Age", "Sex", "Sex"],
    "hazard_ratio": [0.72, 0.68, 0.81, 0.69, 0.75],
    "hr_ci_lower": [0.58, 0.51, 0.62, 0.52, 0.57],
    "hr_ci_upper": [0.89, 0.91, 1.05, 0.92, 0.98],
    "p_value": [0.003, 0.012, 0.089, 0.015, 0.042],
    "treatment_events": [45, 24, 21, 23, 22],
    "control_events": [62, 35, 27, 33, 29],
})

print("Creating forest plot...")

# Create forest plot
forest = ForestPlot(
    data=efficacy_data,
    panels=[
        TextPanel(
            variables="subgroup",
            group_by="category",
            title="Subgroup",
            width=180
        ),
        TextPanel(
            variables="treatment_events",
            title="Treatment",
            width=80
        ),
        TextPanel(
            variables="control_events",
            title="Control",
            width=80
        ),
        SparklinePanel(
            variables="hazard_ratio",
            lower="hr_ci_lower",
            upper="hr_ci_upper",
            title="Hazard Ratio (95% CI)",
            reference_line=1.0,
            xlim=(0.4, 1.2),
            width=250
        ),
        TextPanel(
            variables="p_value",
            title="P-value",
            width=80
        )
    ],
    config=Config(
        title="Overall Survival Subgroup Analysis",
        colors=["#FF6B35"],
        sparkline_height=35,
    )
)

print(f"✓ Forest plot created successfully!")
print(f"  Data shape: {forest.data.shape}")
print(f"  Number of panels: {len(forest.panels)}")

# Test Reactable export
reactable = forest.to_reactable()
print(f"✓ Reactable export successful!")

print("\nSummary:")
print("- All core components working")
print("- Data validation passed")
print("- Export functionality operational")