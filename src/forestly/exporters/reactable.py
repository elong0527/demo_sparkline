"""Reactable exporter for forest plot system."""

import polars as pl
from reactable import Column, Reactable, JS, Theme

from forestly.core.forest_plot import ForestPlot
from forestly.panels.sparkline import SparklinePanel
from forestly.panels.text import TextPanel


class ReactableExporter:
    """Export ForestPlot to interactive Reactable table."""

    def export(self, forest_plot: ForestPlot) -> Reactable:
        """Export to Reactable with panels.

        Args:
            forest_plot: ForestPlot instance

        Returns:
            Reactable object
        """
        # Convert polars to pandas for reactable
        data = forest_plot.data.to_pandas()

        # Create columns from panels
        columns = self._create_columns(forest_plot.panels, forest_plot.config)

        # Find grouping columns
        group_by = self._get_grouping_columns(forest_plot.panels)

        # Create Reactable
        reactable_args = {
            "data": data,
            "columns": columns,
            "resizable": True,
            "filterable": True,
            "searchable": True,
            "default_page_size": 10,
            "show_page_size_options": True,
            "borderless": True,
            "striped": True,
            "highlight": True,
            "full_width": True,
            "width": 1200,
            "wrap": False,
            "theme": Theme(
                cell_padding="0px 8px"
            ),
        }

        # Add grouping if specified
        if group_by:
            # For single group column
            if len(group_by) == 1:
                reactable_args["group_by"] = group_by[0]
            else:
                # For multiple group columns (nested grouping)
                reactable_args["group_by"] = group_by
            
            # Set default expanded to True so nested rows are visible by default
            reactable_args["default_expanded"] = True
            
            # Enable pagination for sub rows
            reactable_args["paginate_sub_rows"] = True

        # Add title if specified
        if forest_plot.config.title:
            reactable_args["element_id"] = "forest-plot-table"

        return Reactable(**reactable_args)

    def _create_columns(self, panels: list, config) -> list[Column]:
        """Create Reactable columns from panels.

        Args:
            panels: List of Panel objects
            config: Config object

        Returns:
            List of Column objects
        """
        columns = []

        for panel in panels:
            if isinstance(panel, TextPanel):
                columns.extend(self._create_text_columns(panel, config))
            elif isinstance(panel, SparklinePanel):
                columns.extend(self._create_sparkline_columns(panel, config))

        return columns

    def _create_text_columns(self, panel: TextPanel, config) -> list[Column]:
        """Create columns for TextPanel.

        Args:
            panel: TextPanel instance
            config: Config object

        Returns:
            List of Column objects
        """
        columns = []

        # Add group_by columns if they exist and aren't already in variables
        if panel.group_by:
            group_cols = [panel.group_by] if isinstance(panel.group_by, str) else panel.group_by
            for group_col in group_cols:
                # Check if this group column is not already included in variables
                variables_list = [panel.variables] if isinstance(panel.variables, str) else panel.variables if panel.variables else []
                if group_col not in variables_list:
                    col_args = {
                        "id": group_col,
                        "name": group_col.replace("_", " ").title(),  # Format column name
                        "aggregate": "unique",  # Show unique value for grouped rows
                    }
                    if panel.width:
                        col_args["width"] = 150  # Default width for group columns
                    columns.append(Column(**col_args))

        if panel.variables:
            variables = (
                [panel.variables]
                if isinstance(panel.variables, str)
                else panel.variables
            )
            labels = (
                [panel.labels] if isinstance(panel.labels, str) else panel.labels
            ) if panel.labels else variables
            widths = (
                [panel.width] if isinstance(panel.width, int) else panel.width
            ) if panel.width else [None] * len(variables)

            for var, label, width in zip(variables, labels, widths):
                col_args = {
                    "id": var,
                    "name": label if label else var,
                }

                if width:
                    col_args["width"] = width

                # Apply formatter if specified
                if config.formatters and var in config.formatters:
                    formatter = config.formatters[var]
                    # Create a closure to capture the formatter correctly
                    def make_cell_formatter(fmt):
                        return lambda cell_info: fmt(cell_info.value)
                    col_args["cell"] = make_cell_formatter(formatter)

                columns.append(Column(**col_args))

        return columns

    def _create_sparkline_columns(self, panel: SparklinePanel, config) -> list[Column]:
        """Create columns for SparklinePanel.

        Args:
            panel: SparklinePanel instance
            config: Config object

        Returns:
            List of Column objects
        """
        columns = []

        if panel.variables:
            variables = (
                [panel.variables]
                if isinstance(panel.variables, str)
                else panel.variables
            )

            for i, var in enumerate(variables):
                # Generate JavaScript function for sparkline
                js_func = self._generate_sparkline_js(panel, var, i, config)

                col_args = {
                    "id": var,
                    "name": panel.title if panel.title else var,
                    "cell": JS(js_func),  # Use JS wrapper for JavaScript code
                }

                if panel.width:
                    col_args["width"] = panel.width

                columns.append(Column(**col_args))

        return columns

    def _generate_sparkline_js(
        self, panel: SparklinePanel, variable: str, index: int, config
    ) -> str:
        """Generate JavaScript function for sparkline rendering.

        Args:
            panel: SparklinePanel instance
            variable: Variable name for this sparkline
            index: Index of variable in panel
            config: Config object

        Returns:
            JavaScript function as string
        """
        # Get lower and upper bounds
        lower_col = panel.lower[index] if isinstance(panel.lower, list) else panel.lower if panel.lower else None
        upper_col = panel.upper[index] if isinstance(panel.upper, list) else panel.upper if panel.upper else None

        # Determine x-axis limits
        if panel.xlim:
            xlim_str = f"[{panel.xlim[0]}, {panel.xlim[1]}]"
        else:
            xlim_str = "[0, 2]"  # Default range

        # Reference line
        ref_line = "null"
        if panel.reference_line is not None:
            if isinstance(panel.reference_line, str):
                ref_line = f"cell.row['{panel.reference_line}']"
            else:
                ref_line = str(panel.reference_line)

        # Color
        color = config.colors[index] if config.colors and len(config.colors) > index else "#4A90E2"
        
        # Generate JavaScript function
        js_code = f"""function(cell, state) {{
  // Check if value exists
  const value = cell.row['{variable}'];
  if (value == null || value === undefined) return null;
  
  // Get error bar values if they exist
  {f"const lower = cell.row['{lower_col}'];" if lower_col else "const lower = null;"}
  {f"const upper = cell.row['{upper_col}'];" if upper_col else "const upper = null;"}
  
  // Create the trace
  const trace = {{
    x: [value],
    y: [0],
    type: 'scatter',
    mode: 'markers',
    marker: {{
      size: 8,
      color: '{color}'
    }},
    name: '',
    hoverinfo: 'x'
  }};
  
  // Add error bars if bounds exist
  if (lower != null && upper != null) {{
    trace.error_x = {{
      type: 'data',
      symmetric: false,
      array: [upper - value],
      arrayminus: [value - lower],
      visible: true,
      color: '{color}',
      thickness: 1.5,
      width: 3
    }};
  }}
  
  // Layout configuration
  const layout = {{
    height: {config.sparkline_height},
    width: {panel.width if panel.width else 200},
    margin: {{l: 5, r: 5, t: 5, b: 5}},
    xaxis: {{
      range: {xlim_str},
      zeroline: false,
      showticklabels: false,
      showgrid: false,
      fixedrange: true
    }},
    yaxis: {{
      visible: false,
      range: [-0.5, 0.5],
      fixedrange: true
    }},
    showlegend: false,
    paper_bgcolor: 'rgba(0,0,0,0)',
    plot_bgcolor: 'rgba(0,0,0,0)',
    shapes: []
  }};
  
  // Add reference line if specified
  const refLine = {ref_line};
  if (refLine != null && refLine !== undefined) {{
    layout.shapes.push({{
      type: 'line',
      x0: refLine,
      x1: refLine,
      y0: -0.5,
      y1: 0.5,
      line: {{
        color: '{panel.reference_line_color if panel.reference_line_color else config.reference_line_color}',
        width: 1,
        dash: 'dash'
      }}
    }});
  }}
  
  // Create Plotly component
  const PlotComponent = window.createPlotlyComponent ? window.createPlotlyComponent(window.Plotly) : 
    class extends React.Component {{
      componentDidMount() {{
        window.Plotly.newPlot(this.el, this.props.data, this.props.layout, this.props.config);
      }}
      componentWillUnmount() {{
        window.Plotly.purge(this.el);
      }}
      render() {{
        return React.createElement('div', {{ref: (el) => this.el = el}});
      }}
    }};
  
  return React.createElement(PlotComponent, {{
    data: [trace],
    layout: layout,
    config: {{displayModeBar: false, responsive: true}}
  }});
}}"""

        return js_code

    def _get_grouping_columns(self, panels: list) -> list[str]:
        """Get grouping columns from panels.

        Args:
            panels: List of Panel objects

        Returns:
            List of grouping column names
        """
        for panel in panels:
            if isinstance(panel, TextPanel) and panel.group_by:
                if isinstance(panel.group_by, str):
                    return [panel.group_by]
                else:
                    return panel.group_by
        return []