from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def build_analysis_package(payload: dict[str, Any], output_dir: str | Path | None = None) -> Path:
    export_dir = Path(output_dir or Path(__file__).resolve().parent.parent / "exports")
    export_dir.mkdir(parents=True, exist_ok=True)

    export_path = export_dir / "analysis_package.json"
    export_path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    return export_path
