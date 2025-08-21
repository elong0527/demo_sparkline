"""Sparkline panel module for forest plot system."""

import polars as pl

from forestly.panels.base import Panel


class SparklinePanel(Panel):
    """Display point estimates with error bars."""

    lower: str | list[str] | None = None
    upper: str | list[str] | None = None
    reference_line: float | str | None = None
    reference_line_color: str | None = None
    xlim: tuple[float, float] | None = None

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
            if isinstance(self.variables, str):
                estimates = [self.variables]
            elif isinstance(self.variables, list):
                estimates = self.variables
            else:
                estimates = []
            result["estimates"] = estimates

        # Handle confidence intervals
        if self.lower:
            lowers = [self.lower] if isinstance(self.lower, str) else self.lower
            result["lower_bounds"] = lowers

        if self.upper:
            uppers = [self.upper] if isinstance(self.upper, str) else self.upper
            result["upper_bounds"] = uppers

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
            labels = [self.labels] if isinstance(self.labels, str) else self.labels
            result["labels"] = labels

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
            if isinstance(self.variables, str):
                required.add(self.variables)
            elif isinstance(self.variables, list):
                required.update(self.variables)

        # Add lower bound columns
        if self.lower:
            if isinstance(self.lower, str):
                required.add(self.lower)
            elif isinstance(self.lower, list):
                required.update(self.lower)

        # Add upper bound columns
        if self.upper:
            if isinstance(self.upper, str):
                required.add(self.upper)
            elif isinstance(self.upper, list):
                required.update(self.upper)

        # Add reference line column if it's a column name
        if isinstance(self.reference_line, str):
            required.add(self.reference_line)

        return required

    def generate_javascript(self) -> str:
        """Generate JavaScript code for sparkline rendering.

        Returns:
            JavaScript code as string
        """
        js_template = """
        function(cellInfo) {
            const value = cellInfo.value;
            const lower = cellInfo.row['${lower}'];
            const upper = cellInfo.row['${upper}'];
            
            const trace = {
                x: [value],
                y: [0],
                error_x: {
                    type: 'data',
                    symmetric: false,
                    array: [upper - value],
                    arrayminus: [value - lower],
                    visible: true
                },
                type: 'scatter',
                mode: 'markers',
                marker: {size: 8}
            };
            
            const layout = {
                height: ${height},
                width: ${width},
                margin: {l: 0, r: 0, t: 0, b: 0},
                xaxis: {
                    range: [${xmin}, ${xmax}],
                    zeroline: false,
                    showticklabels: false
                },
                yaxis: {
                    visible: false,
                    range: [-0.5, 0.5]
                },
                showlegend: false,
                paper_bgcolor: 'rgba(0,0,0,0)',
                plot_bgcolor: 'rgba(0,0,0,0)'
            };
            
            ${reference_line_code}
            
            return React.createElement(Plotly.Plot, {
                data: [trace],
                layout: layout,
                config: {displayModeBar: false}
            });
        }
        """
        return js_template

    def validate_confidence_intervals(self, data: pl.DataFrame) -> None:
        """Validate that confidence intervals contain point estimates.

        Args:
            data: Input DataFrame

        Raises:
            ValueError: If confidence intervals are invalid
        """
        if not (self.variables and self.lower and self.upper):
            return

        estimates = [self.variables] if isinstance(self.variables, str) else self.variables
        lowers = [self.lower] if isinstance(self.lower, str) else self.lower
        uppers = [self.upper] if isinstance(self.upper, str) else self.upper

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