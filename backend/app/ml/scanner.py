"""
MedVisionAI — MedicalModelScanner
=========================================
Wraps a TensorFlow/Keras CNN model to:
  1. Pre-process an uploaded image to model-compatible tensors
  2. Run forward inference and return class probabilities
  3. Generate Grad-CAM heatmap overlays for explainability

Architecture assumptions (swappable via MODEL_PATH env var):
  • Input size  : 224 × 224 × 3
  • Output      : softmax probability vector over CLASS_NAMES
  • Last conv   : auto-detected by scanning model layers in reverse

The class uses a MOCK model when no .h5 file is present so the
entire prediction + Grad-CAM pipeline can be exercised immediately.
"""

import os
import io
import base64
import json
import logging
from pathlib import Path
from typing import Dict, Tuple

import cv2
import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)

# ── Constants ─────────────────────────────────────────────────
IMG_SIZE = (224, 224)

CLASS_NAMES = [
    "Normal",
    "Pneumonia",
    "COVID-19",
    "Pleural Effusion",
    "Cardiomegaly",
]

MODEL_PATH = os.getenv("MODEL_PATH", "/app/models/medvision_cnn.h5")


# ── Lazy TF import (avoids long TF startup for non-ML routes) ─
def _import_tf():
    import tensorflow as tf
    return tf


# ── Mock Model ────────────────────────────────────────────────
class _MockModel:
    """
    Fallback when no real .h5 file is found.
    Returns deterministic-ish probabilities based on image statistics
    so the Grad-CAM pipeline can still be tested end-to-end.
    """
    def __init__(self):
        self.layers = [_MockLayer("mock_conv_last")]

    def predict(self, x: np.ndarray) -> np.ndarray:
        # Seed with image mean so results are image-dependent
        seed = int(x.mean() * 1000) % 2**31
        rng = np.random.default_rng(seed)
        logits = rng.dirichlet(np.ones(len(CLASS_NAMES)))
        return logits[np.newaxis, :]  # shape (1, num_classes)

    def __call__(self, x):
        return self.predict(x)


class _MockLayer:
    def __init__(self, name: str):
        self.name = name
        self.output = None  # not used in mock path


