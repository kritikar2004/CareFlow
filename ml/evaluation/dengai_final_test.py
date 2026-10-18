"""
CareFlow Phase 10
DengAI Protected Final Test

Purpose:
- Evaluate the candidates selected ONLY from validation results.
- Use the untouched DengAI test split.
- Use the same genuine recursive forecasting methodology.
- Test 1, 2, and 4 weekly horizons where supported.
- Do NOT perform model selection after seeing test results.

Selected candidates:
    IQ:
        1 week  -> Recursive XGBoost
        2 weeks -> SARIMA
        4 weeks -> SARIMA

    SJ:
        1 week  -> Naive
        2 weeks -> Naive
        4 weeks -> Naive
"""

from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error
from statsmodels.tsa.statespace.sarimax import SARIMAX
from xgboost import XGBRegressor


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

SPLIT_DIR = (
    PROJECT_ROOT
    / "ml"
    / "data"
    / "processed"
    / "dengai_split"
)


# ============================================================
# CONFIGURATION
# ============================================================

HORIZONS = {
    "1_week": 1,
    "2_weeks": 2,
    "4_weeks": 4,
}


# Final candidates selected before touching the test set.
SELECTED_MODELS = {
    "iq": {
        "1_week": "Recursive XGBoost",
        "2_weeks": "SARIMA",
        "4_weeks": "SARIMA",
    },
    "sj": {
        "1_week": "Naive",
        "2_weeks": "Naive",
        "4_weeks": "Naive",
    },
}


# SARIMA specification used in Phase 10 validation.
SARIMA_ORDER = (1, 0, 0)
SARIMA_SEASONAL_ORDER = (1, 0, 0, 52)


# ============================================================
# METRICS
# ============================================================

def calculate_metrics(actual, predicted):

    actual = np.asarray(actual, dtype=float)
    predicted = np.asarray(predicted, dtype=float)

    mae = mean_absolute_error(
        actual,
        predicted
    )

    rmse = np.sqrt(
        mean_squared_error(
            actual,
            predicted
        )
    )

    non_zero = actual != 0

    if np.any(non_zero):
        mape = np.mean(
            np.abs(
                (
                    actual[non_zero]
                    - predicted[non_zero]
                )
                / actual[non_zero]
            )
        ) * 100
    else:
        mape = np.nan

    return mae, rmse, mape


# ============================================================
# NAIVE
# ============================================================

def naive_forecast(
    train_values,
    horizon
):

    last_value = float(
        train_values[-1]
    )

    return np.repeat(
        last_value,
        horizon
    )


# ============================================================
# SARIMA
# ============================================================

def sarima_forecast(
    train_values,
    horizon
):

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

    forecast = np.maximum(
        np.asarray(
            forecast,
            dtype=float
        ),
        0
    )

    return forecast


# ============================================================
# XGBOOST RECURSIVE FORECAST
# ============================================================

