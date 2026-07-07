from __future__ import annotations

import logging
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

log = logging.getLogger(__name__)


class SQLiteStore:
    """Persist capture events and analysis payloads in SQLite."""

    def __init__(self, db_path: str | Path | None = None) -> None:
        self.db_path = Path(db_path or Path(__file__).resolve().parent.parent / "data" / "capture.db")
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS stocks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ticker TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    payload TEXT
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS fundamentals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ticker TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    payload TEXT
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS prices (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ticker TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    payload TEXT
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS screenshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ticker TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    payload TEXT
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS analysis_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ticker TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    payload TEXT
                )
                """
            )
            conn.commit()

    def save_capture(self, ticker: str, payload: dict[str, Any]) -> None:
        created_at = datetime.utcnow().isoformat()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO stocks (ticker, created_at, payload) VALUES (?, ?, ?)",
                (ticker, created_at, str(payload)),
            )
            conn.execute(
                "INSERT INTO fundamentals (ticker, created_at, payload) VALUES (?, ?, ?)",
                (ticker, created_at, str(payload.get("fundamental", {}))),
            )
            conn.execute(
                "INSERT INTO prices (ticker, created_at, payload) VALUES (?, ?, ?)",
                (ticker, created_at, str(payload.get("price", {}))),
            )
            conn.execute(
                "INSERT INTO screenshots (ticker, created_at, payload) VALUES (?, ?, ?)",
                (ticker, created_at, str(payload.get("screenshots", []))),
            )
            conn.execute(
                "INSERT INTO analysis_results (ticker, created_at, payload) VALUES (?, ?, ?)",
                (ticker, created_at, str(payload)),
            )
            conn.commit()
