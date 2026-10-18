from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from xgboost import XGBRegressor

from backend.datasets.validator import generate_period_disclaimer


# ============================================================
# CareFlow Phase 20 - Disease Forecasting
# ============================================================

MODEL_NAME = "XGBoost"
MODEL_VERSION = "disease-xgboost-v1"
FEATURE_SCHEMA_VERSION = "disease-features-v1"

XGB_CONFIG = {
    "objective": "reg:squarederror",
    "n_estimators": 300,
    "max_depth": 4,
    "learning_rate": 0.05,
    "subsample": 0.8,
    "colsample_bytree": 0.8,
    "random_state": 42,
}


SUPPORTED_HORIZONS = {7, 14, 30}


# ============================================================
# Metrics
# ============================================================

def calculate_metrics(
    y_true: pd.Series,
    y_pred: np.ndarray,
) -> dict[str, float | None]:
    """
    Calculate MAE, RMSE and MAPE using the same metric
    principles established by the existing CareFlow ML layer.
    """

    y_true_array = np.asarray(y_true, dtype=float)
    y_pred_array = np.asarray(y_pred, dtype=float)

    mae = float(
        np.mean(
            np.abs(y_true_array - y_pred_array)
        )
    )

    rmse = float(
        np.sqrt(
            np.mean(
                (y_true_array - y_pred_array) ** 2
            )
        )
    )

    non_zero = y_true_array != 0

    if np.any(non_zero):
        mape = float(
            np.mean(
                np.abs(
                    (
                        y_true_array[non_zero]
                        - y_pred_array[non_zero]
                    )
                    / y_true_array[non_zero]
                )
            )
            * 100
        )
    else:
        mape = None

    return {
        "MAE": mae,
        "RMSE": rmse,
        "MAPE": mape,
    }


# ============================================================
# Model
# ============================================================

def build_disease_model() -> XGBRegressor:
    """
    Create the established CareFlow XGBoost configuration
    for a disease-specific forecasting model.
    """

    return XGBRegressor(**XGB_CONFIG)


# ============================================================
# Disease Data Preparation
# ============================================================

def prepare_disease_data(
    dataframe: pd.DataFrame,
    disease: str,
) -> pd.DataFrame:
    """
    Prepare observations for one specific disease.

    The input must contain:
        date
        disease
        cases

    One separate time series is created for each disease.
    """

    required_columns = {
        "date",
        "disease",
        "cases",
    }

    missing = required_columns - set(dataframe.columns)

    if missing:
        raise ValueError(
            "Disease dataset is missing required processing "
            f"columns: {sorted(missing)}"
        )

    requested_disease = str(disease).strip()

    if not requested_disease:
        raise ValueError(
            "Disease name is required."
        )

    data = dataframe.copy()

    data["disease"] = (
        data["disease"]
        .astype(str)
        .str.strip()
    )

    data = data[
        data["disease"].str.casefold()
        == requested_disease.casefold()
    ].copy()

    if data.empty:
        raise ValueError(
            f"No disease data found for '{requested_disease}'."
        )

    data["date"] = pd.to_datetime(
        data["date"],
        errors="coerce",
    )

    data["cases"] = pd.to_numeric(
        data["cases"],
        errors="coerce",
    )

    data = data.dropna(
        subset=[
            "date",
            "cases",
        ]
    ).copy()

    if data.empty:
        raise ValueError(
            f"No usable observations found for disease "
            f"'{requested_disease}'."
        )

    if (data["cases"] < 0).any():
        raise ValueError(
            f"Disease '{requested_disease}' contains "
            "negative case counts."
        )

    # The validator already rejects duplicate date+disease
    # observations. This additional guard protects direct
    # function usage.
    duplicate_mask = data.duplicated(
        subset=["date", "disease"],
        keep=False,
    )

    if duplicate_mask.any():
        raise ValueError(
            f"Disease '{requested_disease}' contains duplicate "
            "date observations."
        )

    data = (
        data[
            [
                "date",
                "disease",
                "cases",
            ]
        ]
        .sort_values("date")
        .reset_index(drop=True)
    )

    return data


# ============================================================
# History Assessment
# ============================================================

