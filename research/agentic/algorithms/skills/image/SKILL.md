---
name: image-reader
description: Use this skill to read, analyze, or describe an uploaded image file. Supports JPG, PNG, GIF, and WebP. Always use this when the user uploads an image or provides an image file_id.
---

# image-reader

## Overview

Reads an uploaded image from disk, encodes it as base64, and sends it to the vision model for analysis. Returns a detailed description or answers the user's question about the image.

## When to use

- User says "I uploaded an image" or "look at this image"
- The user message contains `[Attached Image — file_id: ...]`
- User asks questions about an image they have attached (describe, analyze, extract text, etc.)

**Do NOT use** without a `file_id`. If the user mentions an image but hasn't uploaded one, ask them to attach it.

## How to invoke

```
view_image(file_id="<thread_id>/<uuid>.<ext>", question="<optional question>")
```

The `file_id` is always provided in the user message when an image is attached:
```
[Attached Image — file_id: abc123/def456.png]
```

### Example

User message:
```
[Attached Image — file_id: session-xyz/a1b2c3d4.jpg]
What does this chart show?
```

Tool call:
```
view_image(file_id="session-xyz/a1b2c3d4.jpg", question="What does this chart show?")
```

## Expected output

A detailed description or answer from the vision model based on the image content.

## Model

The tool sends the picture to `settings.VISION_MODEL_ID` when the app sets it, otherwise to `settings.GENERAL_MODEL_ID`. The model must read images: on Ollama `gemma3:4b` can, `qwen3` cannot. So an app whose general model is `qwen3:8b` sets `VISION_MODEL_ID=gemma3:4b`.

## Implementation

See `image_skill.py` in this folder.
