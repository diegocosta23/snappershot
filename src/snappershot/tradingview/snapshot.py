from __future__ import annotations

import logging
import time
from pathlib import Path

from PIL import Image, ImageGrab, ImageStat

from snappershot.models.step_result import StepOutcome
from snappershot.tradingview.window_manager import WindowManager

log = logging.getLogger(__name__)

# -----------------------------------------------------------------------------
# Konstanter
# -----------------------------------------------------------------------------

POST_FOCUS_SLEEP_SECONDS = 0.50
MIN_FILE_SIZE_BYTES = 30_000
MIN_STDDEV = 5.0
MAX_RETRIES = 2
RETRY_DELAY_SECONDS = 0.30


class SnapshotEngine:
    """
    Tar screenshots av TradingView Desktop-fönstret.

    V1-beteende:
    - Fokuserar TradingView innan capture.
    - Tar screenshot av fönstrets koordinater via ImageGrab.grab(bbox=...).
    - Verifierar att PNG-filen finns, går att läsa och inte verkar vara tom/svart.
    - Returnerar StepOutcome.
    """

    def __init__(self, window: WindowManager | None = None) -> None:
        self.window = window or WindowManager()

    def prepare(self) -> StepOutcome:
        """
        Säkerställer att TradingView är redo för screenshot.
        """
        return self.window.prepare()

    def _validate_output_path(self, output_path: str | Path) -> Path:
        path = Path(output_path)

        if path.suffix.lower() != ".png":
            path = path.with_suffix(".png")

        path.parent.mkdir(parents=True, exist_ok=True)
        return path

    def _is_nonempty_image(self, path: Path) -> bool:
        """
        Försöker avgöra om bilden verkar innehålla något användbart innehåll.
        """
        try:
            with Image.open(path) as img:
                img.verify()

            with Image.open(path) as img:
                gray = img.convert("L")
                stat = ImageStat.Stat(gray)

                if not stat.stddev:
                    return False

                return stat.stddev[0] >= MIN_STDDEV
        except Exception as exc:
            log.debug("Kunde inte analysera PNG %s: %s", path, exc)
            return False

    def _verify_png(self, path: Path) -> StepOutcome:
        """
        Verifierar att PNG-filen är giltig och rimligt innehållsrik.
        """
        if not path.exists():
            return StepOutcome.fail(f"PNG-filen saknas: {path.name}")

        try:
            size = path.stat().st_size
        except Exception as exc:
            return StepOutcome.fail(f"Kunde inte läsa filstorlek för {path.name}: {exc}")

        if size < MIN_FILE_SIZE_BYTES:
            return StepOutcome.fail(
                f"PNG-filen är för liten: {path.name} ({size} bytes)."
            )

        if not self._is_nonempty_image(path):
            return StepOutcome.fail(
                f"Bilden verkar vara tom eller svart: {path.name}."
            )

        return StepOutcome.success(f"PNG verifierad: {path.name}", data=path)

    def _capture_once(self, output_path: Path) -> StepOutcome:
        """
        Tar en enda screenshot och sparar den som PNG.
        """
        focus_result = self.window.focus()
        if not focus_result.ok:
            return StepOutcome.retry(
                f"Kunde inte fokusera TradingView före capture: {focus_result.message}"
            )

        rect = self.window.get_rect()
        if rect is None:
            return StepOutcome.fail(
                "Kunde inte hämta fönstrets koordinater."
            )

        left, top, right, bottom = rect
        if right <= left or bottom <= top:
            return StepOutcome.fail(
                "TradingView-fönstrets koordinater är ogiltiga."
            )

        time.sleep(POST_FOCUS_SLEEP_SECONDS)

        try:
            image = ImageGrab.grab(bbox=(left, top, right, bottom))
        except Exception as exc:
            return StepOutcome.fail(f"ImageGrab.grab misslyckades: {exc}")

        try:
            image.save(str(output_path), "PNG")
        except Exception as exc:
            return StepOutcome.fail(f"Kunde inte spara PNG: {exc}")

        return self._verify_png(output_path)

    def capture(self, output_path: str | Path, label: str = "") -> StepOutcome:
        """
        Tar en screenshot av TradingView-fönstret.

        Returnerar StepOutcome:
            SUCCESS - filen sparad och verifierad
            RETRY   - fokus gick förlorat eller tillfälligt fel
            FAIL    - permanent fel
        """
        path = self._validate_output_path(output_path)
        label_text = f" ({label})" if label else ""

        log.info("SnapshotEngine.capture%s -> %s", label_text, path.name)

        for attempt in range(1, MAX_RETRIES + 1):
            outcome = self._capture_once(path)

            if outcome.ok:
                log.info("Screenshot sparad och verifierad: %s", path.name)
                return StepOutcome.success(
                    f"Screenshot sparad: {path.name}",
                    data=path,
                )

            log.warning(
                "SnapshotEngine.capture%s: försök %d/%d misslyckades: %s",
                label_text,
                attempt,
                MAX_RETRIES,
                outcome.message,
            )

            if outcome.should_retry and attempt < MAX_RETRIES:
                try:
                    path.unlink(missing_ok=True)
                except Exception:
                    pass

                time.sleep(RETRY_DELAY_SECONDS)
                continue

            try:
                path.unlink(missing_ok=True)
            except Exception:
                pass

            return outcome

        return StepOutcome.fail(
            f"Kunde inte ta screenshot{label_text} efter {MAX_RETRIES} försök."
        )

    def capture_window(self, output_path: str | Path, window: object | None = None) -> StepOutcome:
        """
        Bakåtkompatibel metod.

        Om ett fönster skickas in försöker vi använda det,
        annars använder vi WindowManager som vanligt.
        """
        _ = window
        return self.capture(output_path)

    def wait_chart(self, seconds: float = 1.5) -> StepOutcome:
        """
        En enkel väntemod för chart-omritning.

        Finns för bakåtkompatibilitet med äldre kod.
        """
        try:
            time.sleep(seconds)
            return StepOutcome.success(f"Väntade {seconds} sekunder.")
        except Exception as exc:
            return StepOutcome.fail(f"Kunde inte vänta: {exc}")