from dataclasses import dataclass

import pandas as pd


@dataclass(slots=True)
class QualityCheckResult:
    is_valid: bool
    warnings: list[str]
    summary: dict[str, int | bool]


def run_quality_checks(dataframe: pd.DataFrame) -> QualityCheckResult:
    warnings: list[str] = []

    row_count = len(dataframe)
    if row_count == 0:
        return QualityCheckResult(
            is_valid=False,
            warnings=["Batch is empty."],
            summary={
                "row_count": 0,
                "duplicate_rows": 0,
                "rows_with_missing_values": 0,
                "has_duplicates": False,
                "has_missing_values": False,
            },
        )

    duplicate_rows = int(dataframe.duplicated().sum())
    if duplicate_rows:
        warnings.append(f"Detected {duplicate_rows} duplicated rows in batch.")

    rows_with_missing_values = int(dataframe.isnull().any(axis=1).sum())
    if rows_with_missing_values:
        warnings.append(f"Detected {rows_with_missing_values} rows with missing values.")

    return QualityCheckResult(
        is_valid=rows_with_missing_values == 0,
        warnings=warnings,
        summary={
            "row_count": row_count,
            "duplicate_rows": duplicate_rows,
            "rows_with_missing_values": rows_with_missing_values,
            "has_duplicates": duplicate_rows > 0,
            "has_missing_values": rows_with_missing_values > 0,
        },
    )
