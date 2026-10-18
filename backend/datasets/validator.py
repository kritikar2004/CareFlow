from pathlib import Path
from typing import Any

import pandas as pd


# ============================================================
# CareFlow Phase 8 - Dataset Validation
# ============================================================

HISTORY_REQUIRED_COLUMNS = [
    "date",
    "admissions",
    "icu_demand",
]

HISTORY_RECOMMENDED_COLUMNS = [
    "emergency_visits",
    "avg_length_of_stay",
    "outpatient_visits",
]

RESOURCE_REQUIRED_COLUMNS = [
    "date",
    "resource_category",
    "resource_name",
    "unit",
    "quantity_available",
    "quantity_used",
    "reference_capacity",
]

DISEASE_REQUIRED_COLUMNS = [
    "date",
    "disease",
    "cases",
]

HISTORY_NUMERIC_COLUMNS = [
    "admissions",
    "icu_demand",
    "emergency_visits",
    "avg_length_of_stay",
    "outpatient_visits",
]

RESOURCE_NUMERIC_COLUMNS = [
    "quantity_available",
    "quantity_used",
    "reference_capacity",
]

DISEASE_NUMERIC_COLUMNS = [
    "cases",
]


# ============================================================
# Historical Period Disclaimer
# ============================================================

def generate_period_disclaimer(days: int) -> str:
    """
    Generate the historical-data disclaimer according to
    the CareFlow Master specification.
    """

    if days < 30:
        return (
            f"Very Limited Historical Data: Your dataset contains {days} days "
            "of historical data. Reliability may be low."
        )

    if days < 90:
        return (
            f"Limited Historical Data: Your dataset contains {days} days "
            "of historical data. CareFlow can generate a forecast, but "
            "limited historical data may reduce forecast reliability. "
            "Recommended: 12+ months of historical data for better "
            "seasonal patterns."
        )

    if days < 365:
        return (
            f"Limited Historical Data: Your dataset contains {days} days "
            "of historical data. CareFlow can generate a forecast, but "
            "limited historical data may reduce forecast reliability. "
            "Recommended: 12+ months of historical data for better "
            "seasonal patterns."
        )

    if days < 730:
        return (
            f"Historical Data Available: Your dataset contains {days} days "
            "of historical data. This meets the recommended 12+ month "
            "history for forecasting."
        )

    return (
        f"Historical Data Available: Your dataset contains {days} days "
        "of historical data. This provides 24+ months of historical "
        "coverage and better seasonal history where relevant."
    )


# ============================================================
# Column Validation
# ============================================================

def validate_columns(
    dataframe: pd.DataFrame,
    required_columns: list[str],
    recommended_columns: list[str] | None = None,
) -> dict[str, Any]:
    """
    Validate required and recommended columns.
    """

    actual_columns = list(dataframe.columns)

    missing_required = [
        column
        for column in required_columns
        if column not in actual_columns
    ]

    missing_recommended = []

    if recommended_columns:
        missing_recommended = [
            column
            for column in recommended_columns
            if column not in actual_columns
        ]

    return {
        "valid": len(missing_required) == 0,
        "actual_columns": actual_columns,
        "missing_required_columns": missing_required,
        "missing_recommended_columns": missing_recommended,
    }


# ============================================================
# Date Validation
# ============================================================

def validate_dates(
    dataframe: pd.DataFrame,
    date_column: str = "date",
) -> dict[str, Any]:
    """
    Validate the date column and calculate the dataset period.
    """

    if date_column not in dataframe.columns:
        return {
            "valid": False,
            "invalid_date_count": None,
            "start_date": None,
            "end_date": None,
            "historical_days": None,
        }

    converted_dates = pd.to_datetime(
        dataframe[date_column],
        errors="coerce",
    )

    invalid_date_count = int(converted_dates.isna().sum())

    if invalid_date_count > 0:
        return {
            "valid": False,
            "invalid_date_count": invalid_date_count,
            "start_date": None,
            "end_date": None,
            "historical_days": None,
        }

    start_date = converted_dates.min()
    end_date = converted_dates.max()

    historical_days = int((end_date - start_date).days) + 1

    return {
        "valid": True,
        "invalid_date_count": 0,
        "start_date": start_date.strftime("%Y-%m-%d"),
        "end_date": end_date.strftime("%Y-%m-%d"),
        "historical_days": historical_days,
    }


