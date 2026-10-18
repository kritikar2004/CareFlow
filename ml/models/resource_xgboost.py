import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error
from xgboost import XGBRegressor

from ml.models.model_persistence import save_model


DATA_PATH = "ml/data/resource_features.csv"

EXCLUDE_COLUMNS = [
    "date",
    "resource_category",
    "resource_name",
    "unit",
    "quantity_used",
]

TARGET = "quantity_used"


def calculate_metrics(y_true, y_pred):
    mae = mean_absolute_error(y_true, y_pred)
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))

    non_zero = y_true != 0

    if non_zero.any():
        mape = (
            np.mean(
                np.abs(
                    (y_true[non_zero] - y_pred[non_zero])
                    / y_true[non_zero]
                )
            )
            * 100
        )
    else:
        mape = np.nan

    return {
        "MAE": mae,
        "RMSE": rmse,
        "MAPE": mape,
    }


def main():
    # Load feature dataset
    df = pd.read_csv(DATA_PATH)

    # Remove rows without enough historical features
    df = df.dropna().copy()

    # Keep chronological order
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").reset_index(drop=True)

    # Process each resource separately
    resources = sorted(df["resource_name"].unique())

    for resource_name in resources:
        print("\n" + "=" * 60)
        print(f"Resource: {resource_name}")
        print("=" * 60)

        resource_df = (
            df[df["resource_name"] == resource_name]
            .copy()
            .sort_values("date")
            .reset_index(drop=True)
        )

        # Features and target
        feature_columns = [
            column
            for column in resource_df.columns
            if column not in EXCLUDE_COLUMNS
        ]

        X = resource_df[feature_columns]
        y = resource_df[TARGET]

        # Chronological split: 70% / 15% / 15%
        n = len(resource_df)
        train_end = int(n * 0.70)
        validation_end = int(n * 0.85)

        X_train = X.iloc[:train_end]
        y_train = y.iloc[:train_end]

        X_validation = X.iloc[train_end:validation_end]
        y_validation = y.iloc[train_end:validation_end]

        X_test = X.iloc[validation_end:]
        y_test = y.iloc[validation_end:]

        # XGBoost regression model
        model = XGBRegressor(
            objective="reg:squarederror",
            n_estimators=300,
            max_depth=4,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42,
        )

        # Train only on the training period
        model.fit(X_train, y_train)

        # Save one trained model artifact per resource
        artifact_path = (
            f"ml/artifacts/resources/{resource_name}_xgboost.joblib"
        )

        save_model(model, artifact_path)

        print(f"Model saved: {artifact_path}")

        # Validation evaluation
        validation_predictions = model.predict(X_validation)

        validation_metrics = calculate_metrics(
            y_validation,
            validation_predictions,
        )

        print("\nValidation")
        print("--------------------------------")
        print(f"MAE:  {validation_metrics['MAE']:.4f}")
        print(f"RMSE: {validation_metrics['RMSE']:.4f}")
        print(f"MAPE: {validation_metrics['MAPE']:.4f}%")

        # Final test evaluation
        test_predictions = model.predict(X_test)

        test_metrics = calculate_metrics(
            y_test,
            test_predictions,
        )

        print("\nTest")
        print("--------------------------------")
        print(f"MAE:  {test_metrics['MAE']:.4f}")
        print(f"RMSE: {test_metrics['RMSE']:.4f}")
        print(f"MAPE: {test_metrics['MAPE']:.4f}%")


if __name__ == "__main__":
    main()
