from pathlib import Path
import joblib


PROJECT_ROOT = Path(__file__).resolve().parents[2]
ARTIFACTS_DIR = PROJECT_ROOT / "ml" / "artifacts"


def save_model(model, artifact_path):
    """
    Save a trained model using Joblib.
    """
    artifact_path = Path(artifact_path)

    if not artifact_path.is_absolute():
        artifact_path = PROJECT_ROOT / artifact_path

    artifact_path.parent.mkdir(parents=True, exist_ok=True)

    joblib.dump(model, artifact_path)

    return artifact_path


def load_model(artifact_path):
    """
    Load a previously saved Joblib model.
    """
    artifact_path = Path(artifact_path)

    if not artifact_path.is_absolute():
        artifact_path = PROJECT_ROOT / artifact_path

    if not artifact_path.exists():
        raise FileNotFoundError(
            f"Model artifact not found: {artifact_path}"
        )

    return joblib.load(artifact_path)