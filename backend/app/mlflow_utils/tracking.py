from app.core.config import get_settings

settings = get_settings()

EXPERIMENT_NAME = "image-classification"


def init_mlflow():
    import mlflow
    mlflow.set_tracking_uri(settings.mlflow_tracking_uri)
    mlflow.set_experiment(EXPERIMENT_NAME)


def start_run(run_name: str):
    import mlflow
    init_mlflow()
    return mlflow.start_run(run_name=run_name)


def log_params(params: dict):
    import mlflow
    mlflow.log_params(params)


def log_metrics(metrics: dict, step: int | None = None):
    import mlflow
    mlflow.log_metrics(metrics, step=step)


def log_artifact(local_path: str):
    import mlflow
    mlflow.log_artifact(local_path)


def log_model(model, artifact_path: str = "model"):
    import mlflow
    mlflow.tensorflow.log_model(model, artifact_path)
