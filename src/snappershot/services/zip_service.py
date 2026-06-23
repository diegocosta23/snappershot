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
    ) -> Path:

        zip_path = Path(zip_path)

        zip_path.parent.mkdir(parents=True, exist_ok=True)

        with ZipFile(zip_path, "w", compression=ZIP_DEFLATED) as archive:

            for file in files:

                file_path = Path(file)

                if file_path.exists():
                    archive.write(
                        file_path,
                        arcname=file_path.name,
                    )

        return zip_path
