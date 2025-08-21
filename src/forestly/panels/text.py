"""Text panel module for forest plot system."""

import polars as pl

from forestly.panels.base import Panel


class TextPanel(Panel):
    """Display one or more text/numeric columns."""

    group_by: str | list[str] | None = None

    def render(self, data: pl.DataFrame) -> dict:
        """Render panel data for display.

        Args:
            data: Input DataFrame

        Returns:
            Rendered data dictionary
        """
        result = {"data": data}

        if self.variables:
            if isinstance(self.variables, str):
                columns = [self.variables]
            elif isinstance(self.variables, list):
                columns = self.variables
            elif isinstance(self.variables, dict):
                columns = list(self.variables.keys())
            else:
                columns = []

            result["columns"] = columns

        if self.group_by:
            group_cols = (
                [self.group_by] if isinstance(self.group_by, str) else self.group_by
            )
            result["group_by"] = group_cols

        if self.labels:
            labels = [self.labels] if isinstance(self.labels, str) else self.labels
            result["labels"] = labels

        if self.width:
            widths = [self.width] if isinstance(self.width, int) else self.width
            result["widths"] = widths

        result["title"] = self.title
        result["footer"] = self.footer

        return result

    def get_required_columns(self) -> set[str]:
        """Get columns required by this panel.

        Returns:
            Set of required column names
        """
        required = set()

        if self.variables:
            if isinstance(self.variables, str):
                required.add(self.variables)
            elif isinstance(self.variables, list):
                required.update(self.variables)
            elif isinstance(self.variables, dict):
                required.update(self.variables.keys())

        if self.group_by:
            if isinstance(self.group_by, str):
                required.add(self.group_by)
            else:
                required.update(self.group_by)

        return required

    def apply_grouping(self, data: pl.DataFrame) -> pl.DataFrame:
        """Apply hierarchical grouping to data.

        Args:
            data: Input DataFrame

        Returns:
            DataFrame with grouping applied
        """
        if not self.group_by:
            return data

        group_cols = (
            [self.group_by] if isinstance(self.group_by, str) else self.group_by
        )

        # Sort by group columns to ensure proper hierarchy
        return data.sort(group_cols)