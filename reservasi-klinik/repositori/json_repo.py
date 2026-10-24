"""Repositori JSON.

Hanya modul ini yang mengetahui bahwa data aplikasi disimpan sebagai JSON.
"""

import json
from pathlib import Path


class JsonRepository:
    def __init__(self, path: str | Path):
        self.path = Path(path)

    def ambil_semua(self) -> dict:
        with self.path.open(encoding="utf-8") as file:
            return json.load(file)

    def simpan_semua(self, data: dict) -> None:
        with self.path.open("w", encoding="utf-8") as file:
            json.dump(data, file, indent=2, ensure_ascii=False)

