import uuid
from datetime import datetime

from sqlalchemy import Column, String, DateTime, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class DatasetClass(Base):
    __tablename__ = "dataset_classes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    images = relationship("DatasetImage", back_populates="dataset_class", cascade="all, delete-orphan")


class DatasetImage(Base):
    __tablename__ = "dataset_images"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    class_id = Column(UUID(as_uuid=True), ForeignKey("dataset_classes.id"), nullable=False)
    gcs_path = Column(String, nullable=False)
    split = Column(String, default="train")
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    dataset_class = relationship("DatasetClass", back_populates="images")
