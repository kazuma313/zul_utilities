"""
Milvus Helper Utility (lokal ke project)
"""

import json
from pathlib import Path
from typing import Optional


class Milvus:
    """
    Helper class untuk Milvus.
    1. Secara default, config dicari di folder project (cwd).
    2. config_path bisa di-set manual ke file json config lokal.
    3. host/port bisa di-override manual.
    """

    def __init__(
        self,
        config_path: str = "milvus_config.json",
        host: Optional[str] = None,
        port: Optional[int] = None,
    ):
        # Cek config di cwd
        cfg_path = Path.cwd() / config_path
        config = {}

        if cfg_path.exists():
            with open(cfg_path, "r", encoding="utf-8") as f:
                config = json.load(f)

        self.host = host if host is not None else config.get("host", "localhost")
        self.port = port if port is not None else config.get("port", 19530)
        self.connected = False

    def connect(self):
        print(f"Connecting to Milvus at {self.host}:{self.port} ...")
        self.connected = True

    def disconnect(self):
        if self.connected:
            print("Disconnected from Milvus")
            self.connected = False

    def is_connected(self):
        return self.connected
