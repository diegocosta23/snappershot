from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import Any


class StepResult(Enum):
    """
    Resultatet från ett enskilt steg i Capture-pipelinen.
    """

    SUCCESS = auto()
    RETRY = auto()
    FAIL = auto()


@dataclass(slots=True)
class StepOutcome:
    """
    Gemensam returtyp för alla steg i SnapperShot.

    SUCCESS
        Steget lyckades.

    RETRY
        Steget kan försöka igen.

    FAIL
        Steget misslyckades permanent.
    """

    result: StepResult
    message: str = ""
    data: Any = None

    @classmethod
    def success(
        cls,
        message: str = "",
        data: Any = None,
    ) -> "StepOutcome":
        return cls(
            result=StepResult.SUCCESS,
            message=message,
            data=data,
        )

    @classmethod
    def retry(
        cls,
        message: str = "",
        data: Any = None,
    ) -> "StepOutcome":
        return cls(
            result=StepResult.RETRY,
            message=message,
            data=data,
        )

    @classmethod
    def fail(
        cls,
        message: str = "",
        data: Any = None,
    ) -> "StepOutcome":
        return cls(
            result=StepResult.FAIL,
            message=message,
            data=data,
        )

    @property
    def ok(self) -> bool:
        """
        True om steget lyckades.
        """
        return self.result is StepResult.SUCCESS

    @property
    def should_retry(self) -> bool:
        """
        True om steget bör försöka igen.
        """
        return self.result is StepResult.RETRY

    @property
    def failed(self) -> bool:
        """
        True om steget misslyckades permanent.
        """
        return self.result is StepResult.FAIL

    def __bool__(self) -> bool:
        """
        Gör att man kan skriva:

            if outcome:
                ...

        vilket motsvarar:

            if outcome.ok:
                ...
        """
        return self.ok

    def __repr__(self) -> str:
        return (
            f"StepOutcome("
            f"result={self.result.name}, "
            f"message={self.message!r}, "
            f"data={self.data!r})"
        )
