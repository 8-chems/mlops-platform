from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    environment: str = "local"
    database_url: str = "postgresql://mlops:mlops@localhost:5432/mlops"

    jwt_secret_key: str = "change-me"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 120

    gcs_bucket_name: str = "mlops-platform-artifacts"
    gcp_project_id: str = "your-gcp-project"
    firebase_credentials_path: str = "firebase-service-account.json"

    mlflow_tracking_uri: str = "http://localhost:5000"
    cors_origins: str = "http://localhost:5173"

    class Config:
        env_file = ".env"

    @property
    def cors_origin_list(self):
        return [o.strip() for o in self.cors_origins.split(",")]


@lru_cache
def get_settings() -> Settings:
    return Settings()
