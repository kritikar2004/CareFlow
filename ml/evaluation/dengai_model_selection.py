"""
CareFlow Phase 10
DengAI Candidate Model Selection

Purpose:
- Record the validation-based candidate selection.
- Compare the already-tested candidates:
    1. Recursive XGBoost
    2. SARIMA
    3. Naive
- Do NOT access the final test set.
- Do NOT perform additional tuning.
"""

import pandas as pd


# ------------------------------------------------------------
# Validation results already obtained in Phase 10
# ------------------------------------------------------------

results = [
    # city, horizon, model, MAE, RMSE, MAPE

    # IQ - 1 week
    ("iq", "1_week", "Recursive XGBoost",
     1.9196, 1.9196, 12.7972),

    ("iq", "1_week", "SARIMA",
     6.5571, 6.5571, 43.7137),

    ("iq", "1_week", "Naive",
     6.0000, 6.0000, 40.0000),

    # IQ - 2 weeks
    ("iq", "2_weeks", "Recursive XGBoost",
     6.1002, 7.3952, 134.9078),

    ("iq", "2_weeks", "SARIMA",
     4.9117, 5.1800, 62.6874),

    ("iq", "2_weeks", "Naive",
     5.5000, 5.5227, 82.5000),

    # IQ - 4 weeks
    ("iq", "4_weeks", "Recursive XGBoost",
     8.5766, 9.4411, 497.9796),

    ("iq", "4_weeks", "SARIMA",
     4.8245, 4.9757, 216.0915),

    ("iq", "4_weeks", "Naive",
     7.0000, 7.1764, 321.6667),

    # SJ - 1 week
    ("sj", "1_week", "Recursive XGBoost",
     13.2811, 13.2811, 23.7162),

    ("sj", "1_week", "SARIMA",
     12.3169, 12.3169, 21.9945),

    ("sj", "1_week", "Naive",
     11.0000, 11.0000, 19.6429),

    # SJ - 2 weeks
    ("sj", "2_weeks", "Recursive XGBoost",
     26.2974, 29.3425, 38.0673),

    ("sj", "2_weeks", "SARIMA",
     22.3293, 24.4713, 32.5583),

    ("sj", "2_weeks", "Naive",
     20.5000, 22.5942, 29.8214),

    # SJ - 4 weeks
    ("sj", "4_weeks", "Recursive XGBoost",
     34.0288, 36.4517, 44.3171),

    ("sj", "4_weeks", "SARIMA",
     31.6594, 33.7564, 41.1225),

    ("sj", "4_weeks", "Naive",
     29.0000, 30.9597, 37.6370),
]


df = pd.DataFrame(
    results,
    columns=[
        "city",
        "horizon",
        "model",
        "mae",
        "rmse",
        "mape",
    ],
)


# ------------------------------------------------------------
# Select candidate using MAE as primary metric.
# RMSE and MAPE remain supporting metrics.
# ------------------------------------------------------------

selection = []

for (city, horizon), group in df.groupby(
    ["city", "horizon"]
):

    best_index = group["mae"].idxmin()

    best = group.loc[best_index]

    selection.append(
        {
            "city": city,
            "horizon": horizon,
            "selected_model": best["model"],
            "mae": best["mae"],
            "rmse": best["rmse"],
            "mape": best["mape"],
        }
    )


selection_df = pd.DataFrame(selection)


# ------------------------------------------------------------
# Display complete evidence
# ------------------------------------------------------------

print("=" * 80)
print("CARE FLOW - PHASE 10")
print("DengAI Validation Candidate Selection")
print("=" * 80)

print("\nAll validation results:\n")

print(
    df.to_string(index=False)
)


print("\n")
print("=" * 80)
print("SELECTED CANDIDATES")
print("=" * 80)

print(
    selection_df.to_string(index=False)
)


print("\n")
print("=" * 80)
print("SELECTION RULE")
print("=" * 80)

print(
    "Primary metric: MAE"
)

print(
    "RMSE and MAPE are retained as supporting metrics."
)

print(
    "Selection uses validation evidence only."
)

print(
    "The final DengAI test split is not accessed."
)

print(
    "No additional model tuning is performed."
)

print("\nPhase 10 candidate selection complete.")