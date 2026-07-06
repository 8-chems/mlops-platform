from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth.dependencies import require_admin
from app.models.prediction import PredictionLog
from app.schemas.prediction import PredictionLogOut

router = APIRouter(prefix="/api/logs", tags=["logs"])


@router.get("/predictions", response_model=list[PredictionLogOut], dependencies=[Depends(require_admin)])
def all_prediction_logs(db: Session = Depends(get_db), limit: int = 100):
    return db.query(PredictionLog).order_by(PredictionLog.created_at.desc()).limit(limit).all()
