"""Configuration module for forest plot system."""

from typing import Callable

from pydantic import BaseModel, Field


class Config(BaseModel):
    """Configuration for forest plot display and documentation."""

    figure_width: float | None = None
    figure_height: float | None = None
    sparkline_height: int = Field(default=30, gt=0)

    colors: list[str] | None = None
    reference_line_color: str = "#00000050"

    formatters: dict[str, Callable] | None = None

    title: str | None = None
    footnote: str | None = None
    source: str | None = None

    class Config:
        """Pydantic config."""

        arbitrary_types_allowed = True