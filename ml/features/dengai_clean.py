from pathlib import Path

import pandas as pd


RAW_DIR = Path("ml/data/raw/dengai")
PROCESSED_DIR = Path("ml/data/processed")

FEATURES_FILE = RAW_DIR / "dengue_features_train.csv"
LABELS_FILE = RAW_DIR / "dengue_labels_train.csv"

OUTPUT_FILE = PROCESSED_DIR / "dengai_train.csv"


def main():
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    features = pd.read_csv(FEATURES_FILE)
    labels = pd.read_csv(LABELS_FILE)

    # Convert date column
    features["week_start_date"] = pd.to_datetime(
        features["week_start_date"]
    )

    # Merge features with dengue target
    df = features.merge(
        labels,
        on=["city", "year", "weekofyear"],
        how="inner",
        validate="one_to_one",
    )

    # Sort separately by city and date
    df = df.sort_values(
        ["city", "week_start_date"]
    ).reset_index(drop=True)

    # Environmental columns only
    exclude_columns = {
        "city",
        "year",
        "weekofyear",
        "week_start_date",
        "total_cases",
    }

    feature_columns = [
        col for col in df.columns
        if col not in exclude_columns
    ]

    missing_before = int(df[feature_columns].isna().sum().sum())

    # Time interpolation within each city
    df[feature_columns] = (
        df.groupby("city", group_keys=False)[feature_columns]
        .apply(
            lambda group: group.interpolate(
                method="linear",
                limit_direction="both"
            )
        )
        .reset_index(drop=True)
    )

    missing_after = int(df[feature_columns].isna().sum().sum())

    # Safety check
    if missing_after > 0:
        raise ValueError(
            f"Missing feature values remain after cleaning: "
            f"{missing_after}"
        )

    # Target must remain unchanged and valid
    if df["total_cases"].isna().any():
        raise ValueError("Missing total_cases values detected.")

    if (df["total_cases"] < 0).any():
        raise ValueError("Negative total_cases values detected.")

    # Final ordering
    df = df.sort_values(
        ["city", "week_start_date"]
    ).reset_index(drop=True)

    # Save processed dataset
    df.to_csv(OUTPUT_FILE, index=False)

    print("DengAI cleaning completed.")
    print(f"Output: {OUTPUT_FILE}")
    print(f"Rows: {len(df)}")
    print(f"Columns: {len(df.columns)}")
    print(f"Missing feature values before: {missing_before}")
    print(f"Missing feature values after: {missing_after}")
    print(
        f"Date range: "
        f"{df['week_start_date'].min().date()} "
        f"to "
        f"{df['week_start_date'].max().date()}"
    )
    print(f"Cities: {df['city'].unique().tolist()}")
    print(
        f"Total dengue cases: "
        f"{df['total_cases'].min()} to "
        f"{df['total_cases'].max()}"
    )


if __name__ == "__main__":
    main()