# ============================================================
# Missing Value Validation
# ============================================================

def validate_missing_values(
    dataframe: pd.DataFrame,
) -> dict[str, Any]:
    """
    Detect missing values in the dataset.
    """

    missing_by_column = dataframe.isna().sum()

    missing_by_column = {
        column: int(count)
        for column, count in missing_by_column.items()
        if count > 0
    }

    total_missing = int(dataframe.isna().sum().sum())

    return {
        "valid": total_missing == 0,
        "total_missing_values": total_missing,
        "missing_by_column": missing_by_column,
    }


# ============================================================
# Duplicate Validation
# ============================================================

def validate_duplicates(
    dataframe: pd.DataFrame,
    subset: list[str] | None = None,
) -> dict[str, Any]:
    """
    Detect duplicate rows.

    If subset is provided, duplicates are detected using only
    the specified columns.

    For disease_data, the uniqueness rule is:
        date + disease
    """

    if subset:
        missing_subset_columns = [
            column
            for column in subset
            if column not in dataframe.columns
        ]

        if missing_subset_columns:
            return {
                "valid": False,
                "duplicate_rows": 0,
                "subset": subset,
                "error": (
                    "Duplicate validation columns are missing: "
                    + ", ".join(missing_subset_columns)
                ),
            }

        duplicate_count = int(
            dataframe.duplicated(subset=subset).sum()
        )

        return {
            "valid": duplicate_count == 0,
            "duplicate_rows": duplicate_count,
            "subset": subset,
        }

    duplicate_count = int(dataframe.duplicated().sum())

    return {
        "valid": duplicate_count == 0,
        "duplicate_rows": duplicate_count,
    }


# ============================================================
# Numeric Validation
# ============================================================

def validate_numeric_columns(
    dataframe: pd.DataFrame,
    numeric_columns: list[str],
) -> dict[str, Any]:
    """
    Validate numeric fields.

    Missing optional numeric columns are ignored.
    Existing numeric columns are checked for:
    - non-numeric values
    - negative values
    """

    invalid_numeric_values = {}
    negative_values = {}

    for column in numeric_columns:

        if column not in dataframe.columns:
            continue

        converted = pd.to_numeric(
            dataframe[column],
            errors="coerce",
        )

        original_non_null = dataframe[column].notna()

        invalid_count = int(
            (converted.isna() & original_non_null).sum()
        )

        if invalid_count > 0:
            invalid_numeric_values[column] = invalid_count

        negative_count = int(
            (converted < 0).sum()
        )

        if negative_count > 0:
            negative_values[column] = negative_count

    valid = (
        len(invalid_numeric_values) == 0
        and len(negative_values) == 0
    )

    return {
        "valid": valid,
        "invalid_numeric_values": invalid_numeric_values,
        "negative_values": negative_values,
    }


# ============================================================
# Disease-Specific Validation
# ============================================================

def validate_disease_values(
    dataframe: pd.DataFrame,
) -> dict[str, Any]:
    """
    Validate disease-specific fields.

    Rules:
    - disease must not be empty or whitespace-only
    - cases must be numeric
    - cases must be non-negative

    Numeric validation for cases is also performed by
    validate_numeric_columns(). This function additionally
    handles empty disease names.
    """

    empty_disease_count = 0

    if "disease" in dataframe.columns:
        disease_values = dataframe["disease"]

        empty_disease_count = int(
            disease_values.isna().sum()
            + disease_values.astype("string").str.strip().eq("").sum()
        )

    result = {
        "valid": empty_disease_count == 0,
        "empty_disease_count": empty_disease_count,
    }

    return result


