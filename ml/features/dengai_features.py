from pathlib import Path

import pandas as pd


INPUT_FILE = Path("ml/data/processed/dengai_train.csv")
OUTPUT_FILE = Path("ml/data/processed/dengai_features.csv")


def main():
    df = pd.read_csv(INPUT_FILE)

    df["week_start_date"] = pd.to_datetime(
        df["week_start_date"]
    )

    df = df.sort_values(
        ["city", "week_start_date"]
    ).reset_index(drop=True)

    # Historical dengue case features.
    # shift() ensures only past observations are used.
    for lag in [1, 2, 4, 8]:
        df[f"total_cases_lag_{lag}"] = (
            df.groupby("city")["total_cases"]
            .shift(lag)
        )

    # Leakage-safe rolling averages.
    shifted_cases = (
        df.groupby("city")["total_cases"]
        .shift(1)
    )

    df["total_cases_rolling_mean_4"] = (
        shifted_cases
        .groupby(df["city"])
        .transform(
            lambda x: x.rolling(4).mean()
        )
    )

    df["total_cases_rolling_mean_8"] = (
        shifted_cases
        .groupby(df["city"])
        .transform(
            lambda x: x.rolling(8).mean()
        )
    )

    # Calendar features
    df["month"] = df["week_start_date"].dt.month
    df["quarter"] = df["week_start_date"].dt.quarter

    # Verify chronological ordering within each city
    for city, group in df.groupby("city"):
        if not group["week_start_date"].is_monotonic_increasing:
            raise ValueError(
                f"Dates are not chronological for city: {city}"
            )

    # Save feature dataset
    df.to_csv(OUTPUT_FILE, index=False)

    print("DengAI feature engineering completed.")
    print(f"Output: {OUTPUT_FILE}")
    print(f"Rows: {len(df)}")
    print(f"Columns: {len(df.columns)}")
    print(f"Cities: {df['city'].unique().tolist()}")

    print("\nNew temporal features:")
    print(" - total_cases_lag_1")
    print(" - total_cases_lag_2")
    print(" - total_cases_lag_4")
    print(" - total_cases_lag_8")
    print(" - total_cases_rolling_mean_4")
    print(" - total_cases_rolling_mean_8")
    print(" - month")
    print(" - quarter")

    print("\nMissing values created by historical features:")
    print(
        int(
            df[
                [
                    "total_cases_lag_1",
                    "total_cases_lag_2",
                    "total_cases_lag_4",
                    "total_cases_lag_8",
                    "total_cases_rolling_mean_4",
                    "total_cases_rolling_mean_8",
                ]
            ]
            .isna()
            .sum()
            .sum()
        )
    )


if __name__ == "__main__":
    main()