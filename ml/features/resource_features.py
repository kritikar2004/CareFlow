import pandas as pd


def create_resource_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Create leakage-safe features for resource demand forecasting.

    Features are generated separately for each resource_name.
    """

    data = df.copy()

    # Convert and sort dates
    data["date"] = pd.to_datetime(data["date"])
    data = data.sort_values(["resource_name", "date"]).reset_index(drop=True)

    # Calendar features
    data["day_of_week"] = data["date"].dt.dayofweek
    data["day_of_month"] = data["date"].dt.day
    data["month"] = data["date"].dt.month
    data["week_of_year"] = data["date"].dt.isocalendar().week.astype(int)

    # Create lag and rolling features separately for every resource.
    grouped = data.groupby("resource_name")["quantity_used"]

    for lag in [1, 7, 14, 30]:
        data[f"quantity_used_lag_{lag}"] = grouped.shift(lag)

    for window in [7, 14, 30]:
        data[f"quantity_used_rolling_mean_{window}"] = (
            grouped.shift(1)
            .rolling(window=window)
            .mean()
            .reset_index(level=0, drop=True)
        )

    return data