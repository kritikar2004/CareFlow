"""
CareFlow Phase 10
DengAI SARIMA vs Naive Forecast Comparison

Purpose:
- Test one controlled statistical alternative after recursive XGBoost
  showed multi-week weaknesses.
- Use the same validation windows as the recursive DengAI forecast test.
- Test 1, 2, and 4 weekly horizons.
- Keep the final DengAI test split untouched.
- Compare SARIMA against the naive baseline.
"""

from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error
from statsmodels.tsa.statespace.sarimax import SARIMAX


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATA_PATH = (
    PROJECT_ROOT
    / "ml"
    / "data"
    / "processed"
    / "dengai_ml_ready.csv"
)


# ============================================================
# CONFIGURATION
# ============================================================

HORIZONS = {
    "1_week": 1,
    "2_weeks": 2,
    "4_weeks": 4,
}

CITY_CONFIG = {
    "iq": {
        "validation_end": "2009-01-01",
    },
    "sj": {
        "validation_end": "2005-08-13",
    },
}

# Controlled SARIMA specification.
# Weekly DengAI data -> seasonal period = 52 weeks.
SARIMA_ORDER = (1, 0, 0)
SARIMA_SEASONAL_ORDER = (1, 0, 0, 52)


# ============================================================
# METRICS
# ============================================================

def calculate_metrics(actual, predicted):
    actual = np.asarray(actual, dtype=float)
    predicted = np.asarray(predicted, dtype=float)

    mae = mean_absolute_error(actual, predicted)

    rmse = np.sqrt(
        mean_squared_error(actual, predicted)
    )

    non_zero = actual != 0

    if np.any(non_zero):
        mape = np.mean(
            np.abs(
                (actual[non_zero] - predicted[non_zero])
                / actual[non_zero]
            )
        ) * 100
    else:
        mape = np.nan

    return mae, rmse, mape


# ============================================================
# NAIVE FORECAST
# ============================================================

def naive_forecast(train_values, horizon):
    """
    Repeat the last observed value for the requested horizon.
    """

    last_value = float(train_values[-1])

    return np.repeat(last_value, horizon)


# ============================================================
# SARIMA FORECAST
# ============================================================

def sarima_forecast(train_values, horizon):
    """
    Fit the controlled SARIMA model and forecast recursively
    for the requested number of weekly observations.
    """

    model = SARIMAX(
        train_values,
        order=SARIMA_ORDER,
        seasonal_order=SARIMA_SEASONAL_ORDER,
        enforce_stationarity=False,
        enforce_invertibility=False,
    )

    fitted_model = model.fit(
        disp=False
    )

    forecast = fitted_model.forecast(
        steps=horizon
    )

    # Demand cannot be negative.
    forecast = np.maximum(
        np.asarray(forecast, dtype=float),
        0
    )

    return forecast


# ============================================================
# DATA LOADING
# ============================================================

print("=" * 80)
print("CARE FLOW - PHASE 10")
print("DengAI SARIMA vs Naive Forecast Comparison")
print("=" * 80)

print(f"\nLoading dataset:")
print(DATA_PATH)

df = pd.read_csv(DATA_PATH)

df["week_start_date"] = pd.to_datetime(
    df["week_start_date"]
)

df = df.sort_values(
    ["city", "week_start_date"]
).reset_index(drop=True)

print("\nDataset loaded:")
print(f"Rows: {len(df)}")
print(f"Cities: {df['city'].unique().tolist()}")


# ============================================================
# VALIDATION WINDOWS
# ============================================================

all_results = []
error_results = []


