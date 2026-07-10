import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile
from unittest.mock import MagicMock, patch

from src.snappershot.controller.capture_pipeline import CapturePipeline
from src.snappershot.services.zip_service import ZipService


class CapturePipelineZipTests(unittest.TestCase):
    def test_includes_analysis_package_in_zip_inputs(self) -> None:
        pipeline = CapturePipeline()

        with tempfile.TemporaryDirectory() as temp_dir:
            output_folder = Path(temp_dir)
            screenshot = output_folder / "1D.png"
            screenshot.write_bytes(b"img")
            analysis_package = output_folder / "analysis_package.json"
            analysis_package.write_text("{}", encoding="utf-8")

            zip_inputs = pipeline._build_zip_inputs([screenshot], output_folder)

            self.assertEqual(zip_inputs, [screenshot, analysis_package])

    def test_zip_contains_analysis_package_file(self) -> None:
        zip_service = ZipService()

        with tempfile.TemporaryDirectory() as temp_dir:
            folder = Path(temp_dir)
            chart_dir = folder / "charts"
            chart_dir.mkdir()
            screenshots = []
            for name in ["1W.png", "1D.png", "4H.png", "45M.png"]:
                path = chart_dir / name
                path.write_bytes(b"img")
                screenshots.append(path)
            analysis_package = folder / "analysis_package.json"
            analysis_package.write_text("{}", encoding="utf-8")
            zip_path = folder / "company.zip"

            created = zip_service.create_zip(zip_path, [*screenshots, analysis_package], base_dir=folder)

            with ZipFile(created) as archive:
                self.assertEqual(
                    sorted(archive.namelist()),
                    [
                        "analysis_package.json",
                        "charts/1D.png",
                        "charts/1W.png",
                        "charts/45M.png",
                        "charts/4H.png",
                    ],
                )

    def test_pipeline_builds_chart_and_analysis_inputs(self) -> None:
        pipeline = CapturePipeline()

        with tempfile.TemporaryDirectory() as temp_dir:
            output_folder = Path(temp_dir)
            screenshots = [
                output_folder / "charts" / "1W.png",
                output_folder / "charts" / "1D.png",
            ]
            for path in screenshots:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(b"img")
            analysis_package = output_folder / "analysis_package.json"
            analysis_package.write_text("{}", encoding="utf-8")

            zip_inputs = pipeline._build_zip_inputs(screenshots, output_folder)

            self.assertEqual(zip_inputs, [*screenshots, analysis_package])


if __name__ == "__main__":
    unittest.main()
