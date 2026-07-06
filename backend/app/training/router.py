import uuid

from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth.dependencies import require_admin
from app.models.training import TrainingJob, ModelRegistryEntry
from app.schemas.training import (
    TrainingJobCreate, TrainingJobOut, ModelRegistryOut, PromoteModelRequest,
)
from app.training.service import run_training_job

router = APIRouter(prefix="/api/training", tags=["training"])


@router.post("/jobs", response_model=TrainingJobOut, dependencies=[Depends(require_admin)])
def create_training_job(payload: TrainingJobCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    job = TrainingJob(
        model_architecture=payload.model_architecture,
        epochs=payload.epochs,
        batch_size=payload.batch_size,
        learning_rate=payload.learning_rate,
        optimizer=payload.optimizer,
        augmentation="true" if payload.augmentation else "false",
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    background_tasks.add_task(run_training_job, db, job.id)
    return job


@router.get("/jobs", response_model=list[TrainingJobOut], dependencies=[Depends(require_admin)])
def list_training_jobs(db: Session = Depends(get_db)):
    return db.query(TrainingJob).order_by(TrainingJob.created_at.desc()).all()


@router.get("/jobs/{job_id}", response_model=TrainingJobOut, dependencies=[Depends(require_admin)])
def get_training_job(job_id: uuid.UUID, db: Session = Depends(get_db)):
    job = db.query(TrainingJob).filter(TrainingJob.id == job_id).first()
    if job is None:
        raise HTTPException(status_code=404, detail="Training job not found")
    return job


@router.get("/models", response_model=list[ModelRegistryOut], dependencies=[Depends(require_admin)])
def list_models(db: Session = Depends(get_db)):
    return db.query(ModelRegistryEntry).all()


@router.post("/models/{model_id}/promote", response_model=ModelRegistryOut, dependencies=[Depends(require_admin)])
def promote_model(model_id: uuid.UUID, payload: PromoteModelRequest, db: Session = Depends(get_db)):
    model = db.query(ModelRegistryEntry).filter(ModelRegistryEntry.id == model_id).first()
    if model is None:
        raise HTTPException(status_code=404, detail="Model not found")

    if payload.stage == "production":
        db.query(ModelRegistryEntry).filter(
            ModelRegistryEntry.name == model.name,
            ModelRegistryEntry.stage == "production",
        ).update({"stage": "archived"})

    model.stage = payload.stage
    db.commit()
    db.refresh(model)
    return model


@router.delete("/models/{model_id}", dependencies=[Depends(require_admin)])
def delete_model(model_id: uuid.UUID, db: Session = Depends(get_db)):
    model = db.query(ModelRegistryEntry).filter(ModelRegistryEntry.id == model_id).first()
    if model is None:
        raise HTTPException(status_code=404, detail="Model not found")
    db.delete(model)
    db.commit()
    return {"status": "deleted"}
