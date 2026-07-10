import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile

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
            screenshot = folder / "1D.png"
            screenshot.write_bytes(b"img")
            analysis_package = folder / "analysis_package.json"
            analysis_package.write_text("{}", encoding="utf-8")
            zip_path = folder / "company.zip"

            created = zip_service.create_zip(zip_path, [screenshot, analysis_package])

            with ZipFile(created) as archive:
                self.assertEqual(
                    sorted(archive.namelist()),
                    ["1D.png", "analysis_package.json"],
                )


if __name__ == "__main__":
    unittest.main()
