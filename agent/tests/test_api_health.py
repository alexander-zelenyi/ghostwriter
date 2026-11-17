import logging

import pytest

from ghostwriter_agent.api.access_log import (
    ACCESS_LOGGER,
    HealthCheckFilter,
    hide_health_checks_from_access_log,
)
from tests.conftest import ServiceFactory, api_client


@pytest.mark.parametrize("path", ["/livez", "/readyz"])
async def test_health_check_needs_no_token(make_service: ServiceFactory, path: str) -> None:
    service, model = make_service([])

    async with api_client(service, token=None) as client:
        response = await client.get(path)

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert model.calls == []


def access_record(path: str) -> logging.LogRecord:
    """A record shaped like the ones uvicorn writes to its access logger."""
    return logging.LogRecord(
        ACCESS_LOGGER,
        logging.INFO,
        __file__,
        0,
        '%s - "%s %s HTTP/%s" %d',
        ("127.0.0.1:5000", "GET", path, "1.1", 200),
        None,
    )


@pytest.mark.parametrize("path", ["/livez", "/readyz", "/readyz?probe=1"])
def test_health_checks_are_dropped_from_access_log(path: str) -> None:
    assert not HealthCheckFilter().filter(access_record(path))


@pytest.mark.parametrize("path", ["/v1/threads/t1/messages", "/livez-not", "/docs"])
def test_other_requests_stay_in_access_log(path: str) -> None:
    assert HealthCheckFilter().filter(access_record(path))


def test_record_without_args_is_kept() -> None:
    record = logging.LogRecord(ACCESS_LOGGER, logging.INFO, __file__, 0, "plain", None, None)

    assert HealthCheckFilter().filter(record)


def test_filter_is_added_once() -> None:
    hide_health_checks_from_access_log()
    hide_health_checks_from_access_log()

    filters = logging.getLogger(ACCESS_LOGGER).filters
    assert sum(isinstance(f, HealthCheckFilter) for f in filters) == 1
