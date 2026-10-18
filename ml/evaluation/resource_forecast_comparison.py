import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error
from xgboost import XGBRegressor


DATA_PATH = "ml/data/resource_features.csv"

TARGET = "quantity_used"

HORIZONS = [7, 14, 30]

CUTOFF_DATE = "2026-05-18"

FORECAST_FEATURES = [
    "day_of_week",
    "day_of_month",
    "month",
    "week_of_year",
    "quantity_used_lag_1",
    "quantity_used_lag_7",
    "quantity_used_lag_14",
    "quantity_used_lag_30",
    "quantity_used_rolling_mean_7",
    "quantity_used_rolling_mean_14",
    "quantity_used_rolling_mean_30",
]


def calculate_metrics(actual, predicted):
    mae = mean_absolute_error(actual, predicted)

    rmse = np.sqrt(
        mean_squared_error(actual, predicted)
    )

    non_zero = actual != 0

    if non_zero.sum() > 0:
        mape = (
            np.mean(
                np.abs(
                    (
                        actual[non_zero]
                        - predicted[non_zero]
                    )
                    / actual[non_zero]
                )
            )
            * 100
        )
    else:
        mape = np.nan

    return mae, rmse, mape


def build_features(history, forecast_date):
    history = pd.Series(
        history,
        dtype=float
    )

    features = {
        "day_of_week": forecast_date.dayofweek,
        "day_of_month": forecast_date.day,
        "month": forecast_date.month,
        "week_of_year": forecast_date.isocalendar().week,
        "quantity_used_lag_1": history.iloc[-1],
        "quantity_used_lag_7": history.iloc[-7],
        "quantity_used_lag_14": history.iloc[-14],
        "quantity_used_lag_30": history.iloc[-30],
        "quantity_used_rolling_mean_7": history.iloc[-7:].mean(),
        "quantity_used_rolling_mean_14": history.iloc[-14:].mean(),
        "quantity_used_rolling_mean_30": history.iloc[-30:].mean(),
    }

    return pd.DataFrame(
        [features],
        columns=FORECAST_FEATURES,
    )


def run_xgboost_forecast(train, future):
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

        # Recursive forecasting.
        # Future actual values are never added.
        history.append(prediction)

    return np.array(predictions)


def run_naive_forecast(train, future):
    last_observed = float(
        train[TARGET].iloc[-1]
    )

    return np.full(
        len(future),
        last_observed,
        dtype=float,
    )


def compare_metrics(
    xgb_metrics,
    naive_metrics,
):
    xgb_mae, xgb_rmse, xgb_mape = xgb_metrics
    naive_mae, naive_rmse, naive_mape = naive_metrics

    mae_better = xgb_mae < naive_mae
    rmse_better = xgb_rmse < naive_rmse
    mape_better = xgb_mape < naive_mape

    better_count = sum(
        [
            mae_better,
            rmse_better,
            mape_better,
        ]
    )

    if better_count == 3:
        return "XGBoost better"

    if better_count == 0:
        return "Naive better"

    return "Mixed"


def main():

    df = pd.read_csv(DATA_PATH)

    df["date"] = pd.to_datetime(df["date"])

    cutoff = pd.Timestamp(CUTOFF_DATE)

    resources = sorted(
        df["resource_name"]
        .dropna()
        .unique()
    )

    print("Resource Forecast Comparison")
    print("=============================")
    print(f"Training end: {cutoff.date()}")
    print(
        "Forecast evaluation: "
        "validation period"
    )
    print(
        "Final Phase 9 test period remains untouched."
    )

    print("\nResources detected:")
    for resource in resources:
        print(f"- {resource}")

    results = []

    for resource_name in resources:

        print(
            f"\n{'=' * 65}"
        )

        print(
            f"Testing Resource: "
            f"{resource_name}"
        )

        print(
            f"{'=' * 65}"
        )

        resource_df = df[
            df["resource_name"]
            == resource_name
        ].copy()

        resource_df = (
            resource_df
            .sort_values("date")
            .reset_index(drop=True)
        )

        resource_df = resource_df.dropna(
            subset=FORECAST_FEATURES + [TARGET]
        ).copy()

        train = resource_df[
            resource_df["date"] <= cutoff
        ].copy()

        future = resource_df[
            resource_df["date"] > cutoff
        ].copy()

        if len(train) < 30:
            print(
                "Skipping: insufficient training history."
            )
            continue

        if len(future) < 30:
            print(
                "Skipping: insufficient validation horizon."
            )
            continue

        xgb_predictions = run_xgboost_forecast(
            train,
            future,
        )

        naive_predictions = run_naive_forecast(
            train,
            future,
        )

        for horizon in HORIZONS:

            horizon_actual = (
                future[TARGET]
                .iloc[:horizon]
                .to_numpy()
            )

            xgb_pred = (
                xgb_predictions[:horizon]
            )

            naive_pred = (
                naive_predictions[:horizon]
            )

            xgb_metrics = calculate_metrics(
                horizon_actual,
                xgb_pred,
            )

            naive_metrics = calculate_metrics(
                horizon_actual,
                naive_pred,
            )

            result = compare_metrics(
                xgb_metrics,
                naive_metrics,
            )

            results.append(
                {
                    "resource": resource_name,
                    "horizon": horizon,

                    "xgb_mae": xgb_metrics[0],
                    "xgb_rmse": xgb_metrics[1],
                    "xgb_mape": xgb_metrics[2],

                    "naive_mae": naive_metrics[0],
                    "naive_rmse": naive_metrics[1],
                    "naive_mape": naive_metrics[2],

                    "result": result,
                }
            )

            print(
                f"\n{horizon}-day"
            )

            print(
                f"XGBoost: "
                f"MAE={xgb_metrics[0]:.4f}, "
                f"RMSE={xgb_metrics[1]:.4f}, "
                f"MAPE={xgb_metrics[2]:.4f}%"
            )

            print(
                f"Naive:   "
                f"MAE={naive_metrics[0]:.4f}, "
                f"RMSE={naive_metrics[1]:.4f}, "
                f"MAPE={naive_metrics[2]:.4f}%"
            )

            print(
                f"Result: {result}"
            )

    results_df = pd.DataFrame(results)

    print(
        f"\n{'=' * 100}"
    )

    print(
        "FINAL RESOURCE FORECAST COMPARISON"
    )

    print(
        f"{'=' * 100}"
    )

    if results_df.empty:
        print(
            "No resource results generated."
        )
        return

    display_columns = [
        "resource",
        "horizon",
        "xgb_mae",
        "naive_mae",
        "xgb_rmse",
        "naive_rmse",
        "xgb_mape",
        "naive_mape",
        "result",
    ]

    print(
        results_df[
            display_columns
        ].to_string(index=False)
    )

    print(
        f"\n{'=' * 100}"
    )

    print(
        "RESOURCE SUMMARY"
    )

    print(
        f"{'=' * 100}"
    )

    for resource in resources:

        resource_results = results_df[
            results_df["resource"]
            == resource
        ]

        if resource_results.empty:
            continue

        xgb_wins = (
            resource_results["result"]
            == "XGBoost better"
        ).sum()

        naive_wins = (
            resource_results["result"]
            == "Naive better"
        ).sum()

        mixed = (
            resource_results["result"]
            == "Mixed"
        ).sum()

        print(
            f"\n{resource}"
        )

        print(
            f"XGBoost better: "
            f"{xgb_wins}/3 horizons"
        )

        print(
            f"Naive better: "
            f"{naive_wins}/3 horizons"
        )

        print(
            f"Mixed: "
            f"{mixed}/3 horizons"
        )


if __name__ == "__main__":
    main()