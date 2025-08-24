"""Common utility functions for the forestly package."""

from typing import Any


def normalize_to_list(value: str | list[str] | None) -> list[str]:
    """Convert string or list to list, handling None gracefully.
    
    Args:
        value: A string, list of strings, or None
        
    Returns:
        List of strings (empty list if value is None)
    """
    if value is None:
        return []
    return [value] if isinstance(value, str) else value


def normalize_width_to_list(width: int | list[int] | None, count: int) -> list[int | None]:
    """Normalize width to a list matching the count.
    
    Args:
        width: Single width, list of widths, or None
        count: Expected number of width values
        
    Returns:
        List of width values or None values
    """
    if width is None:
        return [None] * count
    if isinstance(width, int):
        return [width] * count
    # Ensure list has correct length
    result = list(width)
    if len(result) < count:
        result.extend([None] * (count - len(result)))
    return result[:count]


def safe_get_color(colors: list[str] | None, index: int, default: str = "#4A90E2") -> str:
    """Safely get a color from list or return default.
    
    Args:
        colors: List of color strings or None
        index: Index to retrieve
        default: Default color if not found
        
    Returns:
        Color string
    """
    if colors and index < len(colors):
        return colors[index]
    return default


def ensure_list_length(items: list[Any], target_length: int, default: Any = None) -> list[Any]:
    """Ensure a list has the target length.
    
    Args:
        items: Input list
        target_length: Desired length
        default: Default value for padding
        
    Returns:
        List with target length
    """
    result = list(items)
    if len(result) < target_length:
        result.extend([default] * (target_length - len(result)))
    return result[:target_length]