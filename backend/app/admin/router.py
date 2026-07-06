from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.auth.dependencies import require_admin
from app.models.user import User
from app.models.dataset import DatasetImage
from app.models.training import TrainingJob
from app.models.prediction import PredictionLog

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/overview", dependencies=[Depends(require_admin)])
def admin_overview(db: Session = Depends(get_db)):
    return {
        "total_users": db.query(func.count(User.id)).scalar(),
        "total_images": db.query(func.count(DatasetImage.id)).scalar(),
        "total_training_jobs": db.query(func.count(TrainingJob.id)).scalar(),
        "total_predictions": db.query(func.count(PredictionLog.id)).scalar(),
    }


@router.get("/users", dependencies=[Depends(require_admin)])
def list_users(db: Session = Depends(get_db)):
    return db.query(User).all()
