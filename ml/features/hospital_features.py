import pandas as pd


def create_hospital_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Create leakage-safe time-series features for CareFlow hospital forecasting.

    The input DataFrame must contain:
    date, admissions, icu_demand, emergency_visits,
    avg_length_of_stay, outpatient_visits
    """

    data = df.copy()

    # Convert and sort by date
    data["date"] = pd.to_datetime(data["date"])
    data = data.sort_values("date").reset_index(drop=True)

    # Calendar features
    data["day_of_week"] = data["date"].dt.dayofweek
    data["day_of_month"] = data["date"].dt.day
    data["month"] = data["date"].dt.month
    data["week_of_year"] = data["date"].dt.isocalendar().week.astype(int)

    # Simple season indicator
    data["season"] = data["month"].map(
        {
            12: "winter",
            1: "winter",
            2: "winter",
            3: "spring",
            4: "spring",
            5: "spring",
            6: "summer",
            7: "summer",
            8: "summer",
            9: "autumn",
            10: "autumn",
            11: "autumn",
        }
    )

    # Lag features
    lag_columns = [
        "admissions",
        "icu_demand",
        "emergency_visits",
        "outpatient_visits",
    ]

    for column in lag_columns:
        for lag in [1, 7, 14, 30]:
            data[f"{column}_lag_{lag}"] = data[column].shift(lag)

    # Leakage-safe rolling features.
    # shift(1) ensures today's target is never included.
    for column in ["admissions", "icu_demand"]:
        shifted = data[column].shift(1)

        for window in [7, 14, 30]:
            data[f"{column}_rolling_mean_{window}"] = (
                shifted.rolling(window=window).mean()
            )

    return data