# ============================================================
# Main Dataset Validation
# ============================================================

def validate_dataset(
    file_path: str | Path,
    dataset_type: str,
) -> dict[str, Any]:
    """
    Main CareFlow dataset validation function.

    dataset_type:
        - hospital_history
        - hospital_resources
        - disease_data
    """

    file_path = Path(file_path)

    result: dict[str, Any] = {
        "file": str(file_path),
        "dataset_type": dataset_type,
        "valid": False,
        "row_count": 0,
        "errors": [],
        "warnings": [],
    }

    # --------------------------------------------------------
    # Check file existence
    # --------------------------------------------------------

    if not file_path.exists():
        result["errors"].append(
            f"File does not exist: {file_path}"
        )
        return result

    # --------------------------------------------------------
    # Read CSV
    # --------------------------------------------------------

    try:
        dataframe = pd.read_csv(file_path)
    except Exception as exc:
        result["errors"].append(
            f"Unable to read CSV: {exc}"
        )
        return result

    result["row_count"] = len(dataframe)

    # --------------------------------------------------------
    # Empty dataset
    # --------------------------------------------------------

    if dataframe.empty:
        result["errors"].append(
            "Dataset is empty."
        )
        return result

    # --------------------------------------------------------
    # Dataset-specific configuration
    # --------------------------------------------------------

    if dataset_type == "hospital_history":

        required_columns = HISTORY_REQUIRED_COLUMNS
        recommended_columns = HISTORY_RECOMMENDED_COLUMNS
        numeric_columns = HISTORY_NUMERIC_COLUMNS
        duplicate_subset = None

    elif dataset_type == "hospital_resources":

        required_columns = RESOURCE_REQUIRED_COLUMNS
        recommended_columns = []
        numeric_columns = RESOURCE_NUMERIC_COLUMNS
        duplicate_subset = None

    elif dataset_type == "disease_data":

        required_columns = DISEASE_REQUIRED_COLUMNS
        recommended_columns = []
        numeric_columns = DISEASE_NUMERIC_COLUMNS
        duplicate_subset = ["date", "disease"]

    else:

        result["errors"].append(
            f"Unknown dataset type: {dataset_type}"
        )
        return result

    # --------------------------------------------------------
    # Column validation
    # --------------------------------------------------------

    column_result = validate_columns(
        dataframe,
        required_columns,
        recommended_columns,
    )

    result["columns"] = column_result

    if not column_result["valid"]:
        result["errors"].append(
            "Required columns are missing."
        )

    if column_result["missing_recommended_columns"]:
        result["warnings"].append(
            "Recommended columns are missing: "
            + ", ".join(
                column_result["missing_recommended_columns"]
            )
        )

    # --------------------------------------------------------
    # Stop date-dependent validation if date column missing
    # --------------------------------------------------------

    if "date" not in dataframe.columns:
        result["errors"].append(
            "Required 'date' column is missing."
        )
        return result

    # --------------------------------------------------------
    # Missing values
    # --------------------------------------------------------

    missing_result = validate_missing_values(
        dataframe
    )

    result["missing_values"] = missing_result

    if not missing_result["valid"]:
        result["errors"].append(
            "Dataset contains missing values."
        )

    # --------------------------------------------------------
    # Disease-specific validation
    # --------------------------------------------------------

    if dataset_type == "disease_data":

        disease_result = validate_disease_values(
            dataframe
        )

        result["disease_validation"] = disease_result

        if not disease_result["valid"]:
            result["errors"].append(
                "Disease column contains empty disease names."
            )

    # --------------------------------------------------------
    # Duplicate rows
    # --------------------------------------------------------

    duplicate_result = validate_duplicates(
        dataframe,
        subset=duplicate_subset,
    )

    result["duplicates"] = duplicate_result

    if not duplicate_result["valid"]:
        if dataset_type == "disease_data":
            result["errors"].append(
                "Dataset contains duplicate date+disease observations."
            )
        else:
            result["errors"].append(
                "Dataset contains duplicate rows."
            )

    # --------------------------------------------------------
    # Date validation
    # --------------------------------------------------------

    date_result = validate_dates(
        dataframe
    )

    result["date_validation"] = date_result

    if not date_result["valid"]:
        result["errors"].append(
            "Dataset contains invalid dates."
        )

    # --------------------------------------------------------
    # Numeric validation
    # --------------------------------------------------------

    numeric_result = validate_numeric_columns(
        dataframe,
        numeric_columns,
    )

    result["numeric_validation"] = numeric_result

    if not numeric_result["valid"]:
        result["errors"].append(
            "Dataset contains invalid or negative numeric values."
        )

    # --------------------------------------------------------
    # Historical period disclaimer
    # --------------------------------------------------------

    if date_result["valid"]:

        historical_days = date_result["historical_days"]

        result["historical_period"] = {
            "start_date": date_result["start_date"],
            "end_date": date_result["end_date"],
            "days": historical_days,
            "disclaimer": generate_period_disclaimer(
                historical_days
            ),
        }

    # --------------------------------------------------------
    # Final validation status
    # --------------------------------------------------------

    result["valid"] = len(result["errors"]) == 0

    return result


