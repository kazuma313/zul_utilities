"""
Adapter RF-DETR: model deteksi dan keypoint, inference, dan unduhan bobot.

Gunanya:
    Satu-satunya file Zul yang mengimpor rfdetr (Apache 2.0). Hasil
    inference keluar sebagai array NumPy biasa: kotak, skor, kelas, dan
    untuk model keypoint, 17 keypoint COCO per orang. Frame masuk dalam
    urutan warna BGR seperti dari OpenCV; adapter membaliknya ke RGB
    yang dibutuhkan RF-DETR. Butuh extra detection:
    `pip install "zul[detection]"`.

Cara pakai:
    from zul.adapters import rfdetr as rfdetr_adapter

    weights = "models/rf-detr-keypoint-preview-xlarge.pth"
    model = rfdetr_adapter.load_model("keypoint", weights=weights)
    arrays = rfdetr_adapter.predict(model, frame, confidence=0.3)
    arrays["xyxy"], arrays["keypoints_xy"]

Kelas memakai id kategori COCO, jadi orang adalah kelas 1. Model keypoint
masih berstatus preview di RF-DETR, karena itu versinya dikunci di
pyproject.toml dan bagian yang dipakai Zul diuji di tests.
"""

from __future__ import annotations

import logging
import os
import warnings
from pathlib import Path
from typing import Any

import numpy as np
import rfdetr
import torch
from rfdetr.assets.model_weights import download_pretrain_weights

MODELS = {
    "keypoint": "RFDETRKeypointPreview",
    "nano": "RFDETRNano",
    "small": "RFDETRSmall",
    "medium": "RFDETRMedium",
    "large": "RFDETRLarge",
}
PERSON_CLASS_ID = 1

# --------------------------------------------------------------------------
# Model
# --------------------------------------------------------------------------
#
# Saat GPU tersedia, model diubah ke float16 lewat model.inference. Pada RTX
# 3060 Laptop, langkah ini memangkas waktu per frame model keypoint dari
# sekitar 77 menjadi 39 milidetik, dengan jumlah deteksi yang setara.
#


def model_class(name: str) -> Any:
    """Kelas RF-DETR untuk satu nama: keypoint, nano, small, medium, atau large."""
    if name not in MODELS:
        raise ValueError(
            f"model '{name}' tidak dikenal; pilih salah satu: {', '.join(MODELS)}"
        )
    return getattr(rfdetr, MODELS[name])


def default_weights(name: str) -> str:
    """Nama file bobot bawaan sebuah model, misalnya rf-detr-medium.pth."""
    return str(model_class(name)._model_config_class().pretrain_weights)


def load_model(
    name: str = "keypoint",
    weights: str | Path | None = None,
    half: bool = True,
    device: str | None = None,
    quiet: bool = True,
) -> Any:
    """Model RF-DETR yang siap dipakai `predict`.

    Tanpa `weights`, bobotnya diunduh ke folder cache RF-DETR (~/.roboflow/models,
    atau isi RF_HOME). Dengan `weights`, bobot diunduh ke path itu jika belum
    ada; nama filenya harus sama dengan nama bawaan model. `half` memakai
    float16 jika GPU tersedia. Objek yang dikembalikan hanya untuk `predict`.
    """
    options: dict[str, Any] = {}
    if weights is not None:
        options["pretrain_weights"] = str(weights)
    if device is not None:
        options["device"] = device
    logger = logging.getLogger("rf-detr")
    previous = logger.level
    if quiet:
        logger.setLevel(logging.ERROR)
    try:
        model = model_class(name)(**options)
        if half and torch.cuda.is_available() and (device or "cuda").startswith("cuda"):
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", torch.jit.TracerWarning)
                model.inference(dtype=torch.float16)
    finally:
        logger.setLevel(previous)
    return model


def predict(
    model: Any, image: np.ndarray, confidence: float
) -> dict[str, np.ndarray | None]:
    """Inference satu frame BGR, hasilnya sebagai dict array NumPy.

    Kuncinya xyxy `(n, 4)`, confidence `(n,)`, class_id `(n,)`, serta
    keypoints_xy `(n, 17, 2)` dan keypoints_conf `(n, 17)` untuk model
    keypoint, atau None untuk model deteksi.
    """
    rgb = np.ascontiguousarray(image[:, :, ::-1])
    result = model.predict(rgb, threshold=confidence, include_source_image=False)
    if hasattr(result, "keypoint_confidence"):
        count = len(result.xy)
        return {
            "xyxy": np.asarray(
                result.data.get("xyxy", np.empty((0, 4))), dtype=np.float64
            ).reshape(count, 4),
            "confidence": np.asarray(
                result.detection_confidence, dtype=np.float64
            ).reshape(count),
            "class_id": np.asarray(result.class_id, dtype=int).reshape(count),
            "keypoints_xy": np.asarray(result.xy, dtype=np.float64),
            "keypoints_conf": np.asarray(result.keypoint_confidence, dtype=np.float64),
        }
    return {
        "xyxy": np.asarray(result.xyxy, dtype=np.float64).reshape(-1, 4),
        "confidence": np.asarray(result.confidence, dtype=np.float64),
        "class_id": np.asarray(result.class_id, dtype=int),
        "keypoints_xy": None,
        "keypoints_conf": None,
    }


# --------------------------------------------------------------------------
# Unduhan Bobot
# --------------------------------------------------------------------------


def download_weights(path: str | Path) -> None:
    """Unduh bobot rilis RF-DETR ke `path`, dicek dengan MD5, jika namanya dikenal."""
    os.makedirs(Path(path).parent, exist_ok=True)
    download_pretrain_weights(str(path))
