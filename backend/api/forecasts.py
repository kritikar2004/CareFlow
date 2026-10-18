from fastapi import APIRouter, Depends, HTTPException, Query, status

from sqlalchemy.orm import Session

from backend.auth.dependencies import get_current_user, get_db
from backend.database.models import Dataset, Forecast, TrainingRun, User

from backend.datasets.persistence import save_forecast

from backend.datasets.processor import (
    forecast_hospital,
    forecast_resource,
    read_uploaded_csv,
)

from backend.forecasting.disease import forecast_disease
from backend.forecasting.disease import (
    forecast_disease,
    get_disease_history_info,
)


router = APIRouter(
    prefix="/forecast",
    tags=["Forecast"],
)


# ============================================================
# ADMISSIONS FORECAST
# ============================================================

@router.get("/admissions")
def get_admissions_forecast(
    horizon: int = Query(
        default=7,
        description="Forecast horizon in days: 7, 14, or 30.",
    ),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if horizon not in {7, 14, 30}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Horizon must be one of: 7, 14, 30 days.",
        )

    dataset = (
        db.query(Dataset)
        .filter(
            Dataset.user_id == current_user.id,
            Dataset.dataset_type == "hospital_history",
            Dataset.is_current.is_(True),
            Dataset.status == "processed",
        )
        .first()
    )

    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                "Hospital history dataset is required. "
                "Please upload and process a hospital history dataset first."
            ),
        )

    try:
        dataframe = read_uploaded_csv(dataset.file_path)

        forecast_result = forecast_hospital(
            dataframe,
            "admissions",
            horizon,
        )

    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Uploaded hospital history dataset file could not be found.",
        ) from exc

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unable to generate admissions forecast: {exc}",
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to generate admissions forecast due to an internal server error.",
        ) from exc

    # --------------------------------------------------------
    # FIND THE CORRECT ADMISSIONS TRAINING RUN
    # --------------------------------------------------------

    source_forecast = (
        db.query(Forecast)
        .filter(
            Forecast.user_id == current_user.id,
            Forecast.dataset_id == dataset.id,
            Forecast.forecast_type == "admissions",
        )
        .order_by(Forecast.id.desc())
        .first()
    )

    if not source_forecast or not source_forecast.training_run_id:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Admissions training run provenance could not be found.",
        )

    training_run = (
        db.query(TrainingRun)
        .filter(
            TrainingRun.id == source_forecast.training_run_id,
            TrainingRun.dataset_id == dataset.id,
            TrainingRun.status == "completed",
        )
        .first()
    )

    if not training_run:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Admissions training run provenance could not be found.",
        )

    # --------------------------------------------------------
    # CHECK FOR EXISTING FORECAST
    # --------------------------------------------------------

    existing_forecast = (
        db.query(Forecast)
        .filter(
            Forecast.user_id == current_user.id,
            Forecast.dataset_id == dataset.id,
            Forecast.forecast_type == "admissions",
            Forecast.horizon == horizon,
        )
        .first()
    )

    if existing_forecast:
        forecast_record = existing_forecast
    else:
        forecast_record = save_forecast(
            db=db,
            user_id=current_user.id,
            dataset_id=dataset.id,
            training_run_id=training_run.id,
            forecast_type="admissions",
            horizon=horizon,
            model_name=forecast_result["model_name"],
            model_version=forecast_result["model_version"],
            results={
                "predictions": forecast_result["predictions"],
            },
            performance_metrics={
                "validation": forecast_result["validation_metrics"],
                "test": forecast_result["test_metrics"],
            },
        )

    return {
        "forecast_type": "admissions",
        "horizon": horizon,
        "dataset": {
            "id": dataset.id,
            "version_number": dataset.version_number,
            "filename": dataset.filename,
            "start_date": dataset.start_date,
            "end_date": dataset.end_date,
        },
        "model": {
            "name": forecast_result["model_name"],
            "version": forecast_result["model_version"],
        },
        "predictions": forecast_result["predictions"],
        "performance_metrics": {
            "validation": forecast_result["validation_metrics"],
            "test": forecast_result["test_metrics"],
        },
        "training_period": {
            "start_date": forecast_result["training_period_start"],
            "end_date": forecast_result["training_period_end"],
        },
        "disclaimer": (
            "Forecasts are estimates generated from the available "
            "hospital data and should support, not replace, clinical "
            "or operational judgment."
        ),
    }


