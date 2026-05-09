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

@pytest.mark.asyncio
async def test_policy_blocked(session, site):
    raw = make_raw(error_type="blocked_private_ip")

    result = await process_check_result(
        session=session,
        site=site,
        raw=raw,
    )

    assert result.status_changed is False
    assert result.notify_payload is None

@pytest.mark.asyncio
async def test_403_is_up(session, site):
    raw = make_raw(status_code=403)

    result = await process_check_result(
        session=session,
        site=site,
        raw=raw,
    )

    assert result.new_status == SiteStatus.UP

@pytest.mark.asyncio
async def test_notify_payload_created(session, site):
    raw = make_raw(status_code=500)

    with patch(
        "app.repositories.checks.ChecksRepository.get_last_statuses",
        new=AsyncMock(return_value=[SiteStatus.DOWN, SiteStatus.DOWN])
    ):
        site.last_status = SiteStatus.UP
        result = await process_check_result(
            session=session,
            site=site,
            raw=raw,
        )

    assert result.notify_payload is not None

@pytest.mark.asyncio
async def test_no_notify_without_stable(session, site):
    raw = make_raw(status_code=500)

    with patch(
        "app.repositories.checks.ChecksRepository.get_last_statuses",
        new=AsyncMock(return_value=[SiteStatus.UP, SiteStatus.DOWN])
    ):
        result = await process_check_result(
            session=session,
            site=site,
            raw=raw,
        )

    assert result.notify_payload is None

@pytest.mark.asyncio
async def test_ssl_change(session, site):
    raw = make_raw(
        status_code=200,
        ssl_valid=True,
        ssl_warning="critical"
    )

    with patch(
        "app.repositories.check_results.CheckResultsRepository.get_last_ssl_states",
        new=AsyncMock(return_value=[
            (True, None, None),  # current
            (True, None, None),  # prev ok
        ])
    ):
        result = await process_check_result(
            session=session,
            site=site,
            raw=raw,
        )

    assert result.notify_payload is not None
    assert result.notify_payload.is_ssl_change is True

@pytest.mark.asyncio
async def test_ssl_not_stable(session, site):
    raw = make_raw(
        status_code=200,
        ssl_valid=True,
        ssl_warning="critical"
    )

    with patch(
        "app.repositories.check_results.CheckResultsRepository.get_last_ssl_states",
        new=AsyncMock(return_value=[
            (True, None, None),
        ])
    ):
        result = await process_check_result(
            session=session,
            site=site,
            raw=raw,
        )

    assert result.notify_payload is None

@pytest.mark.asyncio
async def test_http_changed_raw(session, site):
    site.last_status = SiteStatus.UP

    raw = make_raw(status_code=500)

    with patch(
        "app.repositories.checks.ChecksRepository.get_last_statuses",
        new=AsyncMock(return_value=[SiteStatus.DOWN, SiteStatus.DOWN])
    ):
        result = await process_check_result(
            session=session,
            site=site,
            raw=raw,
        )

    assert result.notify_payload.http_changed_raw is True

@pytest.mark.asyncio
async def test_prev_ssl_state(session, site):
    raw = make_raw(status_code=200, ssl_warning="critical")

    with patch(
        "app.repositories.check_results.CheckResultsRepository.get_last_ssl_states",
        new=AsyncMock(return_value=[
            (True, None, None),
            (True, "warning", None),
        ])
    ):
        result = await process_check_result(
            session=session,
            site=site,
            raw=raw,
        )

    assert result.notify_payload.prev_ssl_state == "warning"

@pytest.mark.asyncio
async def test_ssl_no_data(session, site):
    raw = make_raw(
        status_code=200,
        ssl_valid=None,
        ssl_warning=None,
    )

    with patch(
        "app.repositories.check_results.CheckResultsRepository.get_last_ssl_states",
        new=AsyncMock(return_value=[
            (None, None, None),
            (None, None, None),
        ])
    ):
        site.last_status = SiteStatus.UP
        result = await process_check_result(
            session=session,
            site=site,
            raw=raw,
        )

    assert result.notify_payload is None

@pytest.mark.asyncio
async def test_same_status_no_change(session, site):
    site.last_status = SiteStatus.UP

    raw = make_raw(status_code=200)

    result = await process_check_result(
        session=session,
        site=site,
        raw=raw,
    )

    assert result.status_changed is False
    assert result.notify_payload is None

@pytest.mark.asyncio
async def test_error_vs_down(session, site):
    raw = make_raw(status_code=503)

    result = await process_check_result(
        session=session,
        site=site,
        raw=raw,
    )

    assert result.new_status == SiteStatus.DOWN

@pytest.mark.asyncio
async def test_404_is_error(session, site):
    raw = make_raw(status_code=404)

    result = await process_check_result(
        session=session,
        site=site,
        raw=raw,
    )

    assert result.new_status == SiteStatus.ERROR

@pytest.mark.asyncio
async def test_ssl_invalid_trigger(session, site):
    raw = make_raw(
        status_code=200,
        ssl_valid=False
    )

    with patch(
        "app.repositories.check_results.CheckResultsRepository.get_last_ssl_states",
        new=AsyncMock(return_value=[
            (True, None, None),
            (True, None, None),
        ])
    ):
        result = await process_check_result(
            session=session,
            site=site,
            raw=raw,
        )

    assert result.notify_payload is not None

@pytest.mark.asyncio
async def test_http_and_ssl_change(session, site):
    from unittest.mock import AsyncMock, patch

    raw = make_raw(status_code=500, ssl_warning="critical")

    with patch(
        "app.repositories.checks.ChecksRepository.get_last_statuses",
        new=AsyncMock(return_value=[SiteStatus.DOWN, SiteStatus.DOWN])
    ), patch(
        "app.repositories.check_results.CheckResultsRepository.get_last_ssl_states",
        new=AsyncMock(return_value=[
            (True, None, None),
            (True, None, None),
        ])
    ):
        result = await process_check_result(
            session=session,
            site=site,
            raw=raw,
        )

    payload = result.notify_payload

    assert payload.http_changed is True
    assert payload.is_ssl_change is True

@pytest.mark.asyncio
async def test_ssl_recovery(session, site):
    from unittest.mock import AsyncMock, patch

    raw = make_raw(status_code=200, ssl_warning=None)

    with patch(
        "app.repositories.check_results.CheckResultsRepository.get_last_ssl_states",
        new=AsyncMock(return_value=[
            (True, "critical", None),
            (True, "critical", None),
        ])
    ):
        result = await process_check_result(
            session=session,
            site=site,
            raw=raw,
        )

    assert result.notify_payload is not None
    assert result.notify_payload.prev_ssl_state == "critical"

@pytest.mark.asyncio
async def test_payload_fields(session, site):
    raw = make_raw(status_code=500)

    with patch(
        "app.repositories.checks.ChecksRepository.get_last_statuses",
        new=AsyncMock(return_value=[SiteStatus.DOWN, SiteStatus.DOWN])
    ):
        site.last_status = SiteStatus.UP
        result = await process_check_result(
            session=session,
            site=site,
            raw=raw,
        )

    payload = result.notify_payload

    assert payload is not None
    payload = result.notify_payload
    assert payload.site_id == site.id
    assert payload.site_name == site.name
    assert payload.url == site.url