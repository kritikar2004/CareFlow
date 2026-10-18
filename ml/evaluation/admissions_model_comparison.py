import pandas as pd
import numpy as np
from xgboost import XGBRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error


DATA_PATH = "ml/data/hospital_features.csv"

TARGET = "admissions"

FEATURES = [
    "day_of_week",
    "day_of_month",
    "month",
    "week_of_year",
    "season",

    "admissions_lag_1",
    "admissions_lag_7",
    "admissions_lag_14",
    "admissions_lag_30",

    "icu_demand_lag_1",
    "icu_demand_lag_7",
    "icu_demand_lag_14",
    "icu_demand_lag_30",

    "emergency_visits_lag_1",
    "emergency_visits_lag_7",
    "emergency_visits_lag_14",
    "emergency_visits_lag_30",

    "outpatient_visits_lag_1",
    "outpatient_visits_lag_7",
    "outpatient_visits_lag_14",
    "outpatient_visits_lag_30",

    "admissions_rolling_mean_7",
    "admissions_rolling_mean_14",
    "admissions_rolling_mean_30",

    "icu_demand_rolling_mean_7",
    "icu_demand_rolling_mean_14",
    "icu_demand_rolling_mean_30",
]


def calculate_metrics(actual, predicted):
    mae = mean_absolute_error(actual, predicted)
    rmse = np.sqrt(mean_squared_error(actual, predicted))

    non_zero = actual != 0

    if non_zero.any():
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
    # --------------------------------------------------
    # Load data
    # --------------------------------------------------
    df = pd.read_csv(
        DATA_PATH,
        parse_dates=["date"]
    )

    df = df.sort_values("date").reset_index(drop=True)

    # --------------------------------------------------
    # Encode season for XGBoost
    # Actual values in the dataset:
    # autumn, winter, spring, summer
    # --------------------------------------------------
    season_mapping = {
        "winter": 0,
        "spring": 1,
        "summer": 2,
        "autumn": 3
    }

    df["season"] = df["season"].map(season_mapping)

    if df["season"].isna().any():
        raise ValueError(
            "Unknown season value found after encoding."
        )

    # --------------------------------------------------
    # Remove rows with unavailable engineered features
    # --------------------------------------------------
    df = df.dropna(
        subset=FEATURES + [TARGET]
    ).reset_index(drop=True)

    # --------------------------------------------------
    # Chronological 70 / 15 / 15 split
    # --------------------------------------------------
    total_rows = len(df)

    train_end = int(total_rows * 0.70)
    val_end = int(total_rows * 0.85)

    train = df.iloc[:train_end]
    validation = df.iloc[train_end:val_end]
    test = df.iloc[val_end:]

    y_train = train[TARGET]
    y_val = validation[TARGET]
    y_test = test[TARGET]

    # --------------------------------------------------
    # 1. Naive baseline
    # Previous day's admissions
    # --------------------------------------------------
    naive_val = validation["admissions_lag_1"].values
    naive_test = test["admissions_lag_1"].values

    naive_val_metrics = calculate_metrics(
        y_val.values,
        naive_val
    )

    naive_test_metrics = calculate_metrics(
        y_test.values,
        naive_test
    )

    # --------------------------------------------------
    # 2. Seasonal Naive
    # Previous week's admissions
    # --------------------------------------------------
    seasonal_val = validation["admissions_lag_7"].values
    seasonal_test = test["admissions_lag_7"].values

    seasonal_val_metrics = calculate_metrics(
        y_val.values,
        seasonal_val
    )

    seasonal_test_metrics = calculate_metrics(
        y_test.values,
        seasonal_test
    )

    # --------------------------------------------------
    # 3. XGBoost
    # --------------------------------------------------
    model = XGBRegressor(
        objective="reg:squarederror",
        n_estimators=300,
        max_depth=4,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42
    )

    model.fit(
        train[FEATURES],
        y_train
    )

    xgb_val = model.predict(
        validation[FEATURES]
    )

    xgb_test = model.predict(
        test[FEATURES]
    )

    xgb_val_metrics = calculate_metrics(
        y_val.values,
        xgb_val
    )

    xgb_test_metrics = calculate_metrics(
        y_test.values,
        xgb_test
    )

    # --------------------------------------------------
    # Print comparison
    # --------------------------------------------------
    print("\nAdmissions Model Comparison")
    print("===========================")

    print("\nValidation")
    print("-----------------------------------------------")
    print(
        f"{'Model':<20}"
        f"{'MAE':>10}"
        f"{'RMSE':>10}"
        f"{'MAPE':>12}"
    )
    print("-----------------------------------------------")

    print(
        f"{'Naive':<20}"
        f"{naive_val_metrics[0]:>10.4f}"
        f"{naive_val_metrics[1]:>10.4f}"
        f"{naive_val_metrics[2]:>11.4f}%"
    )

    print(
        f"{'Seasonal Naive':<20}"
        f"{seasonal_val_metrics[0]:>10.4f}"
        f"{seasonal_val_metrics[1]:>10.4f}"
        f"{seasonal_val_metrics[2]:>11.4f}%"
    )

    print(
        f"{'XGBoost':<20}"
        f"{xgb_val_metrics[0]:>10.4f}"
        f"{xgb_val_metrics[1]:>10.4f}"
        f"{xgb_val_metrics[2]:>11.4f}%"
    )

    print("\nTest")
    print("-----------------------------------------------")
    print(
        f"{'Model':<20}"
        f"{'MAE':>10}"
        f"{'RMSE':>10}"
        f"{'MAPE':>12}"
    )
    print("-----------------------------------------------")

    print(
        f"{'Naive':<20}"
        f"{naive_test_metrics[0]:>10.4f}"
        f"{naive_test_metrics[1]:>10.4f}"
        f"{naive_test_metrics[2]:>11.4f}%"
    )

    print(
        f"{'Seasonal Naive':<20}"
        f"{seasonal_test_metrics[0]:>10.4f}"
        f"{seasonal_test_metrics[1]:>10.4f}"
        f"{seasonal_test_metrics[2]:>11.4f}%"
    )

    print(
        f"{'XGBoost':<20}"
        f"{xgb_test_metrics[0]:>10.4f}"
        f"{xgb_test_metrics[1]:>10.4f}"
        f"{xgb_test_metrics[2]:>11.4f}%"
    )

    # --------------------------------------------------
    # Print split information
    # --------------------------------------------------
    print("\nData Split")
    print("-----------------------------------------------")
    print(f"Train rows:      {len(train)}")
    print(f"Validation rows: {len(validation)}")
    print(f"Test rows:       {len(test)}")

    print("\nDate Ranges")
    print("-----------------------------------------------")

    print(
        f"Train:      "
        f"{train['date'].min().date()} "
        f"to "
        f"{train['date'].max().date()}"
    )

    print(
        f"Validation: "
        f"{validation['date'].min().date()} "
        f"to "
        f"{validation['date'].max().date()}"
    )

    print(
        f"Test:       "
        f"{test['date'].min().date()} "
        f"to "
        f"{test['date'].max().date()}"
    )


if __name__ == "__main__":
    main()