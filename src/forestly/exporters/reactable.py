"""Reactable exporter for forest plot system."""

import polars as pl
from reactable import Column, Reactable, JS, Theme, ColGroup

from forestly.core.forest_plot import ForestPlot
from forestly.panels.sparkline import SparklinePanel
from forestly.panels.text import TextPanel
from forestly.utils.common import normalize_to_list, normalize_width_to_list


class ReactableExporter:
    """Export ForestPlot to interactive Reactable table."""

    def export(self, forest_plot: ForestPlot) -> Reactable:
        """Export to Reactable with panels.

        Args:
            forest_plot: ForestPlot instance

        Returns:
            Reactable object
        """
        # Get all column names used in panels (including hidden data columns)
        used_columns = self._get_used_columns(forest_plot.panels)
        
        # Select only the columns that are used in panels
        data = forest_plot.data.select(used_columns)
        
        # Calculate xlim ranges for panels that need them
        self._infer_xlim_for_panels(forest_plot.panels, data)
        
        # Create columns and column groups from panels
        columns, column_groups = self._create_columns_and_groups(forest_plot.panels, forest_plot.config)

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
            "width": "100%",
            "wrap": False,
            "theme": Theme(
                cell_padding="0px 8px"
            ),
        }
        
        # Add column groups if any
        if column_groups:
            reactable_args["column_groups"] = column_groups

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



        return Reactable(**reactable_args)

    def _create_columns_and_groups(self, panels: list, config) -> tuple[list[Column], list[ColGroup]]:
        """Create Reactable columns and column groups from panels.

        Args:
            panels: List of Panel objects
            config: Config object

        Returns:
            Tuple of (List of Column objects, List of ColGroup objects)
        """
        columns = []
        column_groups = []
        
        # Keep track of which columns should be displayed
        display_columns = set()

        for panel in panels:
            if isinstance(panel, TextPanel):
                panel_columns, panel_group = self._create_text_columns_with_group(panel, config)
                columns.extend(panel_columns)
                if panel_group:
                    column_groups.append(panel_group)
                # Add TextPanel columns to display
                for col in panel_columns:
                    display_columns.add(col.id)
            elif isinstance(panel, SparklinePanel):
                panel_columns = self._create_sparkline_columns(panel, config)
                columns.extend(panel_columns)
                # Add SparklinePanel columns to display
                for col in panel_columns:
                    display_columns.add(col.id)
        
        # Get all data column names
        all_data_columns = self._get_used_columns(panels)
        
        # Add hidden columns for data that's not displayed but needed for sparklines
        for col_name in all_data_columns:
            if col_name not in display_columns:
                # Create a hidden column
                columns.append(Column(
                    id=col_name,
                    show=False  # Hide this column
                ))

        return columns, column_groups

    def _create_text_columns_with_group(self, panel: TextPanel, config) -> tuple[list[Column], ColGroup | None]:
        """Create columns and optional column group for TextPanel.

        Args:
            panel: TextPanel instance
            config: Config object

        Returns:
            Tuple of (List of Column objects, Optional ColGroup object)
        """
        columns = []
        column_group = None
        variable_columns = []

        # Handle group_by columns first
        if panel.group_by:
            group_cols = normalize_to_list(panel.group_by)
            for group_col in group_cols:
                variables_list = normalize_to_list(panel.variables) if panel.variables else []
                if group_col not in variables_list:
                    col_args = {
                        "id": group_col,
                        "name": group_col.replace("_", " ").title(),
                        "aggregate": "unique",
                    }
                    if panel.width:
                        col_args["width"] = 150
                    columns.append(Column(**col_args))

        # Handle main variables
        if panel.variables:
            variables = normalize_to_list(panel.variables)
            labels = normalize_to_list(panel.labels) if panel.labels else variables
            widths = normalize_width_to_list(panel.width, len(variables))

            # Create columns for each variable
            for var, label, width in zip(variables, labels, widths):
                # Determine display name based on context
                if panel.title and len(variables) == 1:
                    display_name = panel.title
                else:
                    display_name = label
                
                col_args = {
                    "id": var,
                    "name": display_name,
                }

                if width:
                    col_args["width"] = width

                # Apply formatter if specified
                if config.formatters and var in config.formatters:
                    formatter = config.formatters[var]
                    def make_cell_formatter(fmt):
                        return lambda cell_info: fmt(cell_info.value)
                    col_args["cell"] = make_cell_formatter(formatter)

                column = Column(**col_args)
                columns.append(column)
                variable_columns.append(var)

            # Create column group if we have a title and multiple variables
            if panel.title and len(variables) > 1:
                column_group = ColGroup(
                    name=panel.title,
                    columns=variable_columns
                )

        return columns, column_group

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
            variables = normalize_to_list(panel.variables)
            
            # Generate JavaScript if not provided
            if not panel.js_function:
                # Use panel's generate_javascript method
                panel.js_function = panel.generate_javascript(colors=config.colors if hasattr(config, 'colors') else None)
            js_func = panel.js_function
            
            # Use first variable as column ID
            col_args = {
                "id": variables[0],
                "name": panel.title if panel.title else variables[0],
                "cell": JS(js_func),  # Use JS wrapper for JavaScript code
            }
            
            if panel.width:
                col_args["width"] = panel.width
            
            # Add footer if specified in panel
            if panel.footer:
                # Check if footer is JavaScript (for legend)
                if panel.footer.startswith("function"):
                    col_args["footer"] = JS(panel.footer)
                else:
                    col_args["footer"] = panel.footer
            # Auto-generate legend for multi-variable sparklines with labels
            elif panel.labels and len(variables) > 1:
                legend_js = panel.generate_legend_javascript(colors=config.colors if hasattr(config, 'colors') else None)
                if legend_js:
                    col_args["footer"] = JS(legend_js)
            
            columns.append(Column(**col_args))

        return columns


    def _get_used_columns(self, panels: list) -> list[str]:
        """Get all column names used in panels in the order they appear.

        Args:
            panels: List of Panel objects

        Returns:
            List of column names used in panel order
        """
        used_columns = []
        seen = set()
        
        for panel in panels:
            panel_columns = []
            
            if isinstance(panel, TextPanel):
                # Add group_by columns first
                if panel.group_by:
                    panel_columns.extend(normalize_to_list(panel.group_by))
                
                # Then add variable columns
                if panel.variables:
                    panel_columns.extend(normalize_to_list(panel.variables))
                        
            elif isinstance(panel, SparklinePanel):
                # For SparklinePanel, we need all the columns it uses
                # Add main variable columns
                if panel.variables:
                    panel_columns.extend(normalize_to_list(panel.variables))
                
                # Add lower bound columns
                if panel.lower:
                    panel_columns.extend(normalize_to_list(panel.lower))
                
                # Add upper bound columns
                if panel.upper:
                    panel_columns.extend(normalize_to_list(panel.upper))
                
                # Add reference line column if it's a column name
                if panel.reference_line and isinstance(panel.reference_line, str):
                    panel_columns.append(panel.reference_line)
            
            # Add panel columns to used_columns, avoiding duplicates
            for col in panel_columns:
                if col not in seen:
                    seen.add(col)
                    used_columns.append(col)
        
        return used_columns

    def _infer_xlim_for_panels(self, panels: list, data: pl.DataFrame) -> None:
        """Infer xlim for panels based on data if not specified.

        Args:
            panels: List of Panel objects
            data: DataFrame with the data
        """
        for panel in panels:
            if isinstance(panel, SparklinePanel) and not panel.xlim:
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
                        
                        panel.xlim = (data_min - padding, data_max + padding)

    def _get_grouping_columns(self, panels: list) -> list[str]:
        """Get grouping columns from panels.

        Args:
            panels: List of Panel objects

        Returns:
            List of grouping column names
        """
        for panel in panels:
            if isinstance(panel, TextPanel) and panel.group_by:
                return normalize_to_list(panel.group_by)
        return []