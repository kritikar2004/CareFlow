import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error


DATA_PATH = "ml/data/resource_features.csv"

RESOURCE_NAME = "IV Fluid"

TARGET = "quantity_used"

HORIZONS = [7, 14, 30]

# Same validation forecast origin used by the
# General Bed XGBoost forecast test.
CUTOFF_DATE = "2026-05-18"


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


def main():
    df = pd.read_csv(DATA_PATH)

    df["date"] = pd.to_datetime(df["date"])

    df = df[
        df["resource_name"] == RESOURCE_NAME
    ].copy()

    df = (
        df.sort_values("date")
        .reset_index(drop=True)
    )

    cutoff = pd.Timestamp(CUTOFF_DATE)

    train = df[df["date"] <= cutoff].copy()
    future = df[df["date"] > cutoff].copy()

    print("Resource Multi-Step Naive Baseline Test")
    print("========================================")
    print(f"Resource: {RESOURCE_NAME}")
    print(f"Training end: {cutoff.date()}")
    print(
        f"Forecast start: "
        f"{future['date'].iloc[0].date()}"
    )
    print(
        f"Available future rows: "
        f"{len(future)}"
    )

    # Naive forecast:
    # every future prediction equals the last
    # observed quantity_used at the cutoff.
    last_observed = float(
        train[TARGET].iloc[-1]
    )

    predictions = [
        last_observed
        for _ in range(len(future))
    ]

    future = future.copy()
    future["prediction"] = predictions

    print("\nBaseline Forecast Results")
    print("-------------------------")

    for horizon in HORIZONS:

        horizon_data = future.iloc[:horizon]

        actual = horizon_data[TARGET].to_numpy()
        predicted = horizon_data["prediction"].to_numpy()

        mae, rmse, mape = calculate_metrics(
            actual,
            predicted,
        )

        print(
            f"{horizon}-day: "
            f"MAE={mae:.4f}, "
            f"RMSE={rmse:.4f}, "
            f"MAPE={mape:.4f}%"
        )

    print("\nForecast Points")
    print("---------------")
    print(
        f"7-day:  "
        f"{min(7, len(future))}"
    )
    print(
        f"14-day: "
        f"{min(14, len(future))}"
    )
    print(
        f"30-day: "
        f"{min(30, len(future))}"
    )


if __name__ == "__main__":
    main()