# ============================================================
# ICU FORECAST
# ============================================================

@router.get("/icu")
def get_icu_forecast(
    horizon: int = Query(
        default=7,
        description="Forecast horizon in days: 7, 14, or 30.",
    ),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if horizon not in {7, 14, 30}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Horizon must be one of: 7, 14, or 30 days.",
        )

    dataset = (
        db.query(Dataset)
        .filter(
            Dataset.user_id == current_user.id,
            Dataset.dataset_type == "hospital_history",
            Dataset.is_current.is_(True),
            Dataset.status.in_(["uploaded", "processed"]),
        )
        .order_by(Dataset.id.desc())
        .first()
    )

    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No current hospital history dataset found for this user.",
        )

    try:
        dataframe = read_uploaded_csv(dataset.file_path)

        forecast_result = forecast_hospital(
            dataframe,
            "icu_demand",
            horizon,
        )

    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Uploaded hospital history dataset file could not be found.",
        ) from exc

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unable to generate ICU forecast: {exc}",
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to generate ICU forecast due to an internal server error.",
        ) from exc

    # --------------------------------------------------------
    # FIND THE CORRECT ICU TRAINING RUN
    # --------------------------------------------------------

    source_forecast = (
        db.query(Forecast)
        .filter(
            Forecast.user_id == current_user.id,
            Forecast.dataset_id == dataset.id,
            Forecast.forecast_type == "icu",
        )
        .order_by(Forecast.id.desc())
        .first()
    )

    if not source_forecast or not source_forecast.training_run_id:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="No persisted ICU training provenance found for this dataset.",
        )

    training_run = (
        db.query(TrainingRun)
        .filter(
            TrainingRun.id == source_forecast.training_run_id,
            TrainingRun.dataset_id == dataset.id,
            TrainingRun.status == "completed",
        )
        .first()
    )

    if not training_run:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="ICU training run provenance could not be resolved.",
        )

    # --------------------------------------------------------
    # CHECK FOR EXISTING FORECAST
    # --------------------------------------------------------

    existing_forecast = (
        db.query(Forecast)
        .filter(
            Forecast.user_id == current_user.id,
            Forecast.dataset_id == dataset.id,
            Forecast.forecast_type == "icu",
            Forecast.horizon == horizon,
        )
        .first()
    )

    if existing_forecast:
        forecast_record = existing_forecast
    else:
        forecast_record = save_forecast(
            db=db,
            user_id=current_user.id,
            dataset_id=dataset.id,
            training_run_id=training_run.id,
            forecast_type="icu",
            horizon=horizon,
            model_name=training_run.model_name,
            model_version=training_run.model_version,
            results={
                "predictions": forecast_result["predictions"],
            },
            performance_metrics={
                "validation": forecast_result["validation_metrics"],
                "test": forecast_result["test_metrics"],
            },
        )

    return {
        "forecast_type": "icu",
        "horizon": horizon,
        "dataset": {
            "id": dataset.id,
            "version": dataset.version_number,
            "filename": dataset.filename,
            "start_date": dataset.start_date,
            "end_date": dataset.end_date,
        },
        "model": {
            "name": training_run.model_name,
            "version": training_run.model_version,
        },
        "predictions": forecast_result["predictions"],
        "performance_metrics": {
            "validation": forecast_result["validation_metrics"],
            "test": forecast_result["test_metrics"],
        },
        "training_period": {
            "start": forecast_result["training_period_start"],
            "end": forecast_result["training_period_end"],
        },
        "disclaimer": (
            "Forecasts are generated from the currently selected hospital "
            "dataset and should support, not replace, clinical and operational judgment."
        ),
    }


# ============================================================
# RESOURCE FORECAST
# ============================================================

