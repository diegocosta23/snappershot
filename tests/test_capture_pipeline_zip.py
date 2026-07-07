import tempfile
import unittest
from pathlib import Path

from src.snappershot.controller.capture_pipeline import CapturePipeline


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


if __name__ == "__main__":
    unittest.main()
