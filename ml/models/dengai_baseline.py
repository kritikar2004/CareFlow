from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error


SPLIT_DIR = Path("ml/data/processed/dengai_split")


def calculate_metrics(actual, predicted):
    mae = mean_absolute_error(actual, predicted)
    rmse = np.sqrt(mean_squared_error(actual, predicted))

    non_zero = actual != 0

    if non_zero.sum() > 0:
        mape = (
            np.mean(
                np.abs(
                    (actual[non_zero] - predicted[non_zero])
                    / actual[non_zero]
                )
            )
            * 100
        )
    else:
        mape = np.nan

    return mae, rmse, mape


def evaluate(df, name):
    actual = df["total_cases"].to_numpy()
    predicted = df["total_cases_lag_1"].to_numpy()

    mae, rmse, mape = calculate_metrics(
        actual,
        predicted
    )

    print(f"\n{name}")
    print(f"Rows: {len(df)}")
    print(f"MAE: {mae:.4f}")
    print(f"RMSE: {rmse:.4f}")
    print(f"MAPE: {mape:.4f}%")


def main():
    validation = pd.read_csv(
        SPLIT_DIR / "validation.csv"
    )

    evaluate(validation, "Combined Validation")

    for city in sorted(validation["city"].unique()):
        city_data = validation[
            validation["city"] == city
        ]

        evaluate(
            city_data,
            f"Validation - {city}"
        )


if __name__ == "__main__":
    main()