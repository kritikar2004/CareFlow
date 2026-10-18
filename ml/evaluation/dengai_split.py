from pathlib import Path

import pandas as pd


INPUT_FILE = Path("ml/data/processed/dengai_ml_ready.csv")
OUTPUT_DIR = Path("ml/data/processed/dengai_split")


def split_city_data(group):
    group = group.sort_values("week_start_date").reset_index(drop=True)

    n = len(group)

    train_end = int(n * 0.70)
    validation_end = int(n * 0.85)

    train = group.iloc[:train_end].copy()
    validation = group.iloc[train_end:validation_end].copy()
    test = group.iloc[validation_end:].copy()

    return train, validation, test


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(INPUT_FILE)
    df["week_start_date"] = pd.to_datetime(df["week_start_date"])

    train_parts = []
    validation_parts = []
    test_parts = []

    for city, group in df.groupby("city"):
        train, validation, test = split_city_data(group)

        train_parts.append(train)
        validation_parts.append(validation)
        test_parts.append(test)

        print(f"\nCity: {city}")
        print(f"Total rows: {len(group)}")
        print(
            f"Train: {len(train)} | "
            f"{train['week_start_date'].min().date()} "
            f"to {train['week_start_date'].max().date()}"
        )
        print(
            f"Validation: {len(validation)} | "
            f"{validation['week_start_date'].min().date()} "
            f"to {validation['week_start_date'].max().date()}"
        )
        print(
            f"Test: {len(test)} | "
            f"{test['week_start_date'].min().date()} "
            f"to {test['week_start_date'].max().date()}"
        )

    train_df = pd.concat(train_parts, ignore_index=True)
    validation_df = pd.concat(validation_parts, ignore_index=True)
    test_df = pd.concat(test_parts, ignore_index=True)

    train_df.to_csv(OUTPUT_DIR / "train.csv", index=False)
    validation_df.to_csv(OUTPUT_DIR / "validation.csv", index=False)
    test_df.to_csv(OUTPUT_DIR / "test.csv", index=False)

    print("\nSplit completed.")
    print(f"Train rows: {len(train_df)}")
    print(f"Validation rows: {len(validation_df)}")
    print(f"Test rows: {len(test_df)}")


if __name__ == "__main__":
    main()