def get_disease_history_info(
    dataframe: pd.DataFrame,
    disease: str,
) -> dict[str, Any]:
    """
    Calculate the historical coverage and short-history
    classification for one disease.

    This does not block forecasting based only on history length.
    """

    data = prepare_disease_data(
        dataframe,
        disease,
    )

    start_date = data["date"].min()
    end_date = data["date"].max()

    historical_days = int(
        (end_date - start_date).days
    ) + 1

    if historical_days < 30:
        history_level = "very_limited"
        warning = (
            "Very limited historical disease data. "
            "Forecast reliability may be low."
        )

    elif historical_days < 90:
        history_level = "limited"
        warning = (
            "Limited historical disease data. "
            "A forecast can be generated, but reliability "
            "may be reduced."
        )

    elif historical_days < 365:
        history_level = "moderate"
        warning = (
            "Moderate historical disease data. "
            "Additional history is recommended for stronger "
            "seasonal patterns."
        )

    elif historical_days < 730:
        history_level = "recommended"
        warning = (
            "At least 12 months of historical disease data "
            "are available."
        )

    else:
        history_level = "seasonal"
        warning = (
            "At least 24 months of historical disease data "
            "are available, providing better seasonal history "
            "where relevant."
        )

    return {
        "disease": str(disease).strip(),
        "start_date": start_date.date().isoformat(),
        "end_date": end_date.date().isoformat(),
        "historical_days": historical_days,
        "observation_count": len(data),
        "history_level": history_level,
        "warning": warning,
        "disclaimer": generate_period_disclaimer(
            historical_days
        ),
    }


# ============================================================
# Feature Engineering
# ============================================================

def _select_feature_lags(
    observation_count: int,
) -> list[int]:
    """
    Select lag features that are compatible with the amount
    of available disease history.

    Short histories use shorter lag structures rather than
    being rejected by an arbitrary blanket minimum.
    """

    lags = [1]

    if observation_count >= 14:
        lags.append(7)

    if observation_count >= 30:
        lags.append(14)

    if observation_count >= 60:
        lags.append(30)

    return lags


def create_disease_features(
    dataframe: pd.DataFrame,
) -> tuple[pd.DataFrame, list[str]]:
    """
    Create chronological autoregressive disease features.

    Features include:
    - calendar features
    - disease case lags
    - rolling means

    The disease column itself is not used as a model feature
    because each disease receives its own separate model.
    """

    if dataframe.empty:
        raise ValueError(
            "Cannot create disease features from empty data."
        )

    data = dataframe.copy()

    data["date"] = pd.to_datetime(
        data["date"],
        errors="coerce",
    )

    data["cases"] = pd.to_numeric(
        data["cases"],
        errors="coerce",
    )

    data = (
        data.dropna(
            subset=[
                "date",
                "cases",
            ]
        )
        .sort_values("date")
        .reset_index(drop=True)
    )

    if data.empty:
        raise ValueError(
            "No usable disease observations remain after "
            "feature preparation."
        )

    observation_count = len(data)

    lags = _select_feature_lags(
        observation_count
    )

    feature_columns = [
        "day_of_week",
        "day_of_month",
        "month",
        "week_of_year",
    ]

    data["day_of_week"] = data["date"].dt.dayofweek
    data["day_of_month"] = data["date"].dt.day
    data["month"] = data["date"].dt.month
    data["week_of_year"] = (
        data["date"].dt.isocalendar().week.astype(int)
    )

    for lag in lags:
        column = f"cases_lag_{lag}"

        data[column] = data["cases"].shift(lag)

        feature_columns.append(column)

    rolling_windows = []

    if observation_count >= 14:
        rolling_windows.append(7)

    if observation_count >= 30:
        rolling_windows.append(14)

    if observation_count >= 60:
        rolling_windows.append(30)

    for window in rolling_windows:
        column = f"cases_rolling_mean_{window}"

        data[column] = (
            data["cases"]
            .rolling(window)
            .mean()
        )

        feature_columns.append(column)

    return data, feature_columns


# ============================================================
# Chronological Split
# ============================================================

