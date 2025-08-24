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
        # Use ForestPlot's methods for data preparation
        data = forest_plot.get_prepared_data()
        forest_plot.prepare_panels()
        group_by = forest_plot.get_grouping_columns()
        
        # Create columns and column groups from panels
        columns, column_groups = self._create_columns_and_groups(forest_plot.panels, forest_plot.config, forest_plot.get_used_columns())
        
        # Build and return Reactable
        return self._build_reactable(data, columns, column_groups, group_by)

    def _create_columns_and_groups(self, panels: list, config, used_columns: list[str]) -> tuple[list[Column], list[ColGroup]]:
        """Create Reactable columns and column groups from panels.

        Args:
            panels: List of Panel objects
            config: Config object
            used_columns: List of all columns used by panels

        Returns:
            Tuple of (List of Column objects, List of ColGroup objects)
        """
        columns = []
        column_groups = []
        display_columns = set()

        for panel in panels:
            if isinstance(panel, TextPanel):
                panel_columns, panel_group = self._create_text_columns_with_group(panel, config)
                columns.extend(panel_columns)
                if panel_group:
                    column_groups.append(panel_group)
                # Track displayed columns
                for col in panel_columns:
                    display_columns.add(col.id)
            elif isinstance(panel, SparklinePanel):
                panel_columns = self._create_sparkline_columns(panel, config)
                columns.extend(panel_columns)
                # Track displayed columns
                for col in panel_columns:
                    display_columns.add(col.id)
        
        # Add hidden columns for data that's not displayed but needed for sparklines
        for col_name in used_columns:
            if col_name not in display_columns:
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
                # Use panel's generate_javascript method with type="cell" for main sparkline
                panel.js_function = panel.generate_javascript(
                    colors=config.colors if hasattr(config, 'colors') else None,
                    type="cell"
                )
            js_func = panel.js_function
            
            # Use first variable as column ID
            col_args = {
                "id": variables[0],
                "name": panel.title if panel.title else variables[0],
                "cell": JS(js_func),  # Use JS wrapper for JavaScript code
            }
            
            if panel.width:
                col_args["width"] = panel.width
            
            # Handle footer display: combine custom footer text with x-axis/legend
            if panel.show_x_axis or panel.show_legend:
                # Generate footer JavaScript with x-axis and/or legend
                footer_js = panel.generate_javascript(
                    colors=config.colors if hasattr(config, 'colors') else None,
                    type="footer"
                )
                if footer_js:
                    # If there's also a custom footer text, we'll need to combine them
                    if panel.footer and not panel.footer.startswith("function"):
                        # For now, use the JavaScript footer (x-axis/legend)
                        # The custom text footer can be shown as part of the x-label
                        col_args["footer"] = JS(footer_js)
                    else:
                        col_args["footer"] = JS(footer_js)
            elif panel.footer:
                # Only custom footer text, no x-axis or legend
                if panel.footer.startswith("function"):
                    col_args["footer"] = JS(panel.footer)
                else:
                    col_args["footer"] = panel.footer
            
            columns.append(Column(**col_args))

        return columns

    def _build_reactable(self, data: pl.DataFrame, columns: list[Column], 
                        column_groups: list[ColGroup], group_by: list[str]) -> Reactable:
        """Build Reactable with configuration.

        Args:
            data: Prepared DataFrame
            columns: List of Column objects
            column_groups: List of ColGroup objects
            group_by: List of grouping column names

        Returns:
            Reactable object
        """
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