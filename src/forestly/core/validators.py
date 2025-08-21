"""Data validation module for forest plot system."""

import polars as pl


def validate_confidence_intervals(
    data: pl.DataFrame,
    estimate_col: str,
    lower_col: str,
    upper_col: str,
) -> None:
    """Validate that confidence intervals contain point estimates.

    Args:
        data: Input DataFrame
        estimate_col: Column name for point estimate
        lower_col: Column name for lower bound
        upper_col: Column name for upper bound

    Raises:
        ValueError: If confidence intervals are invalid
    """
    # Check columns exist
    missing_cols = []
    for col in [estimate_col, lower_col, upper_col]:
        if col not in data.columns:
            missing_cols.append(col)

    if missing_cols:
        raise ValueError(f"Missing columns: {missing_cols}")

    # Check that lower <= estimate <= upper
    invalid = data.filter(
        (pl.col(lower_col) > pl.col(estimate_col))
        | (pl.col(estimate_col) > pl.col(upper_col))
    )

    if len(invalid) > 0:
        raise ValueError(
            f"Invalid confidence intervals: {lower_col} <= {estimate_col} <= {upper_col} "
            f"violated in {len(invalid)} rows"
        )


def validate_grouping_structure(
    data: pl.DataFrame, group_cols: list[str]
) -> None:
    """Validate hierarchical grouping structure.

    Args:
        data: Input DataFrame
        group_cols: List of grouping columns in hierarchical order

    Raises:
        ValueError: If grouping structure is invalid
    """
    # Check columns exist
    missing_cols = [col for col in group_cols if col not in data.columns]
    if missing_cols:
        raise ValueError(f"Missing grouping columns: {missing_cols}")

    # Check for nulls in grouping columns
    for col in group_cols:
        null_count = data.filter(pl.col(col).is_null()).height
        if null_count > 0:
            raise ValueError(f"Null values found in grouping column '{col}': {null_count} rows")

    # Check hierarchical consistency
    if len(group_cols) > 1:
        # Each parent group should have consistent child groups
        for i in range(len(group_cols) - 1):
            parent_col = group_cols[i]
            child_col = group_cols[i + 1]

            # Group by parent and check for duplicate child values across different parents
            grouped = data.group_by([parent_col, child_col]).agg(pl.count())
            child_parents = grouped.group_by(child_col).agg(
                pl.col(parent_col).n_unique().alias("n_parents")
            )

            multi_parent_children = child_parents.filter(pl.col("n_parents") > 1)
            if len(multi_parent_children) > 0:
                problematic = multi_parent_children[child_col].to_list()
                raise ValueError(
                    f"Hierarchical inconsistency: {child_col} values {problematic} "
                    f"appear under multiple {parent_col} values"
                )


def validate_numeric_columns(
    data: pl.DataFrame, columns: list[str]
) -> None:
    """Validate that specified columns contain numeric data.

    Args:
        data: Input DataFrame
        columns: List of column names to validate

    Raises:
        ValueError: If columns are not numeric
    """
    for col in columns:
        if col not in data.columns:
            raise ValueError(f"Column '{col}' not found in data")

        dtype = data[col].dtype
        if dtype not in [pl.Int8, pl.Int16, pl.Int32, pl.Int64,
                        pl.UInt8, pl.UInt16, pl.UInt32, pl.UInt64,
                        pl.Float32, pl.Float64]:
            raise ValueError(f"Column '{col}' is not numeric (type: {dtype})")


def validate_p_values(data: pl.DataFrame, p_value_cols: list[str]) -> None:
    """Validate that p-values are in valid range [0, 1].

    Args:
        data: Input DataFrame
        p_value_cols: List of p-value column names

    Raises:
        ValueError: If p-values are outside valid range
    """
    for col in p_value_cols:
        if col not in data.columns:
            continue

        # Check range
        invalid = data.filter((pl.col(col) < 0) | (pl.col(col) > 1))
        if len(invalid) > 0:
            raise ValueError(
                f"P-values in column '{col}' outside range [0, 1]: {len(invalid)} rows"
            )


def validate_reference_line(
    data: pl.DataFrame,
    reference_col: str | None = None,
    reference_value: float | None = None,
) -> None:
    """Validate reference line configuration.

    Args:
        data: Input DataFrame
        reference_col: Column name for dynamic reference line
        reference_value: Fixed value for reference line

    Raises:
        ValueError: If reference line configuration is invalid
    """
    if reference_col and reference_value is not None:
        raise ValueError(
            "Cannot specify both reference_col and reference_value"
        )

    if reference_col:
        if reference_col not in data.columns:
            raise ValueError(f"Reference column '{reference_col}' not found in data")

        # Check if numeric
        validate_numeric_columns(data, [reference_col])


def check_data_consistency(data: pl.DataFrame) -> dict:
    """Perform general data consistency checks.

    Args:
        data: Input DataFrame

    Returns:
        Dictionary with consistency check results
    """
    results = {
        "n_rows": data.height,
        "n_cols": data.width,
        "has_nulls": {},
        "duplicates": None,
        "warnings": [],
    }

    # Check for nulls
    for col in data.columns:
        null_count = data[col].null_count()
        if null_count > 0:
            results["has_nulls"][col] = null_count

    # Check for complete duplicates
    n_unique = data.n_unique()
    if n_unique < data.height:
        results["duplicates"] = data.height - n_unique
        results["warnings"].append(
            f"Found {results['duplicates']} duplicate rows"
        )

    # Check for empty data
    if data.height == 0:
        results["warnings"].append("DataFrame is empty")

    # Check for single row
    if data.height == 1:
        results["warnings"].append("DataFrame contains only one row")

    return results