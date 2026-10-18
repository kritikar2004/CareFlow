from pathlib import Path

import pandas as pd
from statsmodels.tsa.statespace.sarimax import SARIMAX
from xgboost import XGBRegressor

from ml.models.model_persistence import save_model


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

ARTIFACT_DIR = (
    PROJECT_ROOT
    / "ml"
    / "artifacts"
    / "dengai"
)


# ============================================================
# CONFIGURATION
# ============================================================

DATE_COLUMN = "week_start_date"
CITY_COLUMN = "city"
TARGET = "total_cases"

CITY_MAPPING = {
    "iq": 0,
    "sj": 1,
}

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

SARIMA_ORDER = (1, 0, 0)
SARIMA_SEASONAL_ORDER = (1, 0, 0, 52)


# ============================================================
# LOAD DATA
# ============================================================

def load_data():
    data = pd.read_csv(DATA_PATH)

    data[DATE_COLUMN] = pd.to_datetime(
        data[DATE_COLUMN]
    )

    data = data.sort_values(
        [CITY_COLUMN, DATE_COLUMN]
    ).reset_index(drop=True)

    data["city_encoded"] = data[CITY_COLUMN].map(
        CITY_MAPPING
    )

    if data["city_encoded"].isna().any():
        unknown_cities = (
            data.loc[
                data["city_encoded"].isna(),
                CITY_COLUMN
            ]
            .unique()
            .tolist()
        )

        raise ValueError(
            f"Unknown cities found: {unknown_cities}"
        )

    return data


# ============================================================
# LOAD PROTECTED TEST SPLIT
# ============================================================

def load_test_split():
    test_split = pd.read_csv(
        SPLIT_DIR / "test.csv"
    )

    test_split[DATE_COLUMN] = pd.to_datetime(
        test_split[DATE_COLUMN]
    )

    return test_split


# ============================================================
# DETERMINE TRAINING DATA
# ============================================================

def get_training_data(
    data,
    test_split,
    city
):
    city_test = (
        test_split[
            test_split[CITY_COLUMN] == city
        ]
        .sort_values(DATE_COLUMN)
        .reset_index(drop=True)
    )

    if city_test.empty:
        raise ValueError(
            f"No test data found for city: {city}"
        )

    first_test_date = city_test[
        DATE_COLUMN
    ].iloc[0]

    cutoff_date = (
        first_test_date
        - pd.Timedelta(days=7)
    )

    city_data = (
        data[
            data[CITY_COLUMN] == city
        ]
        .sort_values(DATE_COLUMN)
        .reset_index(drop=True)
    )

    training_data = city_data[
        city_data[DATE_COLUMN] <= cutoff_date
    ].copy()

    if training_data.empty:
        raise ValueError(
            f"No training data available for city: {city}"
        )

    print(
        f"\n{city.upper()} training period:"
    )

    print(
        f"  {training_data[DATE_COLUMN].min().date()}"
        f" -> "
        f"{training_data[DATE_COLUMN].max().date()}"
    )

    print(
        f"  Training rows: {len(training_data)}"
    )

    print(
        f"  Cutoff date: {cutoff_date.date()}"
    )

    print(
        f"  First protected test date: "
        f"{first_test_date.date()}"
    )

    return training_data


# ============================================================
# TRAIN IQ RECURSIVE XGBOOST MODEL
# ============================================================

def train_iq_xgboost(training_data):
    model = XGBRegressor(
        **XGB_PARAMS
    )

    model.fit(
        training_data[FORECAST_FEATURES],
        training_data[TARGET]
    )

    return model


# ============================================================
# TRAIN IQ SARIMA MODEL
# ============================================================

def train_iq_sarima(training_data):
    train_values = (
        training_data[TARGET]
        .astype(float)
        .values
    )

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

    return fitted_model


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 75)
    print("CareFlow - Phase 11")
    print("DengAI Model Persistence")
    print("=" * 75)

    print(
        f"\nLoading dataset:\n{DATA_PATH}"
    )

    data = load_data()
    test_split = load_test_split()

    print(
        f"\nDataset rows: {len(data)}"
    )

    print(
        f"Cities: "
        f"{sorted(data[CITY_COLUMN].unique())}"
    )

    print(
        "\nSelected persistent models:"
    )

    print(
        "  IQ -> Recursive XGBoost"
    )

    print(
        "  IQ -> SARIMA"
    )

    print(
        "  SJ -> Naive "
        "(no trainable artifact)"
    )

    # --------------------------------------------------------
    # IQ TRAINING DATA
    # --------------------------------------------------------

    iq_training_data = get_training_data(
        data,
        test_split,
        "iq"
    )

    # --------------------------------------------------------
    # IQ XGBOOST
    # --------------------------------------------------------

    print(
        "\nTraining IQ Recursive XGBoost model..."
    )

    iq_xgb_model = train_iq_xgboost(
        iq_training_data
    )

    iq_xgb_path = (
        ARTIFACT_DIR
        / "iq_xgboost.joblib"
    )

    save_model(
        iq_xgb_model,
        iq_xgb_path
    )

    print(
        f"Model saved: "
        f"{iq_xgb_path.relative_to(PROJECT_ROOT)}"
    )

    # --------------------------------------------------------
    # IQ SARIMA
    # --------------------------------------------------------

    print(
        "\nTraining IQ SARIMA model..."
    )

    iq_sarima_model = train_iq_sarima(
        iq_training_data
    )

    iq_sarima_path = (
        ARTIFACT_DIR
        / "iq_sarima.joblib"
    )

    save_model(
        iq_sarima_model,
        iq_sarima_path
    )

    print(
        f"Model saved: "
        f"{iq_sarima_path.relative_to(PROJECT_ROOT)}"
    )

    # --------------------------------------------------------
    # COMPLETION
    # --------------------------------------------------------

    print("\n" + "=" * 75)
    print("DengAI model persistence complete.")
    print("=" * 75)

    print(
        "\nArtifacts:"
    )

    print(
        "  - ml/artifacts/dengai/iq_xgboost.joblib"
    )

    print(
        "  - ml/artifacts/dengai/iq_sarima.joblib"
    )

    print(
        "\nSJ Naive requires no trained model artifact."
    )


if __name__ == "__main__":
    main()