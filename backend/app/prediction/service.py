import functools

from app.storage import gcs


@functools.lru_cache(maxsize=4)
def load_model_from_gcs(gcs_path: str):
    """Downloads and caches a Keras model from GCS by path."""
    import tempfile
    import tensorflow as tf
    data = gcs.download_bytes(gcs_path)
    with tempfile.NamedTemporaryFile(suffix=".keras", delete=False) as f:
        f.write(data)
        local_path = f.name
    return tf.keras.models.load_model(local_path)
