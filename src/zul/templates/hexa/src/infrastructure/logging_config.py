"""
Konfigurasi logging aplikasi: ke console dan ke `logs/app.log`.

Cara pakai:
    Dipanggil sekali saat aplikasi mulai (lihat `src/interface/http/main.py`):

    from src.infrastructure.logging_config import setup_logging

    setup_logging()                    # level INFO
    setup_logging(logging.DEBUG)       # lebih rinci saat debugging

    Di modul lain cukup pakai logger biasa:

    logger = logging.getLogger(__name__)
    logger.info("pesan diterima thread_id=%s", thread_id)
"""

import logging
import sys
from pathlib import Path

# --------------------------------------------------------------------------
# Format Log
# --------------------------------------------------------------------------
#
# Setiap baris log memuat waktu, nama modul, level, lalu pesannya. Nama
# modul berasal dari logging.getLogger(__name__), sehingga dari satu
# baris log langsung terlihat file mana yang menulis pesan itu.
#

LOG_DIRECTORY = Path("logs")
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logging(log_level: int = logging.INFO) -> None:
    """Pasang handler console dan file di root logger."""
    LOG_DIRECTORY.mkdir(exist_ok=True)

    logging.basicConfig(
        level=log_level,
        format=LOG_FORMAT,
        datefmt=DATE_FORMAT,
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(LOG_DIRECTORY / "app.log", encoding="utf-8"),
        ],
    )

    # Library berikut menulis satu baris log untuk tiap request
    # yang lewat. Level-nya dinaikkan agar log dari aplikasi
    # sendiri tidak tenggelam di antara log library itu.
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)

    logging.getLogger(__name__).info("Logging siap dipakai")
