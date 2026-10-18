from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error
from xgboost import XGBRegressor


SPLIT_DIR = Path("ml/data/processed/dengai_split")


FEATURES = [
    "year",
    "weekofyear",
    "ndvi_ne",
    "ndvi_nw",
    "ndvi_se",
    "ndvi_sw",
    "precipitation_amt_mm",
    "reanalysis_air_temp_k",
    "reanalysis_avg_temp_k",
    "reanalysis_dew_point_temp_k",
    "reanalysis_max_air_temp_k",
    "reanalysis_min_air_temp_k",
    "reanalysis_precip_amt_kg_per_m2",
    "reanalysis_relative_humidity_percent",
    "reanalysis_sat_precip_amt_mm",
    "reanalysis_specific_humidity_g_per_kg",
    "reanalysis_tdtr_k",
    "station_avg_temp_c",
    "station_diur_temp_rng_c",
    "station_max_temp_c",
    "station_min_temp_c",
    "station_precip_mm",
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
                    (actual[non_zero] - predicted[non_zero])
                    / actual[non_zero]
                )
            )
            * 100
        )
    else:
        mape = np.nan

    return mae, rmse, mape


def add_city_encoding(data):
    city_mapping = {
        "iq": 0,
        "sj": 1,
    }

    data = data.copy()

    data["city_encoded"] = data["city"].map(
        city_mapping
    )

    if data["city_encoded"].isna().any():
        unknown_cities = (
            data.loc[
                data["city_encoded"].isna(),
                "city"
            ]
            .unique()
            .tolist()
        )

        raise ValueError(
            f"Unknown city found: {unknown_cities}"
        )

    return data


def evaluate(model, data, name):
    actual = data["total_cases"].to_numpy()

    predicted = model.predict(
        data[FEATURES]
    )

    mae, rmse, mape = calculate_metrics(
        actual,
        predicted
    )

    print(f"\n{name}")
    print(f"Rows: {len(data)}")
    print(f"MAE: {mae:.4f}")
    print(f"RMSE: {rmse:.4f}")
    print(f"MAPE: {mape:.4f}%")

    return mae, rmse, mape


def main():
    train = pd.read_csv(
        SPLIT_DIR / "train.csv"
    )

    validation = pd.read_csv(
        SPLIT_DIR / "validation.csv"
    )

    test = pd.read_csv(
        SPLIT_DIR / "test.csv"
    )

    # Encode city so the model can distinguish
    # between Iquitos and San Juan.
    train = add_city_encoding(train)
    validation = add_city_encoding(validation)
    test = add_city_encoding(test)

    print("City encoding:")
    print("iq -> 0")
    print("sj -> 1")

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
        train[FEATURES],
        train["total_cases"]
    )

    print("\nDengAI XGBoost model trained.")

    # Validation evaluation
    evaluate(
        model,
        validation,
        "Combined Validation"
    )

    for city in sorted(
        validation["city"].unique()
    ):
        city_data = validation[
            validation["city"] == city
        ]

        evaluate(
            model,
            city_data,
            f"Validation - {city}"
        )

    # Final test evaluation
    print("\nFinal Test Evaluation")

    evaluate(
        model,
        test,
        "Combined Test"
    )

    for city in sorted(
        test["city"].unique()
    ):
        city_data = test[
            test["city"] == city
        ]

        evaluate(
            model,
            city_data,
            f"Test - {city}"
        )


if __name__ == "__main__":
    main()