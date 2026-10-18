import os

from fastapi import APIRouter, Depends, HTTPException, Query, status

from sqlalchemy.orm import Session

from backend.auth.dependencies import get_current_user, get_db
from backend.database.models import Dataset, User
from backend.datasets.processor import forecast_resource, read_uploaded_csv


router = APIRouter(
    prefix="/bottleneck",
    tags=["Bottleneck"],
)


# Capacity-pressure thresholds are application configuration, not medical standards.
# Values can be overridden through environment variables.
DEFAULT_NORMAL_MAX_UTILIZATION = 80.0
DEFAULT_PRESSURE_MAX_UTILIZATION = 100.0


def _get_threshold(name: str, default: float) -> float:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default

    try:
        return float(raw_value)
    except ValueError as exc:
        raise RuntimeError(
            f"Invalid bottleneck configuration value for {name}."
        ) from exc


def get_pressure_category(utilization_pct: float) -> str:
    """
    Classify capacity pressure using configurable application thresholds.

    These categories are operational application labels, not universal
    medical standards.
    """
    normal_max = _get_threshold(
        "BOTTLENECK_NORMAL_MAX_UTILIZATION",
        DEFAULT_NORMAL_MAX_UTILIZATION,
    )
    pressure_max = _get_threshold(
        "BOTTLENECK_PRESSURE_MAX_UTILIZATION",
        DEFAULT_PRESSURE_MAX_UTILIZATION,
    )

    if normal_max >= pressure_max:
        raise RuntimeError(
            "BOTTLENECK_NORMAL_MAX_UTILIZATION must be lower than "
            "BOTTLENECK_PRESSURE_MAX_UTILIZATION."
        )

    if utilization_pct <= normal_max:
        return "Within Capacity"

    if utilization_pct <= pressure_max:
        return "Potential Capacity Pressure"

    return "Capacity Exceeded"


@router.get("")
def get_bottleneck(
    resource_name: str = Query(...),
    horizon: int = Query(7),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return resource forecast demand with capacity utilization/pressure."""
    if horizon not in (7, 14, 30):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Horizon must be one of: 7, 14, 30",
        )

    dataset = (
        db.query(Dataset)
        .filter(
            Dataset.user_id == current_user.id,
            Dataset.dataset_type == "hospital_resources",
            Dataset.is_current.is_(True),
            Dataset.status.in_(["uploaded", "processed"]),
        )
        .order_by(Dataset.id.desc())
        .first()
    )

    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No current hospital resources dataset found for this user.",
        )

    try:
        dataframe = read_uploaded_csv(dataset.file_path)
        forecast_result = forecast_resource(
            dataframe,
            resource_name,
            horizon,
        )
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Uploaded resource dataset file could not be found.",
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        )
    except RuntimeError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to generate bottleneck analysis due to a server configuration error.",
        )

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to generate bottleneck analysis due to an internal server error.",
        )

    resource_data = dataframe[
        dataframe["resource_name"].astype(str).str.strip()
        == str(resource_name).strip()
    ].copy()

    if resource_data.empty:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"No data found for resource: {resource_name}",
        )

    resource_data = resource_data.sort_values("date").reset_index(drop=True)

    reference_capacity = float(resource_data["reference_capacity"].iloc[-1])
    unit = str(resource_data["unit"].iloc[-1])

    if reference_capacity <= 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                f"Reference capacity for resource '{resource_name}' "
                "must be greater than zero."
            ),
        )

    bottleneck_predictions = []

    for prediction in forecast_result["predictions"]:
        forecast_demand = float(prediction["predicted_value"])
        utilization_pct = (forecast_demand / reference_capacity) * 100.0

        bottleneck_predictions.append(
            {
                "date": prediction["date"],
                "forecast_demand": forecast_demand,
                "reference_capacity": reference_capacity,
                "utilization_pct": round(utilization_pct, 2),
                "pressure_category": get_pressure_category(utilization_pct),
            }
        )

    return {
        "resource_name": resource_name,
        "unit": unit,
        "horizon": horizon,
        "dataset": {
            "id": dataset.id,
            "version": dataset.version_number,
        },
        "model": {
            "name": forecast_result["model_name"],
            "version": forecast_result["model_version"],
        },
        "predictions": bottleneck_predictions,
        "disclaimer": (
            "Pressure categories use configurable application thresholds "
            "and are not universal medical standards."
        ),
    }
