import enum
import uuid
from datetime import datetime

from sqlalchemy import Column, String, DateTime, Enum, Float, Integer, JSON
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class TrainingStatus(str, enum.Enum):
    queued = "queued"
    running = "running"
    completed = "completed"
    failed = "failed"


class TrainingJob(Base):
    __tablename__ = "training_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    mlflow_run_id = Column(String, nullable=True)
    model_architecture = Column(String, nullable=False)
    epochs = Column(Integer, nullable=False)
    batch_size = Column(Integer, nullable=False)
    learning_rate = Column(Float, nullable=False)
    optimizer = Column(String, nullable=False)
    augmentation = Column(String, default="true")
    status = Column(Enum(TrainingStatus), default=TrainingStatus.queued)
    metrics = Column(JSON, nullable=True)
    model_gcs_path = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    finished_at = Column(DateTime, nullable=True)


class ModelRegistryEntry(Base):
    __tablename__ = "model_registry"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    training_job_id = Column(UUID(as_uuid=True), nullable=False)
    name = Column(String, nullable=False)
    version = Column(Integer, nullable=False)
    stage = Column(String, default="staging")
    gcs_path = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
