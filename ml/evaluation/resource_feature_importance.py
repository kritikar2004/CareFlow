import pandas as pd
from xgboost import XGBRegressor


DATA_PATH = "ml/data/resource_features.csv"

EXCLUDE_COLUMNS = [
    "date",
    "resource_category",
    "resource_name",
    "unit",
    "quantity_used",
]


def main():
    df = pd.read_csv(DATA_PATH).dropna().copy()
    df["date"] = pd.to_datetime(df["date"])

    print("Top Resource Features")
    print("======================")

    for resource_name in sorted(df["resource_name"].unique()):
        resource_df = (
            df[df["resource_name"] == resource_name]
            .sort_values("date")
            .reset_index(drop=True)
        )

        feature_columns = [
            column
            for column in resource_df.columns
            if column not in EXCLUDE_COLUMNS
        ]

        n = len(resource_df)
        train_end = int(n * 0.70)

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
            resource_df[feature_columns].iloc[:train_end],
            resource_df["quantity_used"].iloc[:train_end],
        )

        importance = pd.Series(
            model.feature_importances_,
            index=feature_columns,
        ).sort_values(ascending=False)

        print(f"\n{resource_name}")
        print("----------------")
        print(importance.head(5).to_string())


if __name__ == "__main__":
    main()