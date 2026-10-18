import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error


DATA_PATH = "ml/data/resource_features.csv"


def main():
    df = pd.read_csv(DATA_PATH).dropna().copy()
    df["date"] = pd.to_datetime(df["date"])

    print("Resource Naive Baseline — Validation")
    print("--------------------------------------")

    for resource_name in df["resource_name"].unique():
        resource_df = (
            df[df["resource_name"] == resource_name]
            .sort_values("date")
            .reset_index(drop=True)
        )

        resource_df["naive_prediction"] = (
            resource_df["quantity_used"].shift(1)
        )

        n = len(resource_df)
        train_end = int(n * 0.70)
        validation_end = int(n * 0.85)

        validation = resource_df.iloc[
            train_end:validation_end
        ].dropna()

        y_true = validation["quantity_used"]
        y_pred = validation["naive_prediction"]

        mae = mean_absolute_error(y_true, y_pred)
        rmse = np.sqrt(mean_squared_error(y_true, y_pred))
        mape = np.mean(
            np.abs((y_true - y_pred) / y_true)
        ) * 100

        print(
            f"{resource_name}: "
            f"MAE={mae:.4f}, "
            f"RMSE={rmse:.4f}, "
            f"MAPE={mape:.4f}%"
        )


if __name__ == "__main__":
    main()