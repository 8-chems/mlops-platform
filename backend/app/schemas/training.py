import uuid
from datetime import datetime
from pydantic import BaseModel, Field

from app.models.training import TrainingStatus


class TrainingJobCreate(BaseModel):
    model_architecture: str = Field(default="EfficientNetB0")
    epochs: int = Field(default=50, ge=1, le=1000)
    batch_size: int = Field(default=32, ge=1, le=512)
    learning_rate: float = Field(default=0.001, gt=0)
    optimizer: str = Field(default="adam")
    augmentation: bool = True


class TrainingJobOut(BaseModel):
    id: uuid.UUID
    model_architecture: str
    epochs: int
    batch_size: int
    learning_rate: float
    optimizer: str
    status: TrainingStatus
    metrics: dict | None = None
    mlflow_run_id: str | None = None
    created_at: datetime
    finished_at: datetime | None = None

    class Config:
        from_attributes = True


class ModelRegistryOut(BaseModel):
    id: uuid.UUID
    name: str
    version: int
    stage: str
    gcs_path: str

    class Config:
        from_attributes = True


class PromoteModelRequest(BaseModel):
    stage: str = Field(pattern="^(staging|production|archived)$")
