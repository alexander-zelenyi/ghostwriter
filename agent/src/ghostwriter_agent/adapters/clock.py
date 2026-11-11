from datetime import UTC, datetime


class SystemClock:
    """`Clock` adapter backed by the system clock."""

    def now(self) -> datetime:
        return datetime.now(UTC)
