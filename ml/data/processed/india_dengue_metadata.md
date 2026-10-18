# Indian Dengue Dataset — Processing Metadata

## Source

Dataset:
State/UT and Month-wise Dengue Cases during 2018 and 2019

Source organization:
Ministry of Health and Family Welfare, Government of India

Original raw file:
ml/data/raw/idsp/india_dengue_2018_2019.csv

## Purpose in CareFlow

This dataset is used for Indian dengue context and validation support.

It is NOT used as the primary training dataset for the CareFlow dengue forecasting model.

The primary disease forecasting development dataset is DengAI.

## Processing

Processing script:

ml/features/india_dengue_clean.py

Processed file:

ml/data/processed/india_dengue_monthly.csv

Transformation:

Original wide-format data:

State/UT | 2018-Jan | 2018-Feb | ... | 2019-Jun

was converted to:

state | date | dengue_cases

Yearly Total columns were excluded because they are aggregate values rather than individual time-series observations.

The India-wide `Total` row was excluded because it is an aggregate and not an individual state/UT.

`Not Reported` values were converted to missing (`NaN`).

`Not Reported` values were NOT converted to zero.

## Validation Results

Total states/UTs after processing: 35

Total records: 630

Coverage:
2018-01-01 to 2019-06-01

Records per state/UT:
18

Duplicate state-date records:
0

Negative dengue case values:
0

Unreported monthly values:
18

State with unreported values:
West Bengal

West Bengal has all 18 monthly observations marked as unreported.

## Limitations

The dataset covers only 18 months.

The data is state/UT-level rather than district-level.

Because of its limited time span, it is not suitable as the primary general-purpose dengue forecasting training dataset.

The unreported West Bengal observations must not be interpreted as zero dengue cases.

The dataset is therefore used for Indian disease context and supporting validation rather than primary model training.