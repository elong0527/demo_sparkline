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
    show_x_axis: bool = False  # Whether to show x-axis with labels
    x_label: str | None = None  # X-axis label text
    show_legend: bool = False  # Whether to show legend
    legend_title: str | None = None  # Title for the legend
    legend_position: float | None = None  # Vertical position of legend (0-1)
    legend_type: str = "point"  # Type of legend: "point", "line", or "point+line"
    margin: list[float] | None = None  # Margin settings [bottom, left, top, right, pad]
    height: int | None = None  # Custom height for sparkline

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

    def generate_javascript(self, colors: list[str] | None = None, type: str = "cell") -> str:
        """Generate JavaScript code for sparkline rendering using the template.

        Args:
            colors: Optional list of colors for each trace
            type: Type of reactable component ("cell", "footer", "header")

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
        
        # Set default margin if not provided
        if self.margin is None:
            # Only show x-axis margin in footer, not in cells
            if type == "cell":
                margin = [5, 10, 5, 10, 0]  # Minimal margins for cells
            elif self.show_x_axis and type != "cell":
                margin = [45, 10, 5, 10, 0]  # Increased bottom margin for x-axis in footer
            else:
                margin = [5, 10, 5, 10, 0]  # Default margins
            
            if self.show_legend and type != "cell":
                margin[2] = 35  # Increased top margin for legend in footer
        else:
            margin = self.margin
        
        # Set default height if not provided
        if self.height is None:
            if type == "footer":
                extra_height = 0
                if self.show_x_axis:
                    extra_height += 45  # Increased for x-axis with more spacing
                if self.show_legend:
                    extra_height += 30  # Increased for legend with more spacing
                if self.footer:
                    extra_height += 20  # Increased for footer text
                height = 30 + extra_height  # Base height + extras
            else:
                height = 45 if len(variables) > 1 else 40
        else:
            height = self.height
        
        # Set legend position if not provided
        if self.legend_position is None:
            if type == "cell":
                legend_position = 1.1
            elif type == "footer":
                # Position legend below x-axis if both are shown
                if self.show_x_axis and self.show_legend:
                    legend_position = -0.5  # More space below the x-axis
                elif self.show_legend:
                    legend_position = 0.5  # Center when legend only
                else:
                    legend_position = 0.5
            else:
                legend_position = 0.5
        else:
            legend_position = self.legend_position
        
        # Prepare colors for each variable
        colors_list = []
        color_errorbar_list = []
        for i in range(len(variables)):
            color = safe_get_color(colors, i)
            colors_list.append(f'"{color}"')
            color_errorbar_list.append(f'"{color}"')
        
        # Prepare JavaScript variables for template
        if type == "cell":
            js_x = ", ".join([f'cell.row["{col}"]' for col in variables])
            if lower_cols:
                js_x_lower = ", ".join([f'cell.row["{col}"]' for col in lower_cols])
            else:
                js_x_lower = ", ".join(["null"] * len(variables))
            if upper_cols:
                js_x_upper = ", ".join([f'cell.row["{col}"]' for col in upper_cols])
            else:
                js_x_upper = ", ".join(["null"] * len(variables))
        else:
            # For footer/header showing legend, use dummy values that won't display
            # but allow the legend to render
            if self.show_legend and not self.show_x_axis:
                # Legend only - use out-of-range values so points don't show
                js_x = ", ".join(["-999999"] * len(variables))
            else:
                # X-axis display or both - use null values
                js_x = ", ".join(["null"] * len(variables))
            js_x_lower = ", ".join(["null"] * len(variables))
            js_x_upper = ", ".join(["null"] * len(variables))
        
        # Y positions for multiple traces
        js_y = ", ".join([str(i * 0.15) for i in range(len(variables))])
        
        # Text for hover
        js_text = ", ".join([f'"{label}"' for label in labels])
        
        # X and Y ranges
        if self.xlim:
            js_x_range = f"{self.xlim[0]}, {self.xlim[1]}"
        else:
            js_x_range = "null, null"
        
        y_range_max = (len(variables) - 1) * 0.15 + 0.2 if len(variables) > 1 else 0.5
        js_y_range = f"-0.2, {y_range_max}"
        
        # Reference line
        js_vline = "null"
        if self.reference_line is not None:
            if isinstance(self.reference_line, str):
                js_vline = f'cell.row["{self.reference_line}"]' if type == "cell" else "null"
            else:
                js_vline = str(self.reference_line)
        
        # Colors
        js_color = ", ".join(colors_list)
        js_color_errorbar = ", ".join(color_errorbar_list)
        js_color_vline = f'"{self.reference_line_color}"' if self.reference_line_color else '"#00000050"'
        
        # Legend variables - only show legend in footer, not in cells
        js_showlegend = "true" if (self.show_legend and type != "cell") else "false"
        js_legend_title = self.legend_title or ""
        js_legend_position = str(legend_position)
        js_legend_label = ", ".join([f'"{label}"' for label in labels])
        
        # Margin
        js_margin = ", ".join(map(str, margin))
        
        # X-axis label - only show in footer
        if self.show_x_axis and type != "cell":
            js_xlab = self.x_label or ""
        else:
            js_xlab = ""
        
        # Footer text for annotation
        js_footer_text = ""
        js_footer_y_position = "-0.4"
        if type == "footer" and self.footer:
            js_footer_text = self.footer
            # Calculate footer position based on what else is shown
            if self.show_x_axis and self.show_legend:
                js_footer_y_position = "-0.5"  # Below both x-axis and legend
            elif self.show_x_axis:
                js_footer_y_position = "-0.4"  # Below x-axis
            elif self.show_legend:
                js_footer_y_position = "-0.3"  # Below legend
            else:
                js_footer_y_position = "-0.2"  # Default position
        
        # Control x-axis visibility
        js_show_xaxis = "true" if (self.show_x_axis and type != "cell") else "false"
        
        # Height and width
        js_height = str(height)
        js_width = str(self.width) if self.width else "300"
        
        # Convert legend type
        legend_type_map = {
            "point": "markers",
            "line": "lines",
            "point+line": "markers+lines"
        }
        js_mode = legend_type_map.get(self.legend_type, "markers")
        
        # Create data traces
        data_traces = []
        for i in range(len(variables)):
            # Build error_x only if bounds are provided
            error_x = ""
            if lower_cols and upper_cols and type == "cell":
                error_x = f""",
          error_x: {{
            type: "data",
            symmetric: false,
            array: [x_upper[{i}] - x[{i}]],
            arrayminus: [x[{i}] - x_lower[{i}]],
            color: color_errorbar[{i}],
            thickness: 1.5,
            width: 3
          }}"""
            
            trace = f"""{{
          x: [x[{i}]],
          y: [y[{i}]],
          text: text[{i}],
          hovertemplate: text[{i}] + ": %{{x}}<extra></extra>",
          mode: "{js_mode}",
          type: "scatter",
          name: legend_label[{i}],
          showlegend: showlegend,
          marker: {{
            size: 8,
            color: color[{i}]
          }},
          line: {{
            color: color[{i}]
          }}{error_x}
        }}"""
            data_traces.append(trace)
        
        data_trace = ",\n      ".join(data_traces)
        
        # Generate JavaScript using template
        return template.safe_substitute(
            js_x=js_x,
            js_y=js_y,
            js_x_lower=js_x_lower,
            js_x_upper=js_x_upper,
            js_x_range=js_x_range,
            js_y_range=js_y_range,
            js_vline=js_vline,
            js_text=js_text,
            js_height=js_height,
            js_width=js_width,
            js_color=js_color,
            js_color_errorbar=js_color_errorbar,
            js_color_vline=js_color_vline,
            js_margin=js_margin,
            js_xlab=js_xlab,
            js_show_xaxis=js_show_xaxis,
            js_showlegend=js_showlegend,
            js_legend_title=js_legend_title,
            js_legend_position=js_legend_position,
            js_legend_label=js_legend_label,
            js_footer_text=js_footer_text,
            js_footer_y_position=js_footer_y_position,
            data_trace=data_trace
        )

    def prepare(self, data: pl.DataFrame) -> None:
        """Prepare panel (currently no-op, xlim is set at ForestPlot level).

        Args:
            data: Input DataFrame
        """
        # X-limits are computed at the ForestPlot level for all panels
        pass
    
    @classmethod
    def compute_shared_xlim(cls, panels: list["SparklinePanel"], data: pl.DataFrame) -> tuple[float, float]:
        """Compute shared x-limits across multiple sparkline panels.
        
        Args:
            panels: List of SparklinePanel instances
            data: DataFrame with panel data
            
        Returns:
            Tuple of (min, max) for shared x-axis limits
        """
        from forestly.utils.common import normalize_to_list
        
        min_vals = []
        max_vals = []
        
        for panel in panels:
            # Skip panels with explicit xlim
            if panel.xlim:
                continue
                
            # Get all numeric columns used in this panel
            numeric_cols = []
            
            # Add main variables
            if panel.variables:
                numeric_cols.extend(normalize_to_list(panel.variables))
            
            # Add lower bounds
            if panel.lower:
                numeric_cols.extend(normalize_to_list(panel.lower))
            
            # Add upper bounds
            if panel.upper:
                numeric_cols.extend(normalize_to_list(panel.upper))
            
            # Calculate min and max across all columns
            for col in numeric_cols:
                if col in data.columns:
                    col_data = data[col].drop_nulls()
                    if len(col_data) > 0:
                        min_vals.append(col_data.min())
                        max_vals.append(col_data.max())
        
        if min_vals and max_vals:
            data_min = min(min_vals)
            data_max = max(max_vals)
            
            # Special handling for when 0 is important (e.g., risk difference)
            # Ensure 0 is included if data spans across it
            if data_min < 0 and data_max > 0:
                # Include 0 with minimal padding
                padding_min = abs(data_min) * 0.05
                padding_max = abs(data_max) * 0.05
                return (data_min - padding_min, data_max + padding_max)
            else:
                # Add 5% padding on each side
                range_val = data_max - data_min
                if range_val > 0:
                    padding = range_val * 0.05
                else:
                    padding = abs(data_min) * 0.05 if data_min != 0 else 1
                
                return (data_min - padding, data_max + padding)
        
        # Default range if no data
        return (-1, 1)


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
    