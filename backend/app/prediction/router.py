import uuid

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth.dependencies import get_current_user
from app.models.user import User
from app.models.training import ModelRegistryEntry
from app.models.dataset import DatasetClass
from app.models.prediction import PredictionLog
from app.schemas.prediction import PredictionResult, PredictionLogOut
from app.storage import gcs
from app.training.ml import predict_image
from app.prediction.service import load_model_from_gcs

router = APIRouter(prefix="/api/predict", tags=["prediction"])


@router.post("", response_model=PredictionResult)
async def predict(file: UploadFile = File(...), db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    production_model = db.query(ModelRegistryEntry).filter(ModelRegistryEntry.stage == "production").first()
    if production_model is None:
        raise HTTPException(status_code=503, detail="No production model deployed yet")

    class_names = [c.name for c in db.query(DatasetClass).order_by(DatasetClass.created_at).all()]
    if not class_names:
        raise HTTPException(status_code=503, detail="No classes registered")

    data = await file.read()
    model = load_model_from_gcs(production_model.gcs_path)
    predicted_class, confidence = predict_image(model, data, class_names)

    image_path = gcs.upload_bytes(data, f"predictions/{uuid.uuid4().hex}.jpg", file.content_type or "image/jpeg")
    log = PredictionLog(
        user_id=user.id,
        model_id=production_model.id,
        image_gcs_path=image_path,
        predicted_class=predicted_class,
        confidence=confidence,
    )
    db.add(log)
    db.commit()

    return PredictionResult(predicted_class=predicted_class, confidence=confidence, model_version=production_model.version)


@router.get("/history", response_model=list[PredictionLogOut])
def prediction_history(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(PredictionLog).filter(PredictionLog.user_id == user.id).order_by(PredictionLog.created_at.desc()).all()