def chronological_split(
    dataframe: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Split the prepared disease time series chronologically:

        70% training
        15% validation
        15% test
    """

    data = (
        dataframe
        .sort_values("date")
        .reset_index(drop=True)
    )

    n = len(data)

    if n < 20:
        raise ValueError(
            "At least 20 usable disease observations are "
            "required for chronological model evaluation."
        )

    train_end = int(n * 0.70)
    validation_end = int(n * 0.85)

    train = data.iloc[
        :train_end
    ].copy()

    validation = data.iloc[
        train_end:validation_end
    ].copy()

    test = data.iloc[
        validation_end:
    ].copy()

    if train.empty or validation.empty or test.empty:
        raise ValueError(
            "Disease dataset is too small to create "
            "training, validation and test periods."
        )

    return train, validation, test


# ============================================================
# Disease Model Training
# ============================================================

def train_disease_model(
    dataframe: pd.DataFrame,
    disease: str,
) -> dict[str, Any]:
    """
    Train and evaluate one disease-specific XGBoost model.

    The final test period remains separate from model
    selection/evaluation.
    """

    data = prepare_disease_data(
        dataframe,
        disease,
    )

    feature_data, feature_columns = create_disease_features(
        data
    )

    feature_data = feature_data.dropna(
        subset=feature_columns + ["cases"]
    ).copy()

    if len(feature_data) < 20:
        raise ValueError(
            f"Not enough usable observations for disease "
            f"'{disease}' after feature generation. "
            "At least 20 usable observations are required "
            "for chronological model evaluation."
        )

    train, validation, test = chronological_split(
        feature_data
    )

    X_train = train[feature_columns]
    y_train = train["cases"]

    X_validation = validation[feature_columns]
    y_validation = validation["cases"]

    X_test = test[feature_columns]
    y_test = test["cases"]

    model = build_disease_model()

    model.fit(
        X_train,
        y_train,
    )

    validation_predictions = model.predict(
        X_validation
    )

    test_predictions = model.predict(
        X_test
    )

    validation_predictions = np.maximum(
        validation_predictions,
        0.0,
    )

    test_predictions = np.maximum(
        test_predictions,
        0.0,
    )

    validation_metrics = calculate_metrics(
        y_validation,
        validation_predictions,
    )

    test_metrics = calculate_metrics(
        y_test,
        test_predictions,
    )

    return {
        "model": model,
        "model_name": MODEL_NAME,
        "model_version": MODEL_VERSION,
        "feature_schema_version": FEATURE_SCHEMA_VERSION,
        "disease": str(disease).strip(),
        "feature_columns": feature_columns,
        "validation_metrics": validation_metrics,
        "test_metrics": test_metrics,
        "training_period_start": (
            train["date"].min().date()
        ),
        "training_period_end": (
            train["date"].max().date()
        ),
        "validation_period_start": (
            validation["date"].min().date()
        ),
        "validation_period_end": (
            validation["date"].max().date()
        ),
        "test_period_start": (
            test["date"].min().date()
        ),
        "test_period_end": (
            test["date"].max().date()
        ),
        "training_rows": len(train),
        "validation_rows": len(validation),
        "test_rows": len(test),
        "usable_observations": len(feature_data),
    }


# ============================================================
# Recursive Feature Row
# ============================================================

def _build_forecast_feature_row(
    history: list[float],
    forecast_date: pd.Timestamp,
    feature_columns: list[str],
) -> pd.DataFrame:
    """
    Build one future feature row using the same feature
    structure used during training.
    """

    history_series = pd.Series(
        history,
        dtype=float,
    )

    feature_row: dict[str, float | int] = {
        "day_of_week": forecast_date.dayofweek,
        "day_of_month": forecast_date.day,
        "month": forecast_date.month,
        "week_of_year": int(
            forecast_date.isocalendar().week
        ),
    }

    for column in feature_columns:

        if column.startswith("cases_lag_"):
            lag = int(
                column.replace(
                    "cases_lag_",
                    "",
                )
            )

            if len(history_series) < lag:
                raise ValueError(
                    f"Insufficient history to construct "
                    f"{column}."
                )

            feature_row[column] = (
                history_series.iloc[-lag]
            )

        elif column.startswith(
            "cases_rolling_mean_"
        ):
            window = int(
                column.replace(
                    "cases_rolling_mean_",
                    "",
                )
            )

            if len(history_series) < window:
                raise ValueError(
                    f"Insufficient history to construct "
                    f"{column}."
                )

            feature_row[column] = (
                history_series
                .iloc[-window:]
                .mean()
            )

    return pd.DataFrame(
        [feature_row]
    )[feature_columns]


# ============================================================
# Disease Forecast
# ============================================================

def forecast_disease(
    dataframe: pd.DataFrame,
    disease: str,
    horizon: int = 7,
) -> dict[str, Any]:
    """
    Generate a recursive disease-specific forecast.

    Supported horizons:
        7
        14
        30

    If the disease does not have enough usable observations
    for model training, a controlled limited/unavailable
    response is returned instead of fabricated predictions.
    """

    if horizon not in SUPPORTED_HORIZONS:
        raise ValueError(
            "Disease forecast horizon must be 7, 14, or 30 days."
        )

    requested_disease = str(disease).strip()

    if not requested_disease:
        raise ValueError(
            "Disease name is required."
        )

    data = prepare_disease_data(
        dataframe,
        requested_disease,
    )

    history_info = get_disease_history_info(
        dataframe,
        requested_disease,
    )

    try:
        training_result = train_disease_model(
            dataframe,
            requested_disease,
        )
    except ValueError as exc:
        return {
            "status": "limited",
            "available": False,
            "disease": requested_disease,
            "horizon": horizon,
            "predictions": [],
            "reason": str(exc),
            "history": history_info,
            "disclaimer": (
                "A reliable hospital-specific disease forecast "
                "could not be generated from the available "
                "historical data. No forecast values have been "
                "fabricated."
            ),
        }

    model = training_result["model"]
    feature_columns = training_result[
        "feature_columns"
    ]

    history = (
        data["cases"]
        .astype(float)
        .tolist()
    )

    last_date = pd.Timestamp(
        data["date"].max()
    )

    predictions = []

    for step in range(
        1,
        horizon + 1,
    ):
        forecast_date = (
            last_date
            + pd.Timedelta(days=step)
        )

        feature_row = _build_forecast_feature_row(
            history,
            forecast_date,
            feature_columns,
        )

        prediction = float(
            model.predict(
                feature_row
            )[0]
        )

        prediction = max(
            prediction,
            0.0,
        )

        predictions.append(
            {
                "date": forecast_date.date().isoformat(),
                "predicted_cases": prediction,
            }
        )

        history.append(
            prediction
        )

    return {
        "status": "available",
        "available": True,
        "disease": requested_disease,
        "horizon": horizon,
        "forecast_type": "disease",
        "model_name": training_result["model_name"],
        "model_version": training_result["model_version"],
        "feature_schema_version": training_result[
            "feature_schema_version"
        ],
        "predictions": predictions,
        "validation_metrics": training_result[
            "validation_metrics"
        ],
        "test_metrics": training_result[
            "test_metrics"
        ],
        "training_period_start": (
            training_result[
                "training_period_start"
            ].isoformat()
        ),
        "training_period_end": (
            training_result[
                "training_period_end"
            ].isoformat()
        ),
        "validation_period_start": (
            training_result[
                "validation_period_start"
            ].isoformat()
        ),
        "validation_period_end": (
            training_result[
                "validation_period_end"
            ].isoformat()
        ),
        "test_period_start": (
            training_result[
                "test_period_start"
            ].isoformat()
        ),
        "test_period_end": (
            training_result[
                "test_period_end"
            ].isoformat()
        ),
        "training_rows": training_result[
            "training_rows"
        ],
        "validation_rows": training_result[
            "validation_rows"
        ],
        "test_rows": training_result[
            "test_rows"
        ],
        "history": history_info,
        "disclaimer": (
            "This hospital-specific forecast is based on "
            "historical disease data uploaded by the hospital. "
            "It is intended for operational decision support "
            "and is not a diagnosis or treatment recommendation."
        ),
    }


# ============================================================
# Process All Diseases
# ============================================================

def forecast_all_diseases(
    dataframe: pd.DataFrame,
    horizon: int = 7,
) -> dict[str, Any]:
    """
    Process every disease present in an uploaded disease dataset.

    Each disease receives its own independent forecasting
    pipeline/model.
    """

    if horizon not in SUPPORTED_HORIZONS:
        raise ValueError(
            "Disease forecast horizon must be 7, 14, or 30 days."
        )

    required_columns = {
        "date",
        "disease",
        "cases",
    }

    missing = required_columns - set(dataframe.columns)

    if missing:
        raise ValueError(
            "Disease dataset is missing required processing "
            f"columns: {sorted(missing)}"
        )

    disease_names = sorted(
        {
            str(value).strip()
            for value in dataframe["disease"].dropna()
            if str(value).strip()
        }
    )

    if not disease_names:
        raise ValueError(
            "No valid disease names were found in the dataset."
        )

    results = []

    for disease in disease_names:
        result = forecast_disease(
            dataframe,
            disease,
            horizon,
        )

        results.append(
            result
        )

    return {
        "status": "processed",
        "horizon": horizon,
        "disease_count": len(results),
        "diseases": results,
    }