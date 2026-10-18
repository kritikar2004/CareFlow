from pathlib import Path

import pandas as pd
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


def main():
    train = pd.read_csv(
        SPLIT_DIR / "train.csv"
    )

    city_mapping = {
        "iq": 0,
        "sj": 1,
    }

    train["city_encoded"] = train["city"].map(
        city_mapping
    )

    if train["city_encoded"].isna().any():
        raise ValueError(
            "Unknown city found in training data."
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
        train[FEATURES],
        train["total_cases"]
    )

    importance = pd.DataFrame(
        {
            "feature": FEATURES,
            "importance": model.feature_importances_,
        }
    )

    importance = importance.sort_values(
        "importance",
        ascending=False
    ).reset_index(drop=True)

    print("DengAI XGBoost Feature Importance")
    print("----------------------------------")
    print(
        importance.head(15).to_string(
            index=False
        )
    )


if __name__ == "__main__":
    main()