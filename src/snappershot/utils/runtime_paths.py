from __future__ import annotations

import os
import sys
from pathlib import Path


def is_frozen() -> bool:
    return bool(getattr(sys, "frozen", False))


def base_dir() -> Path:
    if is_frozen() and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)  # type: ignore[attr-defined]
    return Path(__file__).resolve().parents[3]


def app_data_dir() -> Path:
    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        return Path(local_app_data) / "SnapperShot"
    return Path.home() / "AppData" / "Local" / "SnapperShot"


def resource_path(*parts: str) -> Path:
    return base_dir().joinpath(*parts)


def env_file_candidates() -> list[Path]:
    candidates: list[Path] = []

    candidates.append(Path.cwd() / ".env")
    candidates.append(Path(__file__).resolve().parents[3] / ".env")

    if getattr(sys, "frozen", False):
        exe_path = Path(sys.executable).resolve()
        candidates.append(exe_path.with_name(".env"))
        candidates.append(base_dir() / ".env")

    unique: list[Path] = []
    for candidate in candidates:
        if candidate not in unique:
            unique.append(candidate)
    return unique
