from pathlib import Path

import pandas as pd


RAW_FILE = Path("ml/data/raw/idsp/india_dengue_2018_2019.csv")
OUTPUT_FILE = Path("ml/data/processed/india_dengue_monthly.csv")


def main():
    # Load raw dataset
    df = pd.read_csv(RAW_FILE)

    # Select only monthly columns.
    # Exclude yearly Total columns.
    month_columns = [
        column
        for column in df.columns
        if (
            column.startswith("2018 - ")
            or column.startswith("2019 - ")
        )
        and not column.endswith(" - Total")
    ]

    records = []

    # Convert wide format into:
    # state | date | dengue_cases
    for _, row in df.iterrows():
        state = str(row["State/UT"]).strip()

        for column in month_columns:
            year, month = column.split(" - ")

            date = pd.to_datetime(
                f"{year}-{month}-01",
                format="%Y-%B-%d"
            )

            records.append(
                {
                    "state": state,
                    "date": date,
                    "dengue_cases": row[column],
                }
            )

    clean_df = pd.DataFrame(records)

    # Remove the India-wide aggregate row.
    # It is not an individual state/UT.
    clean_df = clean_df[
        clean_df["state"] != "Total"
    ].copy()

    # Convert reported case values to numeric.
    # "Not Reported" becomes NaN.
    # It must NOT be treated as zero.
    clean_df["dengue_cases"] = pd.to_numeric(
        clean_df["dengue_cases"],
        errors="coerce"
    )

    # Count unreported values.
    not_reported_count = clean_df["dengue_cases"].isna().sum()

    print(
        "Unreported monthly values:",
        not_reported_count
    )

    # Sort chronologically within each state.
    clean_df = clean_df.sort_values(
        ["state", "date"]
    ).reset_index(drop=True)

    # Create output directory if necessary.
    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    # Save processed dataset.
    clean_df.to_csv(
        OUTPUT_FILE,
        index=False
    )

    # Verification output.
    print("Created:", OUTPUT_FILE)
    print("Rows:", len(clean_df))
    print(
        "Columns:",
        clean_df.columns.tolist()
    )
    print(
        "States:",
        clean_df["state"].nunique()
    )
    print(
        "Date range:",
        clean_df["date"].min().date(),
        "to",
        clean_df["date"].max().date()
    )
    print(
        "Missing values:",
        clean_df.isna().sum().sum()
    )
    print(
        "Negative cases:",
        (clean_df["dengue_cases"] < 0).sum()
    )


if __name__ == "__main__":
    main()