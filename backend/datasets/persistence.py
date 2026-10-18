from datetime import datetime

from sqlalchemy.orm import Session

from backend.database.models import Forecast, TrainingRun

from backend.database.models import Forecast, ResourceRecord, TrainingRun

def save_training_run(
    db: Session,
    dataset_id: int,
    training_period_start,
    training_period_end,
    model_name: str,
    model_version: str,
    feature_schema_version: str,
    validation_metrics: dict,
    test_metrics: dict,
):
    training_run = TrainingRun(
        dataset_id=dataset_id,
        training_period_start=training_period_start,
        training_period_end=training_period_end,
        model_name=model_name,
        model_version=model_version,
        feature_schema_version=feature_schema_version,
        validation_metrics=validation_metrics,
        test_metrics=test_metrics,
        training_started_at=datetime.utcnow(),
        training_completed_at=datetime.utcnow(),
        status="completed",
    )

    db.add(training_run)
    db.commit()
    db.refresh(training_run)

    return training_run
def save_forecast(
    db: Session,
    user_id: int,
    dataset_id: int,
    training_run_id: int,
    forecast_type: str,
    horizon: int,
    model_name: str,
    model_version: str,
    results: dict,
    performance_metrics: dict,
):
    forecast = Forecast(
        user_id=user_id,
        dataset_id=dataset_id,
        training_run_id=training_run_id,
        forecast_type=forecast_type,
        horizon=horizon,
        generated_at=datetime.utcnow(),
        model_name=model_name,
        model_version=model_version,
        results=results,
        performance_metrics=performance_metrics,
    )

    db.add(forecast)
    db.commit()
    db.refresh(forecast)

    return forecast
def save_resource_records(
    db: Session,
    dataset_id: int,
    dataframe,
):
    records = []

    for row in dataframe.to_dict("records"):
        record = ResourceRecord(
            dataset_id=dataset_id,
            date=row["date"],
            resource_category=row["resource_category"],
            resource_name=row["resource_name"],
            unit=row["unit"],
            quantity_available=row["quantity_available"],
            quantity_used=row["quantity_used"],
            reference_capacity=row["reference_capacity"],
        )

        records.append(record)

    db.add_all(records)
    db.commit()

    return records