@router.get("/resources")
def get_resource_forecast(
    resource_name: str = Query(...),
    horizon: int = Query(7),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
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

    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Uploaded resource dataset file could not be found.",
        ) from exc

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unable to generate resource forecast: {exc}",
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to generate resource forecast due to an internal server error.",
        ) from exc

    # --------------------------------------------------------
    # FIND THE CORRECT RESOURCE TRAINING RUN
    # --------------------------------------------------------

    resource_forecasts = (
        db.query(Forecast)
        .filter(
            Forecast.user_id == current_user.id,
            Forecast.dataset_id == dataset.id,
            Forecast.forecast_type == "resource",
        )
        .order_by(Forecast.id.desc())
        .all()
    )

    source_forecast = next(
        (
            forecast
            for forecast in resource_forecasts
            if isinstance(forecast.results, dict)
            and forecast.results.get("resource_name") == resource_name
        ),
        None,
    )

    if not source_forecast or not source_forecast.training_run_id:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                f"No persisted training provenance found for resource "
                f"'{resource_name}'."
            ),
        )

    training_run = (
        db.query(TrainingRun)
        .filter(
            TrainingRun.id == source_forecast.training_run_id,
            TrainingRun.dataset_id == dataset.id,
            TrainingRun.status == "completed",
        )
        .first()
    )

    if not training_run:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                f"Training run provenance could not be resolved for "
                f"resource '{resource_name}'."
            ),
        )

    # --------------------------------------------------------
    # CHECK FOR EXISTING FORECAST
    # --------------------------------------------------------

    resource_horizon_forecasts = (
        db.query(Forecast)
        .filter(
            Forecast.user_id == current_user.id,
            Forecast.dataset_id == dataset.id,
            Forecast.forecast_type == "resource",
            Forecast.horizon == horizon,
        )
        .all()
    )

    existing_forecast = next(
        (
            forecast
            for forecast in resource_horizon_forecasts
            if isinstance(forecast.results, dict)
            and forecast.results.get("resource_name") == resource_name
        ),
        None,
    )

    if existing_forecast:
        forecast_record = existing_forecast
    else:
        forecast_record = save_forecast(
            db=db,
            user_id=current_user.id,
            dataset_id=dataset.id,
            training_run_id=training_run.id,
            forecast_type="resource",
            horizon=horizon,
            model_name=forecast_result["model_name"],
            model_version=forecast_result["model_version"],
            results={
                "predictions": forecast_result["predictions"],
                "resource_name": resource_name,
            },
            performance_metrics={
                "validation": forecast_result["validation_metrics"],
                "test": forecast_result["test_metrics"],
            },
        )

    return {
        "forecast_type": "resource",
        "resource_name": resource_name,
        "horizon": horizon,
        "dataset": {
            "id": dataset.id,
            "version": dataset.version_number,
            "filename": dataset.filename,
            "start_date": dataset.start_date,
            "end_date": dataset.end_date,
        },
        "model": {
            "name": forecast_result["model_name"],
            "version": forecast_result["model_version"],
        },
        "predictions": forecast_result["predictions"],
        "performance_metrics": {
            "validation": forecast_result["validation_metrics"],
            "test": forecast_result["test_metrics"],
        },
        "training_period": {
            "start": forecast_result["training_period_start"],
            "end": forecast_result["training_period_end"],
        },
        "disclaimer": (
            "Resource forecasts are estimates generated from the available "
            "hospital resource data and should support, not replace, "
            "operational judgment."
        ),
    }


# ============================================================
# DISEASE FORECAST - PHASE 20
# ============================================================

