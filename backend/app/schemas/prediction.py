import uuid
from datetime import datetime
from pydantic import BaseModel


class PredictionResult(BaseModel):
    predicted_class: str
    confidence: float
    model_version: int | None = None


class PredictionLogOut(BaseModel):
    id: uuid.UUID
    predicted_class: str
    confidence: float
    image_gcs_path: str
    created_at: datetime

    class Config:
        from_attributes = True