# ============================================================
# Direct Validation Test
# ============================================================

if __name__ == "__main__":

    project_root = Path(__file__).resolve().parents[2]

    history_file = (
        project_root
        / "datasets"
        / "sample_hospital_history.csv"
    )

    resources_file = (
        project_root
        / "datasets"
        / "sample_hospital_resources.csv"
    )

    disease_file = (
        project_root
        / "datasets"
        / "sample_hospital_disease.csv"
    )

    history_result = validate_dataset(
        history_file,
        "hospital_history",
    )

    resources_result = validate_dataset(
        resources_file,
        "hospital_resources",
    )

    print("\n" + "=" * 70)
    print("CAREFLOW DATASET VALIDATION")
    print("=" * 70)

    print("\nHOSPITAL HISTORY")
    print("-" * 70)
    print(history_result)

    print("\nHOSPITAL RESOURCES")
    print("-" * 70)
    print(resources_result)

    if disease_file.exists():
        disease_result = validate_dataset(
            disease_file,
            "disease_data",
        )

        print("\nDISEASE DATA")
        print("-" * 70)
        print(disease_result)


# ============================================================
# CareFlow Phase 12 - Upload Security Helpers
# ============================================================

MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB
MAX_ROWS = 100_000


class DatasetValidationError(ValueError):
    """Raised when an uploaded dataset fails validation."""


def validate_filename(filename: str) -> str:
    """
    Validate an uploaded dataset filename.

    Only CSV files are allowed.
    Directory paths are not allowed.
    """

    if not filename:
        raise DatasetValidationError(
            "Filename is required."
        )

    safe_name = Path(filename).name

    if safe_name != filename:
        raise DatasetValidationError(
            "Invalid filename. Directory paths are not allowed."
        )

    if not safe_name.lower().endswith(".csv"):
        raise DatasetValidationError(
            "Only CSV files are allowed."
        )

    if len(safe_name) > 255:
        raise DatasetValidationError(
            "Filename is too long."
        )

    return safe_name


def validate_file_size(file_size: int) -> None:
    """
    Validate uploaded file size.

    Maximum allowed size: 10 MB.
    """

    if file_size <= 0:
        raise DatasetValidationError(
            "Uploaded file is empty."
        )

    if file_size > MAX_FILE_SIZE_BYTES:
        raise DatasetValidationError(
            "Uploaded file exceeds the 10 MB size limit."
        )


def validate_row_count_limit(row_count: int) -> None:
    """
    Validate maximum number of uploaded data rows.

    Maximum allowed rows: 100,000.
    """

    if row_count <= 0:
        raise DatasetValidationError(
            "Uploaded CSV contains no data rows."
        )

    if row_count > MAX_ROWS:
        raise DatasetValidationError(
            f"Uploaded CSV exceeds the maximum of {MAX_ROWS} rows."
        )