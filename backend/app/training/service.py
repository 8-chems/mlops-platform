import uuid
from datetime import datetime

from sqlalchemy.orm import Session

from app.models.dataset import DatasetClass, DatasetImage
from app.models.training import TrainingJob, TrainingStatus, ModelRegistryEntry
from app.storage import gcs
from app.mlflow_utils import tracking
from app.training.ml import train_model, save_model_to_tempdir, bytes_to_array


def run_training_job(db: Session, job_id: uuid.UUID):
    """Background task: loads dataset from GCS, trains, logs to MLflow,
    stores the model artifact, and updates job status."""
    job = db.query(TrainingJob).filter(TrainingJob.id == job_id).first()
    if job is None:
        return

    job.status = TrainingStatus.running
    db.commit()

    try:
        classes = db.query(DatasetClass).all()
        class_names = [c.name for c in classes]
        images, labels = [], []
        for idx, cls in enumerate(classes):
            for img in cls.images:
                data = gcs.download_bytes(img.gcs_path)
                images.append(bytes_to_array(data))
                labels.append(idx)

        with tracking.start_run(run_name=f"job-{job.id}") as run:
            tracking.log_params({
                "architecture": job.model_architecture,
                "epochs": job.epochs,
                "batch_size": job.batch_size,
                "learning_rate": job.learning_rate,
                "optimizer": job.optimizer,
                "augmentation": job.augmentation,
            })

            model, metrics = train_model(
                images, labels, class_names,
                architecture=job.model_architecture,
                epochs=job.epochs,
                batch_size=job.batch_size,
                learning_rate=job.learning_rate,
                optimizer_name=job.optimizer,
                augmentation=job.augmentation == "true",
            )
            tracking.log_metrics({k: v for k, v in metrics.items() if isinstance(v, (int, float))})

            local_path = save_model_to_tempdir(model)
            with open(local_path, "rb") as f:
                gcs_path = gcs.upload_bytes(f.read(), f"models/{job.id}.keras")

            job.mlflow_run_id = run.info.run_id
            job.metrics = metrics
            job.model_gcs_path = gcs_path
            job.status = TrainingStatus.completed
            job.finished_at = datetime.utcnow()
            db.commit()

            existing = db.query(ModelRegistryEntry).filter(
                ModelRegistryEntry.name == job.model_architecture
            ).count()
            registry_entry = ModelRegistryEntry(
                training_job_id=job.id,
                name=job.model_architecture,
                version=existing + 1,
                stage="staging",
                gcs_path=gcs_path,
            )
            db.add(registry_entry)
            db.commit()

    except Exception as exc:  # noqa: BLE001
        job.status = TrainingStatus.failed
        job.metrics = {"error": str(exc)}
        job.finished_at = datetime.utcnow()
        db.commit()
