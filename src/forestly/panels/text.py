"""Text panel module for forest plot system."""

import polars as pl

from forestly.panels.base import Panel
from forestly.utils.common import normalize_to_list, normalize_width_to_list


class TextPanel(Panel):
    """Display one or more text/numeric columns."""

    group_by: str | list[str] | None = None
    align: str = "center"  # Alignment for columns: "left", "center", or "right"

    def render(self, data: pl.DataFrame) -> dict:
        """Render panel data for display.

        Args:
            data: Input DataFrame

        Returns:
            Rendered data dictionary
        """
        result = {"data": data}

        if self.variables:
            if isinstance(self.variables, dict):
                columns = list(self.variables.keys())
            else:
                columns = normalize_to_list(self.variables)
            result["columns"] = columns

        if self.group_by:
            result["group_by"] = normalize_to_list(self.group_by)

        if self.labels:
            result["labels"] = normalize_to_list(self.labels)

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
            if isinstance(self.variables, dict):
                required.update(self.variables.keys())
            else:
                required.update(normalize_to_list(self.variables))

        if self.group_by:
            required.update(normalize_to_list(self.group_by))

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

        group_cols = normalize_to_list(self.group_by)

        # Sort by group columns to ensure proper hierarchy
        return data.sort(group_cols)