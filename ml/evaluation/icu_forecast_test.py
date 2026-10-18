import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error
from xgboost import XGBRegressor


DATA_PATH = "ml/data/hospital_features.csv"

TARGET = "icu_demand"

FORECAST_FEATURES = [
    "day_of_week",
    "day_of_month",
    "month",
    "week_of_year",
    "icu_demand_lag_1",
    "icu_demand_lag_7",
    "icu_demand_lag_14",
    "icu_demand_lag_30",
    "icu_demand_rolling_mean_7",
    "icu_demand_rolling_mean_14",
    "icu_demand_rolling_mean_30",
]

HORIZONS = [7, 14, 30]

# Validation forecast origin.
# The final Phase 9 test period remains untouched.
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


def build_features(history, forecast_date):
    history = pd.Series(history, dtype=float)

    features = {
        "day_of_week": forecast_date.dayofweek,
        "day_of_month": forecast_date.day,
        "month": forecast_date.month,
        "week_of_year": forecast_date.isocalendar().week,
        "icu_demand_lag_1": history.iloc[-1],
        "icu_demand_lag_7": history.iloc[-7],
        "icu_demand_lag_14": history.iloc[-14],
        "icu_demand_lag_30": history.iloc[-30],
        "icu_demand_rolling_mean_7": history.iloc[-7:].mean(),
        "icu_demand_rolling_mean_14": history.iloc[-14:].mean(),
        "icu_demand_rolling_mean_30": history.iloc[-30:].mean(),
    }

    return pd.DataFrame(
        [features],
        columns=FORECAST_FEATURES,
    )


def main():
    df = pd.read_csv(DATA_PATH)

    df["date"] = pd.to_datetime(df["date"])

    df = (
        df.sort_values("date")
        .reset_index(drop=True)
    )

    # Remove initial rows that do not have enough historical data
    # to calculate the required lag and rolling features.
    df = df.dropna(
        subset=FORECAST_FEATURES + [TARGET]
    ).copy()

    cutoff = pd.Timestamp(CUTOFF_DATE)

    required_columns = (
        FORECAST_FEATURES + [TARGET, "date"]
    )

    missing_columns = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            "ICU forecast dataset is missing "
            f"required columns: {missing_columns}"
        )

    train = df[df["date"] <= cutoff].copy()
    future = df[df["date"] > cutoff].copy()

    if train.empty:
        raise ValueError(
            "ICU forecast training data is empty "
            f"for cutoff {cutoff.date()}."
        )

    if len(train) < 30:
        raise ValueError(
            "ICU forecast has insufficient training data. "
            f"Required at least 30 rows, found {len(train)}."
        )

    if future.empty:
        raise ValueError(
            "ICU forecast has no future rows after "
            f"cutoff {cutoff.date()}."
        )

    required_forecast_rows = max(HORIZONS)

    if len(future) < required_forecast_rows:
        raise ValueError(
            "ICU forecast does not have enough future rows "
            f"for the {required_forecast_rows}-day evaluation. "
            f"Found {len(future)} rows."
        )

    print("ICU Multi-Step Forecast Test")
    print("============================")
    print(f"Training end: {cutoff.date()}")
    print(
        f"Forecast start: "
        f"{future['date'].iloc[0].date()}"
    )
    print(
        f"Available future rows: "
        f"{len(future)}"
    )

    model = XGBRegressor(
        objective="reg:squarederror",
        n_estimators=300,
        max_depth=4,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
    )

    model.fit(
        train[FORECAST_FEATURES],
        train[TARGET],
    )

    # Only observations available at the forecast origin.
    history = train[TARGET].tolist()

    predictions = []

    for _, row in future.iterrows():

        feature_row = build_features(
            history,
            row["date"],
        )

        prediction = float(
            model.predict(feature_row)[0]
        )

        predictions.append(prediction)

        # Recursive forecasting:
        # use the model's prediction as the next historical value.
        # Future actual ICU demand is never added to history.
        history.append(prediction)

    future = future.copy()

    future["prediction"] = predictions

    # ---------------------------------------------------------
    # Forecast metrics
    # ---------------------------------------------------------

    print("\nForecast Results")
    print("----------------")

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

    # ---------------------------------------------------------
    # Forecast points
    # ---------------------------------------------------------

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

    # ---------------------------------------------------------
    # 30-day error analysis
    # ---------------------------------------------------------

    future["absolute_error"] = np.abs(
        future[TARGET] - future["prediction"]
    )

    future["signed_error"] = (
        future["prediction"] - future[TARGET]
    )

    analysis = future.iloc[:30].copy()

    print("\n30-Day Error Analysis")
    print("---------------------")

    print("\nLargest Absolute Errors")
    print("-----------------------")

    largest_errors = (
        analysis.nlargest(
            10,
            "absolute_error",
        )[
            [
                "date",
                TARGET,
                "prediction",
                "absolute_error",
                "signed_error",
            ]
        ]
    )

    print(
        largest_errors.to_string(
            index=False
        )
    )

    print("\nError Summary")
    print("-------------")

    print(
        f"Mean Absolute Error: "
        f"{analysis['absolute_error'].mean():.4f}"
    )

    print(
        f"Mean Signed Error: "
        f"{analysis['signed_error'].mean():.4f}"
    )

    print(
        f"Underpredictions: "
        f"{(analysis['signed_error'] < 0).sum()}"
    )

    print(
        f"Overpredictions: "
        f"{(analysis['signed_error'] > 0).sum()}"
    )


if __name__ == "__main__":
    main()