def xgboost_recursive_forecast(
    city_df,
    cutoff_date,
    forecast_dates
):

    history = city_df[
        city_df["week_start_date"]
        <= cutoff_date
    ].copy()

    history = history.sort_values(
        "week_start_date"
    ).reset_index(drop=True)

    target = (
        history["total_cases"]
        .astype(float)
        .tolist()
    )

    predictions = []

    for forecast_date in forecast_dates:

        # Build features only from information available
        # before the forecast date.
        current_cases = target

        if len(current_cases) < 8:
            raise ValueError(
                "Not enough historical observations "
                "for recursive XGBoost."
            )

        row = {
            "year": forecast_date.year,
            "weekofyear": int(
                forecast_date.isocalendar().week
            ),
            "month": forecast_date.month,
            "quarter": forecast_date.quarter,
            "total_cases_lag_1": current_cases[-1],
            "total_cases_lag_2": current_cases[-2],
            "total_cases_lag_4": current_cases[-4],
            "total_cases_lag_8": current_cases[-8],
            "total_cases_rolling_mean_4": np.mean(
                current_cases[-4:]
            ),
            "total_cases_rolling_mean_8": np.mean(
                current_cases[-8:]
            ),
            "city_encoded": (
                0 if city_df["city"].iloc[0] == "iq"
                else 1
            ),
        }

        feature_columns = [
            "year",
            "weekofyear",
            "total_cases_lag_1",
            "total_cases_lag_2",
            "total_cases_lag_4",
            "total_cases_lag_8",
            "total_cases_rolling_mean_4",
            "total_cases_rolling_mean_8",
            "month",
            "quarter",
            "city_encoded",
        ]

        X_train_rows = []

        # Construct training examples using only
        # historical target information.
        for i in range(8, len(history)):

            date = history.loc[
                i,
                "week_start_date"
            ]

            values = (
                history.loc[
                    :i - 1,
                    "total_cases"
                ]
                .astype(float)
                .tolist()
            )

            X_train_rows.append(
                [
                    date.year,
                    int(
                        date.isocalendar().week
                    ),
                    values[-1],
                    values[-2],
                    values[-4],
                    values[-8],
                    np.mean(values[-4:]),
                    np.mean(values[-8:]),
                    date.month,
                    date.quarter,
                    (
                        0
                        if city_df["city"].iloc[0] == "iq"
                        else 1
                    ),
                ]
            )

        y_train = (
            history.loc[
                8:,
                "total_cases"
            ]
            .astype(float)
            .values
        )

        model = XGBRegressor(
            n_estimators=300,
            max_depth=4,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42,
            objective="reg:squarederror",
        )

        model.fit(
            np.asarray(
                X_train_rows,
                dtype=float
            ),
            y_train,
        )

        X_future = np.asarray(
            [
                row[column]
                for column in feature_columns
            ],
            dtype=float
        ).reshape(1, -1)

        prediction = float(
            model.predict(X_future)[0]
        )

        prediction = max(
            prediction,
            0
        )

        predictions.append(
            prediction
        )

        # Recursive step:
        # predicted value becomes available historical
        # information for the next forecast.
        target.append(
            prediction
        )

    return np.asarray(
        predictions,
        dtype=float
    )


# ============================================================
# LOAD DATA
# ============================================================

print("=" * 80)
print("CARE FLOW - PHASE 10")
print("DengAI Protected Final Test")
print("=" * 80)

print(
    f"\nLoading dataset:\n{DATA_PATH}"
)

df = pd.read_csv(
    DATA_PATH
)

df["week_start_date"] = pd.to_datetime(
    df["week_start_date"]
)

df = df.sort_values(
    [
        "city",
        "week_start_date"
    ]
).reset_index(drop=True)


# ============================================================
# VERIFY TEST SPLIT
# ============================================================

print("\nVerifying protected test split...")

for city in ["iq", "sj"]:

    test_path = SPLIT_DIR / "test.csv"

    test_split = pd.read_csv(
        test_path
    )

    test_split["week_start_date"] = pd.to_datetime(
        test_split["week_start_date"]
    )

    city_test = test_split[
        test_split["city"] == city
    ].sort_values(
        "week_start_date"
    )

    print(
        f"{city.upper()} test rows: "
        f"{len(city_test)}"
    )

    print(
        f"Test period: "
        f"{city_test['week_start_date'].min().date()} "
        f"-> "
        f"{city_test['week_start_date'].max().date()}"
    )


# ============================================================
# FINAL TEST
# ============================================================

results = []
error_results = []


