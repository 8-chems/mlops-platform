"""Core training logic. Kept framework-simple (Keras) so it runs on CPU for
demos; swap in Vertex AI custom training jobs for real workloads (see
app/training/vertex.py stub)."""
import io
import tempfile
import uuid

import numpy as np
from PIL import Image
from sklearn.metrics import precision_score, recall_score, f1_score, confusion_matrix

IMG_SIZE = (224, 224)

def get_architectures():
    import tensorflow as tf
    return {
        "EfficientNetB0": tf.keras.applications.EfficientNetB0,
        "ResNet50": tf.keras.applications.ResNet50,
        "MobileNetV2": tf.keras.applications.MobileNetV2,
    }


def build_model(architecture: str, num_classes: int, learning_rate: float, optimizer_name: str):
    import tensorflow as tf
    architectures = get_architectures()
    base_cls = architectures.get(architecture, tf.keras.applications.EfficientNetB0)
    base = base_cls(include_top=False, weights="imagenet", input_shape=(*IMG_SIZE, 3), pooling="avg")
    base.trainable = False

    inputs = tf.keras.Input(shape=(*IMG_SIZE, 3))
    x = base(inputs, training=False)
    x = tf.keras.layers.Dropout(0.3)(x)
    outputs = tf.keras.layers.Dense(num_classes, activation="softmax")(x)
    model = tf.keras.Model(inputs, outputs)

    optimizers = {
        "adam": tf.keras.optimizers.Adam,
        "sgd": tf.keras.optimizers.SGD,
        "rmsprop": tf.keras.optimizers.RMSprop,
    }
    opt_cls = optimizers.get(optimizer_name.lower(), tf.keras.optimizers.Adam)
    model.compile(optimizer=opt_cls(learning_rate=learning_rate),
                  loss="sparse_categorical_crossentropy",
                  metrics=["accuracy"])
    return model


def bytes_to_array(image_bytes: bytes) -> np.ndarray:
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB").resize(IMG_SIZE)
    return np.asarray(img, dtype=np.float32) / 255.0


def build_augmentation_layer():
    import tensorflow as tf
    return tf.keras.Sequential([
        tf.keras.layers.RandomFlip("horizontal"),
        tf.keras.layers.RandomRotation(0.1),
        tf.keras.layers.RandomZoom(0.1),
        tf.keras.layers.RandomContrast(0.1),
    ])


def train_model(
    images: list[np.ndarray],
    labels: list[int],
    class_names: list[str],
    architecture: str,
    epochs: int,
    batch_size: int,
    learning_rate: float,
    optimizer_name: str,
    augmentation: bool,
) -> tuple:
    X = np.stack(images)
    y = np.array(labels)

    split = int(len(X) * 0.8)
    X_train, X_val = X[:split], X[split:]
    y_train, y_val = y[:split], y[split:]

    model = build_model(architecture, len(class_names), learning_rate, optimizer_name)

    if augmentation:
        aug = build_augmentation_layer()
        X_train = aug(X_train, training=True).numpy()

    history = model.fit(
        X_train, y_train,
        validation_data=(X_val, y_val),
        epochs=epochs,
        batch_size=batch_size,
        verbose=0,
    )

    y_pred = np.argmax(model.predict(X_val, verbose=0), axis=1)
    metrics = {
        "final_accuracy": float(history.history["accuracy"][-1]),
        "final_val_accuracy": float(history.history["val_accuracy"][-1]),
        "final_loss": float(history.history["loss"][-1]),
        "final_val_loss": float(history.history["val_loss"][-1]),
        "precision": float(precision_score(y_val, y_pred, average="macro", zero_division=0)),
        "recall": float(recall_score(y_val, y_pred, average="macro", zero_division=0)),
        "f1": float(f1_score(y_val, y_pred, average="macro", zero_division=0)),
        "confusion_matrix": confusion_matrix(y_val, y_pred).tolist(),
        "history": {k: [float(v) for v in vals] for k, vals in history.history.items()},
    }
    return model, metrics


def save_model_to_tempdir(model) -> str:
    tmpdir = tempfile.mkdtemp()
    path = f"{tmpdir}/{uuid.uuid4().hex}.keras"
    model.save(path)
    return path


def predict_image(model, image_bytes: bytes, class_names: list[str]) -> tuple[str, float]:
    arr = np.expand_dims(bytes_to_array(image_bytes), axis=0)
    probs = model.predict(arr, verbose=0)[0]
    idx = int(np.argmax(probs))
    return class_names[idx], float(probs[idx])
