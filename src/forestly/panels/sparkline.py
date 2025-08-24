"""Sparkline panel module for forest plot system."""

from pathlib import Path
from string import Template

import polars as pl

from forestly.panels.base import Panel
from forestly.utils.common import normalize_to_list, safe_get_color


class SparklinePanel(Panel):
    """Display point estimates with error bars."""

    lower: str | list[str] | None = None
    upper: str | list[str] | None = None
    reference_line: float | str | None = None
    reference_line_color: str | None = None
    xlim: tuple[float, float] | None = None
    js_function: str | None = None  # Custom JavaScript function for rendering

    def render(self, data: pl.DataFrame) -> dict:
        """Render panel data for display.

        Args:
            data: Input DataFrame

        Returns:
            Rendered data dictionary with sparkline configuration
        """
        result = {"data": data, "type": "sparkline"}

        # Handle variables (point estimates)
        if self.variables:
            estimates = normalize_to_list(self.variables)
            result["estimates"] = estimates

        # Handle confidence intervals
        if self.lower:
            result["lower_bounds"] = normalize_to_list(self.lower)

        if self.upper:
            result["upper_bounds"] = normalize_to_list(self.upper)

        # Handle reference line
        if self.reference_line is not None:
            if isinstance(self.reference_line, str):
                # Column name for dynamic reference line
                result["reference_line_column"] = self.reference_line
            else:
                # Fixed value for reference line
                result["reference_line_value"] = self.reference_line

        # Visual configuration
        if self.reference_line_color:
            result["reference_line_color"] = self.reference_line_color

        if self.xlim:
            result["xlim"] = self.xlim

        if self.labels:
            result["labels"] = normalize_to_list(self.labels)

        if self.width:
            result["width"] = self.width

        result["title"] = self.title
        result["footer"] = self.footer

        return result

    def get_required_columns(self) -> set[str]:
        """Get columns required by this panel.

        Returns:
            Set of required column names
        """
        required = set()

        # Add estimate columns
        if self.variables:
            required.update(normalize_to_list(self.variables))

        # Add lower bound columns
        if self.lower:
            required.update(normalize_to_list(self.lower))

        # Add upper bound columns
        if self.upper:
            required.update(normalize_to_list(self.upper))

        # Add reference line column if it's a column name
        if isinstance(self.reference_line, str):
            required.add(self.reference_line)

        return required

    def generate_javascript(self, colors: list[str] | None = None) -> str:
        """Generate JavaScript code for sparkline rendering using the template.

        Args:
            colors: Optional list of colors for each trace

        Returns:
            JavaScript code as string
        """
        import json
        
        # Load the sparkline template
        template_path = Path(__file__).parent / "templates" / "sparkline.js"
        with open(template_path, "r") as f:
            template = Template(f.read())
        
        # Get variables and bounds
        variables = normalize_to_list(self.variables) if self.variables else []
        lower_cols = normalize_to_list(self.lower) if self.lower else []
        upper_cols = normalize_to_list(self.upper) if self.upper else []
        labels = normalize_to_list(self.labels) if self.labels else variables
        
        # Prepare colors for each variable
        colors_list = []
        for i in range(len(variables)):
            colors_list.append(safe_get_color(colors, i))
        
        # Prepare lower and upper arrays (use null for missing values)
        lower_array = []
        upper_array = []
        for i in range(len(variables)):
            lower_array.append(lower_cols[i] if i < len(lower_cols) else None)
            upper_array.append(upper_cols[i] if i < len(upper_cols) else None)
        
        # Build configuration object
        config = {
            'variables': variables,
            'labels': labels,
            'colors': colors_list,
            'lower': lower_array,
            'upper': upper_array,
            'xlim': self.xlim,
            'reference_line': self.reference_line,
            'reference_line_color': self.reference_line_color,
            'height': 45 if len(variables) > 1 else 40,
            'width': self.width
        }
        
        # Generate JavaScript using template
        return template.substitute(
            function_params="cell, state",
            sparkline_config=json.dumps(config)
        )

    def prepare(self, data: pl.DataFrame) -> None:
        """Prepare panel by inferring xlim if not specified.

        Args:
            data: Input DataFrame
        """
        self.infer_xlim(data)

    def infer_xlim(self, data: pl.DataFrame) -> None:
        """Infer xlim based on data if not specified.

        Args:
            data: Input DataFrame
        """
        if self.xlim:
            return  # Already specified
            
        # Get all numeric columns used in this panel
        numeric_cols = []
        
        # Add main variables
        if self.variables:
            numeric_cols.extend(normalize_to_list(self.variables))
        
        # Add lower bounds
        if self.lower:
            numeric_cols.extend(normalize_to_list(self.lower))
        
        # Add upper bounds
        if self.upper:
            numeric_cols.extend(normalize_to_list(self.upper))
        
        # Calculate min and max across all columns
        if numeric_cols:
            min_vals = []
            max_vals = []
            
            for col in numeric_cols:
                if col in data.columns:
                    col_data = data[col].drop_nulls()
                    if len(col_data) > 0:
                        min_vals.append(col_data.min())
                        max_vals.append(col_data.max())
            
            if min_vals and max_vals:
                data_min = min(min_vals)
                data_max = max(max_vals)
                
                # Add 10% padding on each side
                range_val = data_max - data_min
                if range_val > 0:
                    padding = range_val * 0.1
                else:
                    padding = abs(data_min) * 0.1 if data_min != 0 else 1
                
                self.xlim = (data_min - padding, data_max + padding)

    def validate_confidence_intervals(self, data: pl.DataFrame) -> None:
        """Validate that confidence intervals contain point estimates.

        Args:
            data: Input DataFrame

        Raises:
            ValueError: If confidence intervals are invalid
        """
        if not (self.variables and self.lower and self.upper):
            return

        estimates = normalize_to_list(self.variables)
        lowers = normalize_to_list(self.lower)
        uppers = normalize_to_list(self.upper)

        for est, low, up in zip(estimates, lowers, uppers):
            if est in data.columns and low in data.columns and up in data.columns:
                # Check that lower <= estimate <= upper for all rows
                invalid = data.filter(
                    (pl.col(low) > pl.col(est)) | (pl.col(est) > pl.col(up))
                )
                if len(invalid) > 0:
                    raise ValueError(
                        f"Invalid confidence intervals: {low} <= {est} <= {up} "
                        f"violated in {len(invalid)} rows"
                    )
    
    def generate_legend_javascript(self, colors: list[str] | None = None) -> str:
        """Generate JavaScript for legend footer using the legend template.
        
        Args:
            colors: Optional list of colors for legend items
            
        Returns:
            JavaScript code for legend
        """
        import json
        
        labels = normalize_to_list(self.labels) if self.labels else []
        if not labels:
            return ""
        
        # Load the sparkline legend template
        template_path = Path(__file__).parent / "templates" / "sparkline_legend.js"
        with open(template_path, "r") as f:
            template = Template(f.read())
        
        # Prepare colors for each label
        colors_list = []
        for i in range(len(labels)):
            colors_list.append(safe_get_color(colors, i))
        
        # Build legend configuration object
        legend_config = {
            'labels': labels,
            'colors': colors_list,
            'height': 25,
            'width': self.width
        }
        
        # Generate JavaScript using template
        return template.substitute(
            legend_config=json.dumps(legend_config)
        )