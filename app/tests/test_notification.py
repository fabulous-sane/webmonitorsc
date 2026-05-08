from uuid import uuid4
import pytest

from app.services.notification_service import NotificationService
from app.monitoring.process_result import NotifyPayload
from app.monitoring.status import SiteStatus
from app.monitoring.health import HealthStatus


@pytest.mark.asyncio
async def test_format_http_change():
    payload = NotifyPayload(
        site_id=uuid4(),
        site_name="test",
        url="https://a.com",
        old_status=SiteStatus.UP,
        new_status=SiteStatus.DOWN,
        status_code=500,
        response_time_ms=100,
        http_changed=True,
        http_changed_raw=True,
        error_type=None,
        ssl_valid=True,
        ssl_warning=None,
        ssl_days_left=10,
        ssl_error=None,
        is_ssl_change=False,
        ssl_changed_raw=False,
        prev_ssl_state=None,
        health=HealthStatus.CRITICAL,
    )

    text = NotificationService._format_status(payload)

    assert "Працює → Недоступний" in text
    assert "HTTP" in text


@pytest.mark.asyncio
async def test_format_ssl_change():
    payload = NotifyPayload(
        site_id=uuid4(),
        site_name="test",
        url="https://a.com",
        old_status=SiteStatus.UP,
        new_status=SiteStatus.UP,
        status_code=200,
        response_time_ms=100,
        http_changed=False,
        http_changed_raw=False,
        error_type=None,
        ssl_valid=True,
        ssl_warning="critical",
        ssl_days_left=5,
        ssl_error=None,
        is_ssl_change=True,
        ssl_changed_raw=True,
        prev_ssl_state="ok",
        health=HealthStatus.CRITICAL,
    )

    text = NotificationService._format_status(payload)

    assert "SSL" in text
    assert "OK → Критично" in text