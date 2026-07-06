import uuid

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from PIL import Image
import io

from app.database import get_db
from app.auth.dependencies import require_admin
from app.models.dataset import DatasetClass, DatasetImage
from app.schemas.dataset import DatasetClassCreate, DatasetClassOut, DatasetImageOut, DatasetStats
from app.storage import gcs

router = APIRouter(prefix="/api/datasets", tags=["datasets"])


@router.post("/classes", response_model=DatasetClassOut, dependencies=[Depends(require_admin)])
def create_class(payload: DatasetClassCreate, db: Session = Depends(get_db)):
    if db.query(DatasetClass).filter(DatasetClass.name == payload.name).first():
        raise HTTPException(status_code=400, detail="Class already exists")
    cls = DatasetClass(name=payload.name)
    db.add(cls)
    db.commit()
    db.refresh(cls)
    return DatasetClassOut(id=cls.id, name=cls.name, image_count=0)


@router.get("/classes", response_model=list[DatasetClassOut], dependencies=[Depends(require_admin)])
def list_classes(db: Session = Depends(get_db)):
    classes = db.query(DatasetClass).all()
    return [DatasetClassOut(id=c.id, name=c.name, image_count=len(c.images)) for c in classes]


@router.delete("/classes/{class_id}", dependencies=[Depends(require_admin)])
def delete_class(class_id: uuid.UUID, db: Session = Depends(get_db)):
    cls = db.query(DatasetClass).filter(DatasetClass.id == class_id).first()
    if cls is None:
        raise HTTPException(status_code=404, detail="Class not found")
    for img in cls.images:
        gcs.delete_object(img.gcs_path)
    db.delete(cls)
    db.commit()
    return {"status": "deleted"}


@router.post("/classes/{class_id}/images", response_model=DatasetImageOut, dependencies=[Depends(require_admin)])
async def upload_image(class_id: uuid.UUID, split: str = "train", file: UploadFile = File(...), db: Session = Depends(get_db)):
    cls = db.query(DatasetClass).filter(DatasetClass.id == class_id).first()
    if cls is None:
        raise HTTPException(status_code=404, detail="Class not found")

    data = await file.read()
    try:
        img = Image.open(io.BytesIO(data))
        width, height = img.size
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid image file")

    gcs_path = gcs.upload_image(data, cls.name, content_type=file.content_type or "image/jpeg")
    record = DatasetImage(class_id=class_id, gcs_path=gcs_path, split=split, width=width, height=height)
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.delete("/images/{image_id}", dependencies=[Depends(require_admin)])
def delete_image(image_id: uuid.UUID, db: Session = Depends(get_db)):
    img = db.query(DatasetImage).filter(DatasetImage.id == image_id).first()
    if img is None:
        raise HTTPException(status_code=404, detail="Image not found")
    gcs.delete_object(img.gcs_path)
    db.delete(img)
    db.commit()
    return {"status": "deleted"}


@router.get("/stats", response_model=DatasetStats, dependencies=[Depends(require_admin)])
def dataset_stats(db: Session = Depends(get_db)):
    images = db.query(DatasetImage).all()
    per_class: dict[str, int] = {}
    splits = {"train": 0, "val": 0, "test": 0}
    for img in images:
        cls_name = img.dataset_class.name
        per_class[cls_name] = per_class.get(cls_name, 0) + 1
        if img.split in splits:
            splits[img.split] += 1
    return DatasetStats(total_images=len(images), train=splits["train"], val=splits["val"], test=splits["test"], per_class=per_class)