for city in ["iq", "sj"]:

    print("\n")
    print("=" * 80)
    print(f"FINAL TEST - {city.upper()}")
    print("=" * 80)

    city_df = (
        df[
            df["city"] == city
        ]
        .sort_values("week_start_date")
        .reset_index(drop=True)
    )

    test_split = pd.read_csv(
        SPLIT_DIR / "test.csv"
    )

    test_split["week_start_date"] = pd.to_datetime(
        test_split["week_start_date"]
    )

    city_test = (
        test_split[
            test_split["city"] == city
        ]
        .sort_values("week_start_date")
        .reset_index(drop=True)
    )

    test_dates = (
        city_test["week_start_date"]
        .tolist()
    )

    # We evaluate the first four test observations,
    # matching the 1/2/4-week validation protocol.
    forecast_dates = test_dates[:4]

    cutoff_date = (
        forecast_dates[0]
        - pd.Timedelta(days=7)
    )

    training_df = city_df[
        city_df["week_start_date"]
        <= cutoff_date
    ].copy()

    train_values = (
        training_df["total_cases"]
        .astype(float)
        .values
    )

    actual_values = (
        city_df[
            city_df["week_start_date"]
            .isin(forecast_dates)
        ]
        .sort_values("week_start_date")[
            "total_cases"
        ]
        .astype(float)
        .values
    )

    print(
        f"\nTraining period: "
        f"{training_df['week_start_date'].min().date()} "
        f"-> "
        f"{training_df['week_start_date'].max().date()}"
    )

    print(
        f"Final test forecast window: "
        f"{forecast_dates[0].date()} "
        f"-> "
        f"{forecast_dates[-1].date()}"
    )

    print(
        f"Actual test values: "
        f"{actual_values.tolist()}"
    )

    # --------------------------------------------------------
    # Generate each candidate forecast.
    # --------------------------------------------------------

    print("\nGenerating final-test candidate forecasts...")

    naive_predictions = naive_forecast(
        train_values,
        4
    )

    sarima_predictions = sarima_forecast(
        train_values,
        4
    )

    xgb_predictions = xgboost_recursive_forecast(
        city_df,
        cutoff_date,
        forecast_dates
    )

    candidate_predictions = {
        "Naive": naive_predictions,
        "SARIMA": sarima_predictions,
        "Recursive XGBoost": xgb_predictions,
    }

    print(
        "\nNaive:",
        np.round(
            naive_predictions,
            4
        ).tolist()
    )

    print(
        "SARIMA:",
        np.round(
            sarima_predictions,
            4
        ).tolist()
    )

    print(
        "Recursive XGBoost:",
        np.round(
            xgb_predictions,
            4
        ).tolist()
    )

    # --------------------------------------------------------
    # Evaluate selected candidates only for reporting.
    # --------------------------------------------------------

    for horizon_name, horizon in HORIZONS.items():

        selected_model = SELECTED_MODELS[
            city
        ][horizon_name]

        predictions = candidate_predictions[
            selected_model
        ][:horizon]

        actual = actual_values[
            :horizon
        ]

        mae, rmse, mape = calculate_metrics(
            actual,
            predictions
        )

        print("\n" + "-" * 70)
        print(
            f"{city.upper()} - {horizon_name}"
        )

        print(
            f"Selected model: {selected_model}"
        )

        print(
            f"MAE : {mae:.4f}"
        )

        print(
            f"RMSE: {rmse:.4f}"
        )

        print(
            f"MAPE: {mape:.4f}%"
        )

        results.append(
            {
                "city": city,
                "horizon": horizon_name,
                "selected_model": selected_model,
                "mae": mae,
                "rmse": rmse,
                "mape": mape,
            }
        )

    # --------------------------------------------------------
    # Error analysis for selected 4-week candidate.
    # --------------------------------------------------------

    selected_4_week_model = SELECTED_MODELS[
        city
    ]["4_weeks"]

    selected_predictions = candidate_predictions[
        selected_4_week_model
    ]

    errors = (
        actual_values
        - selected_predictions
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

    largest_index = np.argmax(
        np.abs(errors)
    )

    print("\n" + "-" * 70)
    print(
        "FINAL TEST 4-WEEK ERROR ANALYSIS"
    )

    print(
        f"Selected model: "
        f"{selected_4_week_model}"
    )

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
        f"{abs(errors[largest_index]):.4f}"
    )

    print(
        f"Largest error date: "
        f"{forecast_dates[largest_index].date()}"
    )

    error_results.append(
        {
            "city": city,
            "selected_model": selected_4_week_model,
            "mean_absolute_error": mean_abs_error,
            "mean_signed_error": mean_signed_error,
            "under_predictions": int(
                under_predictions
            ),
            "over_predictions": int(
                over_predictions
            ),
            "largest_absolute_error": abs(
                errors[largest_index]
            ),
            "largest_error_date": forecast_dates[
                largest_index
            ],
        }
    )


# ============================================================
# FINAL RESULTS
# ============================================================

results_df = pd.DataFrame(
    results
)

error_df = pd.DataFrame(
    error_results
)


print("\n\n")
print("=" * 80)
print("FINAL DENGAI TEST RESULTS")
print("=" * 80)

print(
    results_df.to_string(
        index=False
    )
)

print("\n")
print("=" * 80)
print("FINAL TEST ERROR ANALYSIS")
print("=" * 80)

print(
    error_df.to_string(
        index=False
    )
)

print("\n")
print("=" * 80)
print("PHASE 10 PROTECTED FINAL TEST COMPLETE")
print("=" * 80)

print(
    "\nIMPORTANT:"
    "\n- Candidate selection was performed before this test."
    "\n- The final test results must not be used to retune models."
    "\n- The final test is reported as evaluation evidence only."
)