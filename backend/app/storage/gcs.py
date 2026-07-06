import uuid
from io import BytesIO

from google.cloud import storage

from app.core.config import get_settings

settings = get_settings()

_client = None


def get_client() -> storage.Client:
    global _client
    if _client is None:
        _client = storage.Client(project=settings.gcp_project_id)
    return _client


def upload_bytes(data: bytes, destination_path: str, content_type: str = "application/octet-stream") -> str:
    """Uploads raw bytes to GCS and returns the gs:// path."""
    bucket = get_client().bucket(settings.gcs_bucket_name)
    blob = bucket.blob(destination_path)
    blob.upload_from_file(BytesIO(data), content_type=content_type)
    return f"gs://{settings.gcs_bucket_name}/{destination_path}"


def upload_image(data: bytes, class_name: str, content_type: str = "image/jpeg") -> str:
    filename = f"datasets/{class_name}/{uuid.uuid4().hex}.jpg"
    return upload_bytes(data, filename, content_type)


def download_bytes(gcs_path: str) -> bytes:
    """gcs_path may be a full gs:// URI or a bucket-relative path."""
    path = gcs_path.replace(f"gs://{settings.gcs_bucket_name}/", "")
    bucket = get_client().bucket(settings.gcs_bucket_name)
    blob = bucket.blob(path)
    return blob.download_as_bytes()


def delete_object(gcs_path: str) -> None:
    path = gcs_path.replace(f"gs://{settings.gcs_bucket_name}/", "")
    bucket = get_client().bucket(settings.gcs_bucket_name)
    bucket.blob(path).delete()


def generate_signed_url(gcs_path: str, expiration_seconds: int = 3600) -> str:
    path = gcs_path.replace(f"gs://{settings.gcs_bucket_name}/", "")
    bucket = get_client().bucket(settings.gcs_bucket_name)
    blob = bucket.blob(path)
    return blob.generate_signed_url(expiration=expiration_seconds)
