import pytest
from unittest.mock import AsyncMock, patch

from app.monitoring.process_result import process_check_result
from app.monitoring.status import SiteStatus
from app.monitoring.run_check import CheckRawResult


def make_raw(
    status_code=None,
    error_type=None,
    ssl_valid=True,
    ssl_warning=None,
    ssl_days_left=100,
    reachable=True,
):
    return CheckRawResult(
        reachable=reachable,
        status_code=status_code,
        response_time_ms=100,
        error_type=error_type,
        ssl_valid=ssl_valid,
        ssl_warning=ssl_warning,
        ssl_days_left=ssl_days_left,
        ssl_error=None,
    )


@pytest.mark.asyncio
async def test_http_500(session, site):
    raw = make_raw(status_code=500)

    result = await process_check_result(session=session, site=site, raw=raw)

    assert result.new_status == SiteStatus.DOWN


@pytest.mark.asyncio
async def test_timeout(session, site):
    raw = make_raw(error_type="timeout")

    result = await process_check_result(session=session, site=site, raw=raw)

    assert result.new_status == SiteStatus.TIMEOUT


@pytest.mark.asyncio
async def test_antiflapping(session, site):
    raw = make_raw(status_code=500)

    with patch(
        "app.repositories.checks.ChecksRepository.get_last_statuses",
        new=AsyncMock(return_value=[
            SiteStatus.UP,
            SiteStatus.DOWN,
        ])
    ):
        result = await process_check_result(session=session, site=site, raw=raw)

    assert result.status_changed is False


@pytest.mark.asyncio
async def test_recovery(session, site):
    site.last_status = SiteStatus.DOWN

    raw = make_raw(status_code=200)

    with patch(
        "app.repositories.checks.ChecksRepository.get_last_statuses",
        new=AsyncMock(return_value=[
            SiteStatus.UP,
            SiteStatus.UP,
        ])
    ):
        result = await process_check_result(session=session, site=site, raw=raw)

    assert result.new_status == SiteStatus.UP
    assert result.status_changed is True