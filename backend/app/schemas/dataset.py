import uuid
from datetime import datetime
from pydantic import BaseModel


class DatasetClassCreate(BaseModel):
    name: str


class DatasetClassOut(BaseModel):
    id: uuid.UUID
    name: str
    image_count: int = 0

    class Config:
        from_attributes = True


class DatasetImageOut(BaseModel):
    id: uuid.UUID
    class_id: uuid.UUID
    gcs_path: str
    split: str
    uploaded_at: datetime

    class Config:
        from_attributes = True


class DatasetStats(BaseModel):
    total_images: int
    train: int
    val: int
    test: int
    per_class: dict[str, int]
