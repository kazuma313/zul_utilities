# Image untuk menjalankan `cctv` di server tanpa layar (mode save).
# PyTorch dari PyPI untuk Linux sudah membawa CUDA; dengan docker-compose.yml
# GPU NVIDIA dipakai, dengan docker-compose.cpu.yml model berjalan di CPU.
FROM python:3.11-slim

# git untuk meng-install zul dari GitHub; libgl1 dan libglib2.0-0 untuk OpenCV.
RUN apt-get update \
    && apt-get install -y --no-install-recommends git libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*
COPY --from=ghcr.io/astral-sh/uv:0.12.3 /uv /usr/local/bin/uv

WORKDIR /app
COPY pyproject.toml README.md ./
COPY src ./src
RUN uv pip install --system .
COPY configs ./configs

ENTRYPOINT ["cctv"]
CMD ["run", "configs/entrance.yaml", "--mode", "save"]
