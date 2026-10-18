from pathlib import Path

import pandas as pd


INPUT_FILE = Path(
    "ml/data/processed/maharashtra_dengue_weather_monthly.csv"
)


def main():
    df = pd.read_csv(
        INPUT_FILE,
        parse_dates=["date"]
    )

    print("=== Maharashtra Dengue + Pune Weather Analysis ===")

    print("\nShape:")
    print(df.shape)

    print("\nDate range:")
    print(
        df["date"].min().date(),
        "to",
        df["date"].max().date()
    )

    print("\nData:")
    print(df.to_string(index=False))

    print("\nDescriptive statistics:")
    print(
        df[
            [
                "dengue_cases",
                "temperature_c",
                "precipitation_mm",
            ]
        ].describe().round(3)
    )

    print("\nCorrelation matrix:")
    print(
        df[
            [
                "dengue_cases",
                "temperature_c",
                "precipitation_mm",
            ]
        ]
        .corr()
        .round(3)
    )

    print("\nHighest dengue-case months:")
    print(
        df[
            [
                "date",
                "dengue_cases",
                "temperature_c",
                "precipitation_mm",
            ]
        ]
        .sort_values(
            "dengue_cases",
            ascending=False
        )
        .head(5)
        .to_string(index=False)
    )

    print("\nHighest precipitation months:")
    print(
        df[
            [
                "date",
                "dengue_cases",
                "temperature_c",
                "precipitation_mm",
            ]
        ]
        .sort_values(
            "precipitation_mm",
            ascending=False
        )
        .head(5)
        .to_string(index=False)
    )


if __name__ == "__main__":
    main()