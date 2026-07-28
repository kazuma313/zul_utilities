# logging_config.py
import logging
from logging.config import dictConfig

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,  # supaya logger lib pihak ketiga tetap jalan
    "formatters": {
        "standard": {
            "format": "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "INFO",
            "formatter": "standard",
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "INFO",
            "formatter": "standard",
            "filename": "logs/app.log",
            "maxBytes": 5_000_000,
            "backupCount": 5,
            "encoding": "utf-8",
        },
    },
    "root": {  # untuk library pihak ketiga
        "level": "WARNING",
        "handlers": ["console"],
    },
    "loggers": {
        "my_app": {  # logger utama app kamu
            "level": "INFO",
            "handlers": ["console", "file"],
            "propagate": False,
        },
    },
}


def configure_logging():
    dictConfig(LOGGING_CONFIG)
