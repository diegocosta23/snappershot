import asyncio
import json
import sqlite3
from pathlib import Path

from src.snappershot.capture_engine import CaptureEngine
from src.snappershot.database.sqlite_store import SQLiteStore
from src.snappershot.services.storage_service import StorageService

engine = CaptureEngine()
result = asyncio.run(
    engine.run("ABB.ST", screenshots=[Path("C:/temp/placeholder.png")])
)
print("RESULT_KEYS", sorted(result.keys()))
print("RESULT_JSON", json.dumps(result, indent=2, default=str)[:12000])
root = StorageService().ROOT_FOLDER
print("EXPORT_PATHS", [str(p) for p in root.rglob("analysis_package.json")][-5:])
db = SQLiteStore()
conn = sqlite3.connect(db.db_path)
cur = conn.cursor()
print(
    "TABLES",
    cur.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    ).fetchall(),
)
print(
    "ROWS",
    {
        t: cur.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        for t in [
            "stocks",
            "fundamentals",
            "prices",
            "technical_indicators",
            "news",
            "screenshots",
            "analysis_results",
        ]
    },
)
conn.close()
