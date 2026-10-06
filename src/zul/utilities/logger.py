"""
Logger siap pakai: menulis ke console dan ke file (rotating).

Cara pakai:
    from zul.utilities.logger import get_logger

    logger = get_logger()                                    # logs/app.log
    logger = get_logger("ingestion", level="DEBUG", log_file="logs/ingest.log")

    logger.info("mulai memproses %d dokumen", total)

Folder file log dibuat otomatis. Memanggil `get_logger` berkali-kali dengan
nama yang sama mengembalikan logger yang sama tanpa menggandakan handler.
"""

import logging
import logging.config
from pathlib import Path

# --------------------------------------------------------------------------
# Konfigurasi Logging
# --------------------------------------------------------------------------
#
# Bentuknya mengikuti logging.config.dictConfig. Logger milik library
# pihak ketiga sengaja tidak dimatikan, dan file log dirotasi saat
# ukurannya mencapai 1 MB dengan 5 file cadangan yang disimpan.
#

DEFAULT_LOGGER_NAME = "my_service"
DEFAULT_LOG_FILE = "logs/app.log"

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,  # supaya logger lib pihak ketiga tetap jalan
    "formatters": {
        "standard": {"format": "%(asctime)s | %(levelname)s | %(name)s | %(message)s"}
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "standard",
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "formatter": "standard",
            "filename": DEFAULT_LOG_FILE,
            "maxBytes": 1_000_000,
            "backupCount": 5,
            "encoding": "utf-8",
        },
    },
    "loggers": {
        DEFAULT_LOGGER_NAME: {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False,
        }
    },
}

# --------------------------------------------------------------------------
# Membuat Logger
# --------------------------------------------------------------------------
#
# Nama logger yang sudah dikonfigurasi dicatat di sini, supaya
# dictConfig cuma berjalan sekali bagi tiap nama dan handler
# file tidak dibuat ulang tiap kali get_logger dipanggil.
#

_configured_loggers: set[str] = set()


def _build_config(name: str, level: str, log_file: str) -> dict:
    """LOGGING_CONFIG untuk satu logger dengan nama, level, dan file tertentu."""
    return {
        **LOGGING_CONFIG,
        "handlers": {
            **LOGGING_CONFIG["handlers"],
            "file": {**LOGGING_CONFIG["handlers"]["file"], "filename": log_file},
        },
        "loggers": {
            name: {**LOGGING_CONFIG["loggers"][DEFAULT_LOGGER_NAME], "level": level}
        },
    }


def get_logger(
    name: str = DEFAULT_LOGGER_NAME,
    level: str = "INFO",
    log_file: str = DEFAULT_LOG_FILE,
) -> logging.Logger:
    """
    Logger yang menulis ke console dan ke file (rotating).

    Aman dipanggil berulang kali: handler hanya dipasang sekali per nama logger.
    Folder log_file dibuat otomatis jika belum ada.
    """
    if name not in _configured_loggers:
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)
        logging.config.dictConfig(_build_config(name, level, log_file))
        _configured_loggers.add(name)
    return logging.getLogger(name)
