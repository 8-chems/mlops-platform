from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.database import Base, engine
from app.auth.router import router as auth_router
from app.dataset.router import router as dataset_router
from app.training.router import router as training_router
from app.prediction.router import router as prediction_router
from app.admin.router import router as admin_router
from app.logs.router import router as logs_router

# Import models so they register on Base.metadata before create_all / migrations
from app.models import user, dataset, training, prediction  # noqa: F401

settings = get_settings()

app = FastAPI(
    title="MLOps Image Classification Platform",
    description="Production-style MLOps platform: dataset management, training, "
                "MLflow tracking, model registry, and client-facing inference.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(dataset_router)
app.include_router(training_router)
app.include_router(prediction_router)
app.include_router(admin_router)
app.include_router(logs_router)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.on_event("startup")
async def on_startup():
    # Database tables should be created via Alembic migrations in production
    # For local dev, run migrations manually or use a separate script
    pass