for city, config in CITY_CONFIG.items():

    print("\n")
    print("=" * 80)
    print(f"CITY: {city.upper()}")
    print("=" * 80)

    city_df = (
        df[df["city"] == city]
        .sort_values("week_start_date")
        .reset_index(drop=True)
    )

    validation_end = pd.Timestamp(
        config["validation_end"]
    )

    validation_rows = city_df[
        city_df["week_start_date"] <= validation_end
    ].copy()

    if validation_rows.empty:
        print("No validation rows found.")
        continue

    validation_dates = (
        validation_rows["week_start_date"]
        .tolist()
    )

    # Last four validation observations are used as the
    # common forecast evaluation window.
    forecast_dates = validation_dates[-4:]

    cutoff_date = forecast_dates[0] - pd.Timedelta(days=7)

    training_rows = city_df[
        city_df["week_start_date"] <= cutoff_date
    ].copy()

    train_values = (
        training_rows["total_cases"]
        .astype(float)
        .values
    )

    actual_values = (
        city_df[
            city_df["week_start_date"].isin(
                forecast_dates
            )
        ]
        .sort_values("week_start_date")["total_cases"]
        .astype(float)
        .values
    )

    print(f"\nTraining rows: {len(training_rows)}")
    print(
        f"Training period: "
        f"{training_rows['week_start_date'].min().date()} "
        f"-> "
        f"{training_rows['week_start_date'].max().date()}"
    )

    print(
        f"Validation forecast window: "
        f"{forecast_dates[0].date()} "
        f"-> "
        f"{forecast_dates[-1].date()}"
    )

    print(
        f"Forecast cutoff: "
        f"{cutoff_date.date()}"
    )

    print(
        f"Actual validation values: "
        f"{actual_values.tolist()}"
    )

    # --------------------------------------------------------
    # Forecast full 4-week validation window once.
    # --------------------------------------------------------

    print("\nFitting SARIMA...")

    try:
        sarima_full_forecast = sarima_forecast(
            train_values,
            4
        )

        print(
            "SARIMA forecast:",
            np.round(
                sarima_full_forecast,
                4
            ).tolist()
        )

    except Exception as exc:
        print("\nSARIMA fitting failed.")
        print(f"Error: {exc}")
        continue

    naive_full_forecast = naive_forecast(
        train_values,
        4
    )

    print(
        "Naive forecast:",
        naive_full_forecast.tolist()
    )

    # --------------------------------------------------------
    # Evaluate 1, 2 and 4 week horizons.
    # --------------------------------------------------------

    for horizon_name, horizon in HORIZONS.items():

        actual = actual_values[:horizon]

        sarima_pred = sarima_full_forecast[:horizon]

        naive_pred = naive_full_forecast[:horizon]

        sarima_mae, sarima_rmse, sarima_mape = (
            calculate_metrics(
                actual,
                sarima_pred
            )
        )

        naive_mae, naive_rmse, naive_mape = (
            calculate_metrics(
                actual,
                naive_pred
            )
        )

        print("\n" + "-" * 70)
        print(f"HORIZON: {horizon_name}")

        print("\nSARIMA")
        print(f"MAE : {sarima_mae:.4f}")
        print(f"RMSE: {sarima_rmse:.4f}")
        print(f"MAPE: {sarima_mape:.4f}%")

        print("\nNaive")
        print(f"MAE : {naive_mae:.4f}")
        print(f"RMSE: {naive_rmse:.4f}")
        print(f"MAPE: {naive_mape:.4f}%")

        all_results.append(
            {
                "city": city,
                "horizon": horizon_name,
                "sarima_mae": sarima_mae,
                "sarima_rmse": sarima_rmse,
                "sarima_mape": sarima_mape,
                "naive_mae": naive_mae,
                "naive_rmse": naive_rmse,
                "naive_mape": naive_mape,
            }
        )

    # --------------------------------------------------------
    # Error analysis on 4-week horizon.
    # --------------------------------------------------------

    errors = (
        actual_values
        - sarima_full_forecast
    )

    mean_abs_error = np.mean(
        np.abs(errors)
    )

    mean_signed_error = np.mean(
        errors
    )

    under_predictions = np.sum(
        errors > 0
    )

    over_predictions = np.sum(
        errors < 0
    )

    largest_error_index = np.argmax(
        np.abs(errors)
    )

    print("\n" + "-" * 70)
    print("SARIMA 4-WEEK ERROR ANALYSIS")

    print(
        f"Mean absolute error: "
        f"{mean_abs_error:.4f}"
    )

    print(
        f"Mean signed error: "
        f"{mean_signed_error:.4f}"
    )

    print(
        f"Under-predictions: "
        f"{under_predictions}"
    )

    print(
        f"Over-predictions: "
        f"{over_predictions}"
    )

    print(
        f"Largest absolute error: "
        f"{abs(errors[largest_error_index]):.4f}"
    )

    print(
        f"Largest error date: "
        f"{forecast_dates[largest_error_index].date()}"
    )

    error_results.append(
        {
            "city": city,
            "mean_absolute_error": mean_abs_error,
            "mean_signed_error": mean_signed_error,
            "under_predictions": int(
                under_predictions
            ),
            "over_predictions": int(
                over_predictions
            ),
            "largest_absolute_error": abs(
                errors[largest_error_index]
            ),
            "largest_error_date": forecast_dates[
                largest_error_index
            ],
        }
    )


# ============================================================
# FINAL SUMMARY
# ============================================================

results_df = pd.DataFrame(
    all_results
)

error_df = pd.DataFrame(
    error_results
)

print("\n\n")
print("=" * 80)
print("FINAL SARIMA vs NAIVE SUMMARY")
print("=" * 80)

if not results_df.empty:

    print(
        results_df.to_string(
            index=False
        )
    )

    print("\n\nMetric-wise comparison:")

    for _, row in results_df.iterrows():

        city = row["city"]
        horizon = row["horizon"]

        print(
            f"\n{city.upper()} - {horizon}"
        )

        print(
            f"MAE  -> "
            f"SARIMA: {row['sarima_mae']:.4f}, "
            f"Naive: {row['naive_mae']:.4f}"
        )

        print(
            f"RMSE -> "
            f"SARIMA: {row['sarima_rmse']:.4f}, "
            f"Naive: {row['naive_rmse']:.4f}"
        )

        print(
            f"MAPE -> "
            f"SARIMA: {row['sarima_mape']:.4f}%, "
            f"Naive: {row['naive_mape']:.4f}%"
        )

else:
    print("No SARIMA results were generated.")

print("\n")
print("=" * 80)
print("PHASE 10 SARIMA TEST COMPLETE")
print("=" * 80)

print(
    "\nIMPORTANT:"
    "\n- Final DengAI test data was not used."
    "\n- No model selection was performed using the final test set."
    "\n- This was one controlled SARIMA experiment."
    "\n- Do not claim SARIMA is better until the metrics are inspected."
)