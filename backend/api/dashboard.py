from fastapi import APIRouter, Depends

from sqlalchemy.orm import Session

from backend.auth.dependencies import get_current_user, get_db
from backend.database.models import Dataset, Forecast, User


router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"],
)


@router.get("")
def get_dashboard(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # --------------------------------------------------------
    # CURRENT DATASETS
    # --------------------------------------------------------

    current_datasets = (
        db.query(Dataset)
        .filter(
            Dataset.user_id == current_user.id,
            Dataset.is_current.is_(True),
        )
        .order_by(Dataset.id.desc())
        .all()
    )

    history_dataset = next(
        (
            dataset
            for dataset in current_datasets
            if dataset.dataset_type == "hospital_history"
        ),
        None,
    )

    resources_dataset = next(
        (
            dataset
            for dataset in current_datasets
            if dataset.dataset_type == "hospital_resources"
        ),
        None,
    )

    # --------------------------------------------------------
    # DATASET RESPONSE
    # --------------------------------------------------------

    def serialize_dataset(dataset):
        if dataset is None:
            return None

        return {
            "id": dataset.id,
            "filename": dataset.filename,
            "dataset_type": dataset.dataset_type,
            "status": dataset.status,
            "is_current": dataset.is_current,
            "version_number": dataset.version_number,
            "upload_date": (
                dataset.upload_date.isoformat()
                if dataset.upload_date
                else None
            ),
            "start_date": (
                dataset.start_date.isoformat()
                if dataset.start_date
                else None
            ),
            "end_date": (
                dataset.end_date.isoformat()
                if dataset.end_date
                else None
            ),
        }

    # --------------------------------------------------------
    # CURRENT FORECASTS
    # --------------------------------------------------------

    admissions_forecast = None
    icu_forecast = None
    resource_forecasts = []

    if history_dataset:
        admissions_forecast = (
            db.query(Forecast)
            .filter(
                Forecast.user_id == current_user.id,
                Forecast.dataset_id == history_dataset.id,
                Forecast.forecast_type == "admissions",
            )
            .order_by(Forecast.id.desc())
            .first()
        )

        icu_forecast = (
            db.query(Forecast)
            .filter(
                Forecast.user_id == current_user.id,
                Forecast.dataset_id == history_dataset.id,
                Forecast.forecast_type == "icu",
            )
            .order_by(Forecast.id.desc())
            .first()
        )

    if resources_dataset:
        resource_forecasts = (
            db.query(Forecast)
            .filter(
                Forecast.user_id == current_user.id,
                Forecast.dataset_id == resources_dataset.id,
                Forecast.forecast_type == "resource",
            )
            .order_by(Forecast.id.desc())
            .all()
        )

    # --------------------------------------------------------
    # FORECAST SERIALIZATION
    # --------------------------------------------------------

    def serialize_forecast(forecast):
        if forecast is None:
            return None

        return {
            "id": forecast.id,
            "forecast_type": forecast.forecast_type,
            "horizon": forecast.horizon,
            "generated_at": (
                forecast.generated_at.isoformat()
                if forecast.generated_at
                else None
            ),
            "model_name": forecast.model_name,
            "model_version": forecast.model_version,
            "results": forecast.results,
            "performance_metrics": forecast.performance_metrics,
        }

    # --------------------------------------------------------
    # RESOURCE FORECASTS
    # --------------------------------------------------------

    serialized_resources = [
        serialize_forecast(forecast)
        for forecast in resource_forecasts
    ]

    # --------------------------------------------------------
    # DASHBOARD STATUS
    # --------------------------------------------------------

    history_ready = (
        history_dataset is not None
        and history_dataset.status == "processed"
    )

    resources_ready = (
        resources_dataset is not None
        and resources_dataset.status == "processed"
    )

    forecasts_available = (
        admissions_forecast is not None
        or icu_forecast is not None
        or len(resource_forecasts) > 0
    )

    # --------------------------------------------------------
    # RESPONSE
    # --------------------------------------------------------

    return {
        "hospital": {
            "id": current_user.id,
            "hospital_name": current_user.hospital_name,
            "phone": current_user.phone,
            "email": current_user.email,
            "city": current_user.city,
        },
        "datasets": {
            "hospital_history": serialize_dataset(history_dataset),
            "hospital_resources": serialize_dataset(resources_dataset),
            "history_ready": history_ready,
            "resources_ready": resources_ready,
        },
        "forecasts": {
            "admissions": serialize_forecast(admissions_forecast),
            "icu": serialize_forecast(icu_forecast),
            "resources": serialized_resources,
            "available": forecasts_available,
        },
        "status": {
            "ready": history_ready and resources_ready,
            "message": (
                "Hospital datasets are ready for CareFlow intelligence."
                if history_ready and resources_ready
                else (
                    "Upload and process the required hospital datasets "
                    "to generate hospital-specific forecasts."
                )
            ),
        },
        "disclaimer": (
            "Forecasts are estimates based on historical and public data. "
            "They should not be treated as clinical advice or as a "
            "substitute for professional healthcare decisions."
        ),
    }