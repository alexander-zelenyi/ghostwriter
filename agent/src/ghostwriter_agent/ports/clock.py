from datetime import datetime
from typing import Protocol, runtime_checkable


@runtime_checkable
class Clock(Protocol):
    """Source of the current time."""

    def now(self) -> datetime:
        """Return the current timezone-aware datetime."""
        ...