@router.get("/disease")
def get_disease_forecast(
    disease: str = Query(
        ...,
        min_length=1,
        description="Disease name to forecast.",
    ),
    horizon: int = Query(
        default=7,
        description="Forecast horizon in days: 7, 14, or 30.",
    ),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Generate a forecast for one disease from the authenticated
    hospital's current disease_data dataset.

    Each disease is forecast independently using the Phase 20
    disease forecasting pipeline.
    """

    if horizon not in {7, 14, 30}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Horizon must be one of: 7, 14, 30 days.",
        )

    requested_disease = disease.strip()

    if not requested_disease:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Disease name is required.",
        )

    # --------------------------------------------------------
    # FIND CURRENT HOSPITAL DISEASE DATASET
    # --------------------------------------------------------

    dataset = (
        db.query(Dataset)
        .filter(
            Dataset.user_id == current_user.id,
            Dataset.dataset_type == "disease_data",
            Dataset.is_current.is_(True),
            Dataset.status == "processed",
        )
        .order_by(Dataset.id.desc())
        .first()
    )

    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                "Disease dataset is required. "
                "Please upload and process a disease dataset first."
            ),
        )

    # --------------------------------------------------------
    # READ UPLOADED DATASET
    # --------------------------------------------------------

    try:
        dataframe = read_uploaded_csv(dataset.file_path)

    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Uploaded disease dataset file could not be found.",
        ) from exc

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unable to read disease dataset: {exc}",
        ) from exc

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to read disease dataset due to an internal server error.",
        )

    # --------------------------------------------------------
    # GENERATE DISEASE FORECAST
    # --------------------------------------------------------

    try:
        forecast_result = forecast_disease(
            dataframe=dataframe,
            disease=requested_disease,
            horizon=horizon,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unable to generate disease forecast: {exc}",
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to generate disease forecast due to an internal server error.",
        ) from exc

    # --------------------------------------------------------
    # LIMITED / UNAVAILABLE FORECAST
    # --------------------------------------------------------

    if not forecast_result.get("available", False):
        return {
            "forecast_type": "disease",
            "status": forecast_result.get("status", "limited"),
            "available": False,
            "disease": requested_disease,
            "horizon": horizon,
            "dataset": {
                "id": dataset.id,
                "version_number": dataset.version_number,
                "filename": dataset.filename,
                "start_date": dataset.start_date,
                "end_date": dataset.end_date,
            },
            "predictions": [],
            "history": forecast_result.get("history"),
            "reason": forecast_result.get("reason"),
            "disclaimer": forecast_result.get("disclaimer"),
        }

    # --------------------------------------------------------
    # FIND EXISTING DISEASE FORECAST FOR THIS DATASET/DISEASE
    # --------------------------------------------------------

    disease_forecasts = (
        db.query(Forecast)
        .filter(
            Forecast.user_id == current_user.id,
            Forecast.dataset_id == dataset.id,
            Forecast.forecast_type == "disease",
            Forecast.horizon == horizon,
        )
        .order_by(Forecast.id.desc())
        .all()
    )

    source_forecast = next(
        (
            forecast
            for forecast in disease_forecasts
            if isinstance(forecast.results, dict)
            and str(forecast.results.get("disease", "")).strip().casefold()
            == requested_disease.casefold()
        ),
        None,
    )

    # --------------------------------------------------------
    # RESOLVE TRAINING RUN PROVENANCE
    # --------------------------------------------------------

    training_run = None

    if source_forecast and source_forecast.training_run_id:
        training_run = (
            db.query(TrainingRun)
            .filter(
                TrainingRun.id == source_forecast.training_run_id,
                TrainingRun.dataset_id == dataset.id,
                TrainingRun.status == "completed",
            )
            .first()
        )

    # --------------------------------------------------------
    # SAVE FORECAST IF NOT ALREADY PERSISTED
    # --------------------------------------------------------

    if not source_forecast:
        # The upload pipeline stores one Forecast per disease.
        # Find its persisted training run by matching the disease.
        disease_forecast_candidates = (
            db.query(Forecast)
            .filter(
                Forecast.user_id == current_user.id,
                Forecast.dataset_id == dataset.id,
                Forecast.forecast_type == "disease",
            )
            .order_by(Forecast.id.desc())
            .all()
        )

        source_forecast = next(
            (
                forecast
                for forecast in disease_forecast_candidates
                if isinstance(forecast.results, dict)
                and str(forecast.results.get("disease", "")).strip().casefold()
                == requested_disease.casefold()
            ),
            None,
        )

        if source_forecast and source_forecast.training_run_id:
            training_run = (
                db.query(TrainingRun)
                .filter(
                    TrainingRun.id == source_forecast.training_run_id,
                    TrainingRun.dataset_id == dataset.id,
                    TrainingRun.status == "completed",
                )
                .first()
            )

    if source_forecast is None:
        # This can happen when the API is called for a valid disease
        # and horizon that was not persisted during upload.
        #
        # Phase 20 still requires provenance for API-generated forecasts,
        # so create a TrainingRun using the exact metadata returned by
        # the disease forecasting pipeline.
        from backend.datasets.persistence import save_training_run

        training_run = save_training_run(
            db=db,
            dataset_id=dataset.id,
            training_period_start=forecast_result["training_period_start"],
            training_period_end=forecast_result["training_period_end"],
            model_name=forecast_result["model_name"],
            model_version=forecast_result["model_version"],
            feature_schema_version=forecast_result["feature_schema_version"],
            validation_metrics=forecast_result["validation_metrics"],
            test_metrics=forecast_result["test_metrics"],
        )

        source_forecast = save_forecast(
            db=db,
            user_id=current_user.id,
            dataset_id=dataset.id,
            training_run_id=training_run.id,
            forecast_type="disease",
            horizon=horizon,
            model_name=forecast_result["model_name"],
            model_version=forecast_result["model_version"],
            results={
                "predictions": forecast_result["predictions"],
                "disease": requested_disease,
            },
            performance_metrics={
                "validation": forecast_result["validation_metrics"],
                "test": forecast_result["test_metrics"],
            },
        )

    elif training_run is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Disease training run provenance could not be resolved.",
        )

    # --------------------------------------------------------
    # RESPONSE
    # --------------------------------------------------------

    return {
        "forecast_type": "disease",
        "status": forecast_result["status"],
        "available": True,
        "disease": forecast_result["disease"],
        "horizon": horizon,
        "dataset": {
            "id": dataset.id,
            "version_number": dataset.version_number,
            "filename": dataset.filename,
            "start_date": dataset.start_date,
            "end_date": dataset.end_date,
        },
        "model": {
            "name": forecast_result["model_name"],
            "version": forecast_result["model_version"],
            "feature_schema_version": forecast_result[
                "feature_schema_version"
            ],
        },
        "predictions": forecast_result["predictions"],
        "performance_metrics": {
            "validation": forecast_result["validation_metrics"],
            "test": forecast_result["test_metrics"],
        },
        "training_period": {
            "start_date": forecast_result["training_period_start"],
            "end_date": forecast_result["training_period_end"],
        },
        "history": forecast_result["history"],
        "disclaimer": forecast_result["disclaimer"],
    }
# ============================================================
# DISEASE FORECAST - PHASE 20
# ============================================================
# ============================================================
# AVAILABLE DISEASES
# ============================================================

@router.get("/disease/available")
def get_available_diseases(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Return the diseases available in the authenticated hospital's
    current processed disease dataset.

    This endpoint performs discovery only. It does not train models,
    generate forecasts, or create Forecast/TrainingRun records.
    """

    dataset = (
        db.query(Dataset)
        .filter(
            Dataset.user_id == current_user.id,
            Dataset.dataset_type == "disease_data",
            Dataset.is_current.is_(True),
            Dataset.status == "processed",
        )
        .order_by(Dataset.id.desc())
        .first()
    )

    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                "Disease dataset is required. "
                "Please upload and process a disease dataset first."
            ),
        )

    try:
        dataframe = read_uploaded_csv(dataset.file_path)
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Uploaded disease dataset file could not be found.",
        ) from exc

    required_columns = {"date", "disease", "cases"}

    missing = required_columns - set(dataframe.columns)

    if missing:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                "Disease dataset is missing required columns: "
                f"{sorted(missing)}"
            ),
        )

    disease_names = sorted(
        {
            str(value).strip()
            for value in dataframe["disease"].dropna()
            if str(value).strip()
        },
        key=str.casefold,
    )

    if not disease_names:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No valid diseases were found in the current dataset.",
        )

    diseases = []

    for disease in disease_names:
        try:
            history = get_disease_history_info(
                dataframe,
                disease,
            )
        except ValueError:
            continue

        usable_observations = history["observation_count"] >= 20

        diseases.append(
            {
                "disease": history["disease"],
                "start_date": history["start_date"],
                "end_date": history["end_date"],
                "historical_days": history["historical_days"],
                "observation_count": history["observation_count"],
                "history_level": history["history_level"],
                "forecast_available": usable_observations,
                "available_horizons": (
                    [7, 14, 30] if usable_observations else []
                ),
                "warning": history["warning"],
            }
        )

    return {
        "dataset": {
            "id": dataset.id,
            "version_number": dataset.version_number,
            "filename": dataset.filename,
            "start_date": dataset.start_date,
            "end_date": dataset.end_date,
        },
        "diseases": diseases,
    }