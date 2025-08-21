"""Base panel module for forest plot system."""

from abc import ABC, abstractmethod

import polars as pl
from pydantic import BaseModel, ConfigDict


class Panel(BaseModel, ABC):
    """Base class for display panels."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    variables: str | list[str] | dict[str, str] | None = None
    title: str | None = None
    labels: str | list[str] | None = None
    width: int | list[int] | None = None
    footer: str = ""

    @abstractmethod
    def render(self, data: pl.DataFrame) -> dict:
        """Render panel data for display.

        Args:
            data: Input DataFrame

        Returns:
            Rendered data dictionary
        """
        pass

    @abstractmethod
    def get_required_columns(self) -> set[str]:
        """Get columns required by this panel.

        Returns:
            Set of required column names
        """
        pass

    def validate_columns(self, data: pl.DataFrame) -> None:
        """Validate that required columns exist in data.

        Args:
            data: Input DataFrame

        Raises:
            ValueError: If required columns are missing
        """
        required = self.get_required_columns()
        available = set(data.columns)
        missing = required - available

        if missing:
            raise ValueError(f"Missing required columns: {missing}")