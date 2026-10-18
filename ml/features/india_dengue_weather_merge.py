from pathlib import Path

import pandas as pd


DENGUE_FILE = Path(
    "ml/data/processed/india_dengue_monthly.csv"
)

WEATHER_FILE = Path(
    "ml/data/processed/era5_pune_monthly.csv"
)

OUTPUT_FILE = Path(
    "ml/data/processed/maharashtra_dengue_weather_monthly.csv"
)


def main():
    # Load processed datasets.
    dengue_df = pd.read_csv(
        DENGUE_FILE,
        parse_dates=["date"]
    )

    weather_df = pd.read_csv(
        WEATHER_FILE,
        parse_dates=["date"]
    )

    # Keep Maharashtra only.
    maharashtra_df = dengue_df[
        dengue_df["state"] == "Maharashtra"
    ].copy()

    # Keep only the weather period overlapping
    # with the Maharashtra dengue dataset.
    weather_df = weather_df[
        weather_df["date"].between(
            maharashtra_df["date"].min(),
            maharashtra_df["date"].max()
        )
    ].copy()

    # Merge on monthly date.
    merged_df = maharashtra_df.merge(
        weather_df,
        on="date",
        how="inner",
        validate="one_to_one"
    )

    # Keep the state explicitly.
    merged_df["state"] = "Maharashtra"

    # Select the final column order.
    merged_df = merged_df[
        [
            "state",
            "date",
            "dengue_cases",
            "latitude",
            "longitude",
            "temperature_c",
            "precipitation_mm",
        ]
    ]

    # Sort chronologically.
    merged_df = merged_df.sort_values(
        "date"
    ).reset_index(drop=True)

    # Create output directory if needed.
    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    # Save merged dataset.
    merged_df.to_csv(
        OUTPUT_FILE,
        index=False
    )

    # Verification output.
    print("Created:", OUTPUT_FILE)
    print("Rows:", len(merged_df))
    print(
        "Columns:",
        merged_df.columns.tolist()
    )
    print(
        "Date range:",
        merged_df["date"].min().date(),
        "to",
        merged_df["date"].max().date()
    )
    print(
        "Missing values:",
        merged_df.isna().sum().sum()
    )
    print(
        "Duplicate dates:",
        merged_df["date"].duplicated().sum()
    )
    print(
        "Dengue cases range:",
        merged_df["dengue_cases"].min(),
        "to",
        merged_df["dengue_cases"].max()
    )
    print(
        "Temperature range (°C):",
        round(merged_df["temperature_c"].min(), 2),
        "to",
        round(merged_df["temperature_c"].max(), 2)
    )
    print(
        "Precipitation range (mm):",
        round(merged_df["precipitation_mm"].min(), 4),
        "to",
        round(merged_df["precipitation_mm"].max(), 4)
    )


if __name__ == "__main__":
    main()