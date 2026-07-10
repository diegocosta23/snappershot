from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


class ZipService:
    """
    Skapar ZIP-filer med SnapperShots screenshots.
    """

    def create_zip(
        self,
        zip_path: str | Path,
        files: Iterable[str | Path],
        base_dir: str | Path | None = None,
    ) -> Path:

        zip_path = Path(zip_path)
        base_dir_path = Path(base_dir).resolve() if base_dir is not None else None

        zip_path.parent.mkdir(parents=True, exist_ok=True)

        with ZipFile(zip_path, "w", compression=ZIP_DEFLATED) as archive:

            for file in files:

                file_path = Path(file)

                if file_path.exists():
                    arcname = file_path.name
                    if base_dir_path is not None:
                        try:
                            arcname = file_path.resolve().relative_to(base_dir_path).as_posix()
                        except ValueError:
                            arcname = file_path.name
                    archive.write(
                        file_path,
                        arcname=arcname,
                    )

        return zip_path
