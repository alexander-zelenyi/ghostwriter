import logging

HEALTH_CHECK_PATHS = frozenset({"/livez", "/readyz"})
ACCESS_LOGGER = "uvicorn.access"


class HealthCheckFilter(logging.Filter):
    """Drops uvicorn access records of health checks. Their args: (client, method, path, ...)."""

    def filter(self, record: logging.LogRecord) -> bool:
        args = record.args
        if isinstance(args, tuple) and len(args) >= 3:
            path = str(args[2]).partition("?")[0]
            return path not in HEALTH_CHECK_PATHS
        return True


def hide_health_checks_from_access_log() -> None:
    """Idempotent: the logger is global and `create_app` may run many times."""
    logger = logging.getLogger(ACCESS_LOGGER)
    if not any(isinstance(f, HealthCheckFilter) for f in logger.filters):
        logger.addFilter(HealthCheckFilter())
