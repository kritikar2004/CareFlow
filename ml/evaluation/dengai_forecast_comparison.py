from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error
from xgboost import XGBRegressor


DATA_PATH = Path(
    "ml/data/processed/dengai_ml_ready.csv"
)

DATE_COLUMN = "week_start_date"
CITY_COLUMN = "city"
TARGET = "total_cases"

# DengAI is weekly.
# 1 step = ~7 days
# 2 steps = ~14 days
# 4 steps = ~28 days
HORIZONS = [1, 2, 4]

CITY_MAPPING = {
    "iq": 0,
    "sj": 1,
}

# Only features that can genuinely be generated
# at forecast time.
FORECAST_FEATURES = [
    "year",
    "weekofyear",
    "month",
    "quarter",
    "city_encoded",
    "total_cases_lag_1",
    "total_cases_lag_2",
    "total_cases_lag_4",
    "total_cases_lag_8",
    "total_cases_rolling_mean_4",
    "total_cases_rolling_mean_8",
]

XGB_PARAMS = {
    "objective": "reg:squarederror",
    "n_estimators": 300,
    "max_depth": 4,
    "learning_rate": 0.05,
    "subsample": 0.8,
    "colsample_bytree": 0.8,
    "random_state": 42,
}


def calculate_mape(actual, predicted):
    actual = np.asarray(actual)
    predicted = np.asarray(predicted)

    non_zero = actual != 0

    if non_zero.sum() == 0:
        return np.nan

    return (
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


def calculate_metrics(actual, predicted):
    return {
        "MAE": mean_absolute_error(
            actual,
            predicted
        ),
        "RMSE": np.sqrt(
            mean_squared_error(
                actual,
                predicted
            )
        ),
        "MAPE": calculate_mape(
            actual,
            predicted
        ),
    }


def create_recursive_features(
    history,
    forecast_date,
    city_encoded
):
    """
    Create features for one future week.

    Only historical or previously predicted
    dengue cases are used.
    """

    if len(history) < 8:
        raise ValueError(
            "At least 8 historical observations "
            "are required."
        )

    return {
        "year": forecast_date.year,
        "weekofyear": forecast_date.isocalendar().week,
        "month": forecast_date.month,
        "quarter": forecast_date.quarter,
        "city_encoded": city_encoded,

        "total_cases_lag_1": history[-1],
        "total_cases_lag_2": history[-2],
        "total_cases_lag_4": history[-4],
        "total_cases_lag_8": history[-8],

        "total_cases_rolling_mean_4": np.mean(
            history[-4:]
        ),

        "total_cases_rolling_mean_8": np.mean(
            history[-8:]
        ),
    }


def train_model(train_data):
    model = XGBRegressor(
        **XGB_PARAMS
    )

    model.fit(
        train_data[FORECAST_FEATURES],
        train_data[TARGET]
    )

    return model


def recursive_xgb_forecast(
    train_data,
    forecast_dates,
    city_encoded
):
    """
    Genuine recursive forecast.

    Future actual dengue cases are NEVER
    inserted into the prediction history.
    """

    model = train_model(
        train_data
    )

    history = (
        train_data[TARGET]
        .astype(float)
        .tolist()
    )

    predictions = []

    for forecast_date in forecast_dates:

        features = create_recursive_features(
            history,
            forecast_date,
            city_encoded
        )

        X_future = pd.DataFrame(
            [features],
            columns=FORECAST_FEATURES
        )

        prediction = float(
            model.predict(X_future)[0]
        )

        # Cases cannot be negative.
        prediction = max(
            0.0,
            prediction
        )

        predictions.append(
            prediction
        )

        # Add prediction, NOT actual.
        history.append(
            prediction
        )

    return predictions


def naive_forecast(
    train_data,
    horizon
):
    """
    Persistence baseline:
    repeat the last observed value.
    """

    last_value = float(
        train_data[TARGET].iloc[-1]
    )

    return [
        last_value
        for _ in range(horizon)
    ]


def print_metrics(
    name,
    metrics
):
    print(
        f"{name:<10}"
        f"MAE={metrics['MAE']:.4f}  "
        f"RMSE={metrics['RMSE']:.4f}  "
        f"MAPE={metrics['MAPE']:.4f}%"
    )


# =========================================================
# LOAD DATA
# =========================================================

df = pd.read_csv(
    DATA_PATH
)

df[DATE_COLUMN] = pd.to_datetime(
    df[DATE_COLUMN]
)

df = df.sort_values(
    [CITY_COLUMN, DATE_COLUMN]
).reset_index(
    drop=True
)


# =========================================================
# VERIFY RAW DATA COLUMNS
# =========================================================

required_raw_columns = [
    DATE_COLUMN,
    CITY_COLUMN,
    TARGET,
]

missing_columns = [
    column
    for column in required_raw_columns
    if column not in df.columns
]

if missing_columns:
    raise ValueError(
        "Missing required raw columns: "
        + ", ".join(missing_columns)
    )


# =========================================================
# CREATE CITY ENCODING
# =========================================================

df["city_encoded"] = (
    df[CITY_COLUMN]
    .map(CITY_MAPPING)
)

if df["city_encoded"].isna().any():

    unknown_cities = (
        df.loc[
            df["city_encoded"].isna(),
            CITY_COLUMN
        ]
        .unique()
        .tolist()
    )

    raise ValueError(
        f"Unknown cities found: "
        f"{unknown_cities}"
    )


print("=" * 75)
print("DengAI Genuine Recursive Forecast Comparison")
print("=" * 75)

print(
    f"Dataset: {DATA_PATH}"
)

print(
    f"Rows: {len(df)}"
)

print(
    f"Cities: "
    f"{sorted(df[CITY_COLUMN].unique())}"
)

print()

print(
    "City encoding:"
)

print(
    "  iq -> 0"
)

print(
    "  sj -> 1"
)

print()

print(
    "Forecast uses only:"
)

print(
    "  - historical dengue cases"
)

print(
    "  - recursively predicted dengue cases"
)

print(
    "  - calendar features"
)

print(
    "  - city encoding"
)

print()

print(
    "Future weather values are NOT used."
)

print(
    "Final Phase 9 test set remains untouched."
)

print()


# =========================================================
# PROCESS EACH CITY
# =========================================================

for city in sorted(
    df[CITY_COLUMN].unique()
):

    print("=" * 75)
    print(
        f"CITY: {city}"
    )
    print("=" * 75)

    city_df = (
        df[
            df[CITY_COLUMN] == city
        ]
        .sort_values(DATE_COLUMN)
        .reset_index(drop=True)
    )

    city_encoded = CITY_MAPPING[
        city
    ]

    print(
        f"Rows: {len(city_df)}"
    )

    print(
        f"Date range: "
        f"{city_df[DATE_COLUMN].min().date()} "
        f"to "
        f"{city_df[DATE_COLUMN].max().date()}"
    )

    # -----------------------------------------------------
    # Phase 9 validation boundaries
    # -----------------------------------------------------

    if city == "iq":

        validation_end = pd.Timestamp(
            "2009-01-01"
        )

    elif city == "sj":

        validation_end = pd.Timestamp(
            "2005-08-13"
        )

    else:

        raise ValueError(
            f"Unexpected city: {city}"
        )

    validation_data = city_df[
        city_df[DATE_COLUMN]
        <= validation_end
    ].copy()

    # Final 4 validation weeks.
    forecast_window = (
        validation_data
        .tail(4)
        .copy()
        .reset_index(drop=True)
    )

    forecast_dates = (
        forecast_window[
            DATE_COLUMN
        ]
        .tolist()
    )

    # Observation immediately before
    # forecast window.
    cutoff_date = (
        forecast_dates[0]
        - pd.Timedelta(days=7)
    )

    train_data = validation_data[
        validation_data[DATE_COLUMN]
        <= cutoff_date
    ].copy()

    print()

    print(
        f"Forecast cutoff: "
        f"{cutoff_date.date()}"
    )

    print(
        f"Forecast window: "
        f"{forecast_dates[0].date()} "
        f"to "
        f"{forecast_dates[-1].date()}"
    )

    print(
        f"Training rows: "
        f"{len(train_data)}"
    )

    print(
        "Final Phase 9 test rows: NOT USED"
    )

    print()


    # =====================================================
    # 1 / 2 / 4 WEEK FORECASTS
    # =====================================================

    for horizon in HORIZONS:

        horizon_dates = (
            forecast_dates[:horizon]
        )

        actual = (
            forecast_window[
                forecast_window[DATE_COLUMN]
                .isin(horizon_dates)
            ][TARGET]
            .to_numpy()
        )

        # -------------------------------------------------
        # XGBoost
        # -------------------------------------------------

        xgb_predictions = (
            recursive_xgb_forecast(
                train_data,
                horizon_dates,
                city_encoded
            )
        )

        xgb_metrics = calculate_metrics(
            actual,
            xgb_predictions
        )

        # -------------------------------------------------
        # Naive
        # -------------------------------------------------

        naive_predictions = (
            naive_forecast(
                train_data,
                horizon
            )
        )

        naive_metrics = calculate_metrics(
            actual,
            naive_predictions
        )

        print(
            "-" * 60
        )

        print(
            f"Horizon: "
            f"{horizon} week(s) "
            f"(~{horizon * 7} days)"
        )

        print_metrics(
            "XGBoost",
            xgb_metrics
        )

        print_metrics(
            "Naive",
            naive_metrics
        )

        print(
            "Comparison:"
        )

        print(
            f"  MAE  -> "
            f"{'XGBoost' if xgb_metrics['MAE'] < naive_metrics['MAE'] else 'Naive'}"
        )

        print(
            f"  RMSE -> "
            f"{'XGBoost' if xgb_metrics['RMSE'] < naive_metrics['RMSE'] else 'Naive'}"
        )

        print(
            f"  MAPE -> "
            f"{'XGBoost' if xgb_metrics['MAPE'] < naive_metrics['MAPE'] else 'Naive'}"
        )

        print()


    # =====================================================
    # ERROR ANALYSIS
    # =====================================================

    print(
        "-" * 60
    )

    print(
        "4-week XGBoost Error Analysis"
    )

    four_week_predictions = (
        recursive_xgb_forecast(
            train_data,
            forecast_dates,
            city_encoded
        )
    )

    error_df = forecast_window[
        [
            DATE_COLUMN,
            TARGET,
        ]
    ].copy()

    error_df[
        "prediction"
    ] = four_week_predictions

    error_df[
        "signed_error"
    ] = (
        error_df[TARGET]
        - error_df["prediction"]
    )

    error_df[
        "absolute_error"
    ] = (
        error_df["signed_error"]
        .abs()
    )

    print(
        f"Mean absolute error: "
        f"{error_df['absolute_error'].mean():.4f}"
    )

    print(
        f"Mean signed error: "
        f"{error_df['signed_error'].mean():.4f}"
    )

    print(
        f"Underpredictions: "
        f"{(
            error_df['signed_error'] > 0
        ).sum()}"
    )

    print(
        f"Overpredictions: "
        f"{(
            error_df['signed_error'] < 0
        ).sum()}"
    )

    largest_error = error_df.loc[
        error_df["absolute_error"].idxmax()
    ]

    print(
        f"Largest absolute error: "
        f"{largest_error['absolute_error']:.4f} "
        f"on "
        f"{largest_error[DATE_COLUMN].date()}"
    )

    print()


print("=" * 75)
print("DengAI Genuine Forecast Test Complete")
print("=" * 75)

print(
    "DengAI is weekly."
)

print(
    "Therefore tested horizons are "
    "1, 2 and 4 weeks "
    "(approximately 7, 14 and 28 days)."
)

print(
    "Exact 30-day forecasting is not claimed "
    "because the dataset is weekly."
)