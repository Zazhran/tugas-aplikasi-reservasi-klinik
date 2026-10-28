# repositori/json_repo.py
import json
import os

DATA_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data.json"
)


def baca_data():
    with open(DATA_FILE, encoding="utf-8") as f:
        return json.load(f)


def simpan_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)