# ── Main Scanner Class ────────────────────────────────────────
class MedicalModelScanner:
    """
    Singleton-style ML scanner.
    Instantiate once at app startup; call `analyse(image_bytes)` per request.
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._model = None
            cls._instance._is_mock = False
        return cls._instance

    # ── Initialisation ────────────────────────────────────────
    def load_model(self) -> None:
        """Load the Keras model from disk, or fall back to mock."""
        if self._model is not None:
            return

        if Path(MODEL_PATH).exists():
            try:
                tf = _import_tf()
                self._model = tf.keras.models.load_model(MODEL_PATH)
                self._is_mock = False
                logger.info(f"Loaded real model from {MODEL_PATH}")
            except Exception as exc:
                logger.warning(f"Could not load model ({exc}). Using mock.")
                self._model = _MockModel()
                self._is_mock = True
        else:
            logger.warning(f"Model not found at {MODEL_PATH}. Using mock model.")
            self._model = _MockModel()
            self._is_mock = True

    # ── Pre-processing ────────────────────────────────────────
    @staticmethod
    def _preprocess(image_bytes: bytes) -> Tuple[np.ndarray, np.ndarray]:
        """
        Convert raw image bytes → (model_input_tensor, display_rgb_array).

        Returns:
            tensor       : float32 array of shape (1, 224, 224, 3), values in [0, 1]
            display_img  : uint8 RGB array (224, 224, 3) for overlay generation
        """
        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        img = img.resize(IMG_SIZE, Image.LANCZOS)
        arr = np.array(img, dtype=np.float32) / 255.0          # normalise [0, 1]
        tensor = np.expand_dims(arr, axis=0)                    # (1, H, W, C)
        display_img = np.array(img, dtype=np.uint8)
        return tensor, display_img

    # ── Grad-CAM ──────────────────────────────────────────────
    def _compute_gradcam(
        self,
        tensor: np.ndarray,
        class_idx: int,
        display_img: np.ndarray,
    ) -> np.ndarray:
        """
        Full Grad-CAM implementation:

        1. Build a sub-model that outputs (last_conv_feature_maps, predictions)
        2. Record gradients d(class_score) / d(last_conv_output) via GradientTape
        3. Pool gradients spatially  →  weights α_k  (one per feature map)
        4. Weighted sum of feature maps  →  heatmap  (pre-ReLU)
        5. ReLU to keep only positive contributions
        6. Resize heatmap to 224 × 224 and apply jet colour map
        7. Blend heatmap onto original image (α = 0.5)

        Returns:
            overlaid_bgr : uint8 BGR image (224, 224, 3) ready for cv2 encoding
        """
        if self._is_mock:
            return self._mock_gradcam(display_img)

        tf = _import_tf()

        # Find the last convolutional layer
        last_conv_layer = None
        for layer in reversed(self._model.layers):
            if isinstance(layer, (
                tf.keras.layers.Conv2D,
                tf.keras.layers.DepthwiseConv2D,
            )):
                last_conv_layer = layer
                break

        if last_conv_layer is None:
            logger.warning("No Conv2D layer found — returning plain heatmap.")
            return self._mock_gradcam(display_img)

        # Sub-model: input → (conv_output, predictions)
        grad_model = tf.keras.Model(
            inputs=self._model.inputs,
            outputs=[last_conv_layer.output, self._model.output],
        )

        with tf.GradientTape() as tape:
            inputs = tf.cast(tensor, tf.float32)
            conv_outputs, predictions = grad_model(inputs)
            # Score for the target class
            loss = predictions[:, class_idx]

        # Gradients of class score w.r.t. conv feature maps
        grads = tape.gradient(loss, conv_outputs)        # (1, H', W', C_conv)

        # Global Average Pool over spatial dims → (C_conv,)
        pooled_grads = tf.reduce_mean(grads, axis=(0, 1, 2))

        conv_outputs = conv_outputs[0]                   # (H', W', C_conv)
        # Weight each feature map and sum
        heatmap = conv_outputs @ pooled_grads[..., tf.newaxis]  # (H', W', 1)
        heatmap = tf.squeeze(heatmap)                    # (H', W')

        # ReLU — keep only positive contributions
        heatmap = tf.nn.relu(heatmap).numpy()

        # Normalise to [0, 1]
        heatmap_max = heatmap.max()
        if heatmap_max > 0:
            heatmap = heatmap / heatmap_max

        return self._apply_colormap(heatmap, display_img)

    @staticmethod
    def _apply_colormap(heatmap: np.ndarray, display_img: np.ndarray) -> np.ndarray:
        """Resize heatmap, apply JET colormap, blend with original."""
        heatmap_uint8 = np.uint8(255 * heatmap)
        heatmap_resized = cv2.resize(heatmap_uint8, IMG_SIZE)
        jet = cv2.applyColorMap(heatmap_resized, cv2.COLORMAP_JET)

        # Convert display_img (RGB) → BGR for OpenCV
        display_bgr = cv2.cvtColor(display_img, cv2.COLOR_RGB2BGR)

        # Weighted overlay
        overlay = cv2.addWeighted(display_bgr, 0.55, jet, 0.45, 0)
        return overlay

    @staticmethod
    def _mock_gradcam(display_img: np.ndarray) -> np.ndarray:
        """
        Generate a plausible-looking Grad-CAM for the mock model.
        Creates a symmetric Gaussian blob centred on the image,
        mimicking the model paying attention to the lung region.
        """
        h, w = IMG_SIZE
        # Create Gaussian heat source around center-lower region (lung area)
        cx, cy = w // 2, int(h * 0.55)
        x = np.arange(w)
        y = np.arange(h)
        X, Y = np.meshgrid(x, y)
        sigma_x, sigma_y = w * 0.28, h * 0.32
        heatmap = np.exp(
            -(((X - cx) ** 2) / (2 * sigma_x ** 2) + ((Y - cy) ** 2) / (2 * sigma_y ** 2))
        )
        # Add a secondary smaller blob (simulate second lung)
        cx2 = int(w * 0.35)
        heatmap += 0.6 * np.exp(
            -(((X - cx2) ** 2) / (2 * (sigma_x * 0.6) ** 2) + ((Y - cy) ** 2) / (2 * (sigma_y * 0.6) ** 2))
        )
        heatmap = (heatmap / heatmap.max()).astype(np.float32)
        return MedicalModelScanner._apply_colormap(heatmap, display_img)

    # ── Encode overlay → base64 ───────────────────────────────
    @staticmethod
    def _encode_base64(bgr_image: np.ndarray) -> str:
        """Encode a BGR OpenCV image as a base64 PNG string."""
        success, buffer = cv2.imencode(".png", bgr_image)
        if not success:
            raise RuntimeError("Failed to encode Grad-CAM image to PNG.")
        return base64.b64encode(buffer).decode("utf-8")

    # ── Public API ────────────────────────────────────────────
    def analyse(self, image_bytes: bytes) -> Dict:
        """
        Full inference pipeline.

        Args:
            image_bytes: Raw bytes of the uploaded medical image.

        Returns:
            {
                "prediction":   str,   # Top class label
                "confidence":   float, # Probability 0–1
                "all_scores":   str,   # JSON of {label: score, ...}
                "gradcam_b64":  str,   # Base64 PNG heatmap overlay
                "is_mock":      bool,  # True when using mock model
            }
        """
        self.load_model()

        tensor, display_img = self._preprocess(image_bytes)

        # Forward pass
        probs = self._model.predict(tensor)[0]           # (num_classes,)
        class_idx = int(np.argmax(probs))
        confidence = float(probs[class_idx])
        prediction = CLASS_NAMES[class_idx]

        all_scores = {
            CLASS_NAMES[i]: round(float(probs[i]), 4)
            for i in range(len(CLASS_NAMES))
        }

        # Grad-CAM
        gradcam_bgr = self._compute_gradcam(tensor, class_idx, display_img)
        gradcam_b64 = self._encode_base64(gradcam_bgr)

        logger.info(
            f"Prediction: {prediction} ({confidence:.2%}) | mock={self._is_mock}"
        )

        return {
            "prediction": prediction,
            "confidence": confidence,
            "all_scores": json.dumps(all_scores),
            "gradcam_b64": gradcam_b64,
            "is_mock": self._is_mock,
        }
