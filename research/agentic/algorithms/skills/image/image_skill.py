"""Image reader skill.

Reads an uploaded image file, encodes it as base64, and sends it to the
vision model to answer the user's question or describe the image.

Images are resized before sending if they exceed the MAX_PIXELS limit to
avoid decompression-bomb rejections from the vLLM server.
"""

import base64
import io
import logging
from pathlib import Path

from langchain_core.tools import tool
from openai import OpenAI
from PIL import Image

# Pillow raises DecompressionBombError for images over ~178MP by default.
# We handle resizing ourselves, so disable the hard limit.
Image.MAX_IMAGE_PIXELS = None

from app.config.settings import settings

logger = logging.getLogger(__name__)

# skills/image/ → project root → app/uploads/
UPLOADS_DIR = Path(__file__).parent.parent.parent / "app" / "uploads"

MIME_TYPES = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".gif": "image/gif",
    ".webp": "image/webp",
}

# vLLM rejects images over ~179M pixels; stay well under that
MAX_PIXELS = 4096 * 4096  # ~16.7M pixels
MAX_LONG_SIDE = 4096       # cap the longest dimension


def _prepare_image(image_path: Path, mime_type: str) -> tuple[bytes, str]:
    """Load image, resize if needed, return (bytes, mime_type)."""
    with Image.open(image_path) as img:
        # Convert palette/RGBA modes that JPEG can't handle
        if img.mode not in ("RGB", "RGBA", "L"):
            img = img.convert("RGB")

        w, h = img.size
        pixels = w * h
        logger.info("[TOOL] view_image original size=%dx%d (%dMP)", w, h, pixels // 1_000_000)

        if pixels > MAX_PIXELS or max(w, h) > MAX_LONG_SIDE:
            scale = min(MAX_LONG_SIDE / max(w, h), (MAX_PIXELS / pixels) ** 0.5)
            new_w, new_h = int(w * scale), int(h * scale)
            img = img.resize((new_w, new_h), Image.LANCZOS)
            logger.info("[TOOL] view_image resized to %dx%d", new_w, new_h)

        buf = io.BytesIO()
        fmt = "JPEG" if mime_type == "image/jpeg" else "PNG"
        save_mime = "image/jpeg" if fmt == "JPEG" else "image/png"
        if img.mode == "RGBA" and fmt == "JPEG":
            img = img.convert("RGB")
        img.save(buf, format=fmt, optimize=True)
        return buf.getvalue(), save_mime


@tool
def view_image(file_id: str, question: str = "") -> str:
    """Analyze or describe an uploaded image.

    Use this whenever the user uploads an image or the message contains
    '[Attached Image — file_id: ...]'. Pass the user's question so the
    model can give a focused answer.

    Args:
        file_id: The image file identifier (format: 'thread_id/uuid.ext').
        question: Optional question about the image. Defaults to a general description request.
    """
    logger.info("[TOOL] view_image called | file_id=%s | question=%r", file_id, question)

    image_path = UPLOADS_DIR / file_id
    if not image_path.exists():
        logger.error("[TOOL] view_image file not found: %s", image_path)
        return f"Image file not found for file_id '{file_id}'. Make sure the file was uploaded successfully."

    suffix = image_path.suffix.lower()
    mime_type = MIME_TYPES.get(suffix)
    if not mime_type:
        return f"Unsupported image format '{suffix}'. Supported: {', '.join(MIME_TYPES)}."

    try:
        image_bytes, mime_type = _prepare_image(image_path, mime_type)
    except Exception as e:
        logger.error("[TOOL] view_image failed to load/resize image: %s", e)
        return f"Failed to process image: {e}"

    b64 = base64.b64encode(image_bytes).decode()
    data_url = f"data:{mime_type};base64,{b64}"

    prompt = question.strip() if question.strip() else (
        "Please describe this image in detail. Include any text, objects, charts, diagrams, or other notable content."
    )

    logger.info(
        "[TOOL] view_image sending to vision model | size=%d bytes | mime=%s",
        len(image_bytes), mime_type,
    )

    # A text model cannot read the picture (qwen3 has no vision), so VISION_MODEL_ID may name a
    # separate model, for example gemma3:4b on Ollama.  Without it the general model is used, as before.
    model = getattr(settings, "VISION_MODEL_ID", "") or settings.GENERAL_MODEL_ID

    try:
        client = OpenAI(api_key=settings.LLM_API_KEY, base_url=settings.LLM_BASE_URL)
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": data_url}},
                    ],
                }
            ],
        )
        result = response.choices[0].message.content or ""
        logger.info("[TOOL] view_image done | response_chars=%d", len(result))
        return result

    except Exception as e:
        logger.error("[TOOL] view_image error: %s", e)
        return f"Failed to analyze image: {e}"
