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

    def generate_javascript(self, colors: list[str] | None = None, type: str = "cell", font_size: int = 12) -> str:
        """Generate JavaScript code for sparkline rendering using the template.

        Args:
            colors: Optional list of colors for each trace
            type: Type of reactable component ("cell", "footer", "header")
            font_size: Font size for text and legends

        Returns:
            JavaScript code as string
        """
        template_path = Path(__file__).parent / "templates" / "sparkline.js"
        with open(template_path, "r") as f:
            template = Template(f.read())
        
        variables = normalize_to_list(self.variables) if self.variables else []
        lower_cols = normalize_to_list(self.lower) if self.lower else []
        upper_cols = normalize_to_list(self.upper) if self.upper else []
        labels = normalize_to_list(self.labels) if self.labels else variables
        
        margin = self._get_margin(type)
        height = self._get_height(type, len(variables))
        legend_position = self._get_legend_position(type)
        
        colors_list = [f'"{safe_get_color(colors, i)}"' for i in range(len(variables))]
        color_errorbar_list = colors_list.copy()
        
        js_x, js_x_lower, js_x_upper = self._prepare_x_values(type, variables, lower_cols, upper_cols)
        
        # Calculate y-spacing using the general function
        y_positions = self._calculate_y_spacing(len(variables))
        js_y = ", ".join([str(y) for y in y_positions])
        js_y_range = "0, 1.0"  # Always use consistent range
        
        js_text = ", ".join([f'"{label}"' for label in labels])
        
        js_x_range = f"{self.xlim[0]}, {self.xlim[1]}" if self.xlim else "null, null"
        
        js_vline = self._prepare_reference_line(type)
        
        js_color = ", ".join(colors_list)
        js_color_errorbar = ", ".join(color_errorbar_list)
        js_color_vline = f'"{self.reference_line_color}"' if self.reference_line_color else '"#00000050"'
        
        js_showlegend = "true" if (self.show_legend and type != "cell") else "false"
        js_legend_title = self.legend_title or ""
        js_legend_position = str(legend_position)
        js_legend_label = ", ".join([f'"{label}"' for label in labels])
        
        js_margin = ", ".join(map(str, margin))
        js_xlab = self.x_label or "" if self.show_x_axis and type != "cell" else ""
        
        js_footer_text = self.footer if type == "footer" and self.footer else ""
        js_footer_y_position = "-0.5"  # Fixed position for all footer text
        
        js_show_xaxis = "true" if (self.show_x_axis and type != "cell") else "false"
        js_height = str(height)
        js_width = str(self.width) if self.width else "300"
        
        legend_type_map = {
            "point": "markers",
            "line": "lines",
            "point+line": "markers+lines"
        }
        js_mode = legend_type_map.get(self.legend_type, "markers")
        js_type = type  # Pass the type to JavaScript for conditional logic
        
        # Font size for legend and labels
        js_font_size = str(font_size)
        
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
            js_font_size=js_font_size,
            js_legend_position=js_legend_position,
            js_legend_label=js_legend_label,
            js_footer_text=js_footer_text,
            js_footer_y_position=js_footer_y_position,
            js_mode=js_mode,
            js_type=js_type
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
        reference_lines = []
        
        for panel in panels:
            # Skip panels with explicit xlim
            if panel.xlim:
                continue
            
            # Collect reference lines
            if panel.reference_line is not None and not isinstance(panel.reference_line, str):
                reference_lines.append(panel.reference_line)
                
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
            
            # Include reference lines in the range calculation
            if reference_lines:
                ref_min = min(reference_lines)
                ref_max = max(reference_lines)
                data_min = min(data_min, ref_min)
                data_max = max(data_max, ref_max)
            
            # Calculate range and padding
            range_val = data_max - data_min
            
            # Ensure reference lines have adequate space
            # If we have a reference line at 0 and all data is positive
            if 0 in reference_lines and data_min >= 0:
                # Ensure negative space for the reference line to be visible
                padding_left = max(range_val * 0.1, abs(data_max) * 0.05)
                padding_right = range_val * 0.05
                return (-padding_left, data_max + padding_right)
            # If we have reference lines, ensure they're well within the range
            elif reference_lines:
                padding = range_val * 0.1 if range_val > 0 else 1
                return (data_min - padding, data_max + padding)
            # Standard case: data spans positive and negative
            elif data_min < 0 and data_max > 0:
                padding_min = abs(data_min) * 0.05
                padding_max = abs(data_max) * 0.05
                return (data_min - padding_min, data_max + padding_max)
            else:
                # Add 5% padding on each side
                if range_val > 0:
                    padding = range_val * 0.05
                else:
                    padding = abs(data_min) * 0.05 if data_min != 0 else 1
                
                return (data_min - padding, data_max + padding)
        
        # Default range if no data
        return (-1, 1)


    def _get_margin(self, type: str) -> list[float]:
        """Get margin configuration based on context."""
        if self.margin is not None:
            return self.margin
            
        # Margin configuration [bottom, left, top, right, pad]
        if type == "footer":
            # Use consistent bottom margin for all footers with x-axis
            # This ensures x-axes align between panels
            if self.show_x_axis:
                return [40, 10, 0, 10, 0]  # Increased to provide space for both x-axis and potential legend
            elif self.show_legend:
                return [25, 10, 0, 10, 0]  # Legend-only margin
            else:
                return [10, 10, 0, 10, 0]  # Minimal margin
        else:
            # Cell has no extra margins
            return [0, 10, 0, 10, 0]
    
    def _get_height(self, type: str, n_variables: int) -> int:
        """Get height configuration based on context."""
        if self.height is not None:
            return self.height
            
        if type == "footer":
            # Use consistent height for all footers with x-axis to ensure alignment
            if self.show_x_axis and self.show_legend:
                return 65  # Slightly increased for better spacing
            elif self.show_x_axis:
                return 65  # Same height even without legend to maintain alignment
            elif self.show_legend:
                return 45  # Legend only
            else:
                return 35  # Minimal footer height
        else:
            return 25  # Minimal cell height for compact row spacing
    
    def _get_legend_position(self, type: str) -> float:
        """Get legend position based on context."""
        if self.legend_position is not None:
            return self.legend_position
            
        # Legend position in paper coordinates (0=bottom, 1=top of figure)
        if type == "footer" and self.show_x_axis and self.show_legend:
            return -0.45  # Adjusted to align exactly with x-label text baseline
        elif type == "footer" and self.show_legend:
            return -0.15  # Legend only position (paper coords)
        else:
            return 0.5  # Default position (not used in footer)
    
    def _calculate_y_spacing(self, n_variables: int, padding: float = 0.35) -> list[float]:
        """Calculate y-positions for variables with optimal spacing.
        
        General formula that works for any number of variables.
        
        Args:
            n_variables: Number of variables to display
            padding: Space to leave at top and bottom (0-0.5).
                    Smaller padding = traces use more vertical space
            
        Returns:
            List of y-positions for each variable
        """
        if n_variables == 0:
            return []
        
        if n_variables == 1:
            # Single variable is always centered
            return [0.5]
        
        # General formula for multiple variables
        y_min = padding
        y_max = 1 - padding
        
        # Distribute variables evenly within the allocated space
        spacing = (y_max - y_min) / (n_variables - 1)
        y_positions = [y_min + i * spacing for i in range(n_variables)]
        
        return y_positions
    
    
    def _prepare_x_values(self, type: str, variables: list, lower_cols: list, upper_cols: list) -> tuple:
        """Prepare x-axis values for JavaScript."""
        if type == "cell":
            js_x = ", ".join([f'cell.row["{col}"]' for col in variables])
            js_x_lower = ", ".join([f'cell.row["{col}"]' for col in lower_cols]) if lower_cols else ", ".join(["null"] * len(variables))
            js_x_upper = ", ".join([f'cell.row["{col}"]' for col in upper_cols]) if upper_cols else ", ".join(["null"] * len(variables))
        else:
            if self.show_legend and not self.show_x_axis:
                js_x = ", ".join(["-999999"] * len(variables))
            else:
                js_x = ", ".join(["null"] * len(variables))
            js_x_lower = ", ".join(["null"] * len(variables))
            js_x_upper = ", ".join(["null"] * len(variables))
        
        return js_x, js_x_lower, js_x_upper
    
    def _prepare_reference_line(self, type: str) -> str:
        """Prepare reference line value for JavaScript."""
        if self.reference_line is None:
            return "null"
        
        if isinstance(self.reference_line, str):
            return f'cell.row["{self.reference_line}"]' if type == "cell" else "null"
        else:
            return str(self.reference_line)
    

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
    