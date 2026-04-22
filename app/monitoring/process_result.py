from dataclasses import dataclass
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.site import Site
from app.monitoring.status import SiteStatus
from app.monitoring.run_check import CheckRawResult
from app.repositories.checks import ChecksRepository
from app.repositories.check_results import CheckResultsRepository
from app.core.config import settings

@dataclass
class NotifyPayload:
    site_id: UUID
    site_name: str
    url: str
    old_status: SiteStatus | None
    new_status: SiteStatus
    status_code: int | None
    response_time_ms: int | None

    ssl_warning: str | None = None
    ssl_days_left: int | None = None

@dataclass
class ProcessResult:
    status_changed: bool
    old_status: SiteStatus | None
    new_status: SiteStatus
    notify_payload: NotifyPayload | None

async def process_check_result(
    *,
    session: AsyncSession,
    site: Site,
    raw: CheckRawResult,
) -> ProcessResult:

    checks_repo = ChecksRepository(session)
    results_repo = CheckResultsRepository(session)
    policy_errors = {"blocked_private_ip", "invalid_scheme"}

    if raw.error_type in policy_errors:
        return ProcessResult(False, site.last_status, site.last_status, None)

    if raw.error_type == "timeout":
        raw_status = SiteStatus.TIMEOUT
    elif raw.error_type in ("connection_error", "request_error"):
        raw_status = SiteStatus.ERROR
    elif raw.status_code in (403, 401):
        raw_status = SiteStatus.UP
    elif raw.status_code and raw.status_code >= 500:
        raw_status = SiteStatus.DOWN
    elif raw.status_code and raw.status_code >= 400:
        raw_status = SiteStatus.ERROR
    else:
        raw_status = SiteStatus.UP

    ssl_warning = None

    if raw.ssl_days_left is not None:
        if raw.ssl_days_left <= settings.SSL_CRITICAL_DAYS:
            ssl_warning = "critical"
        elif raw.ssl_days_left <= settings.SSL_WARNING_DAYS:
            ssl_warning = "warning"

    await checks_repo.add_result(
        site_id=site.id,
        status=raw_status,
        status_code=raw.status_code,
        response_time_ms=raw.response_time_ms,
        ssl_valid=raw.ssl_valid,
        ssl_expires_at=raw.ssl_expires_at,
        ssl_days_left=raw.ssl_days_left,
        ssl_error=raw.ssl_error,
        ssl_warning=ssl_warning,
    )

    threshold = (
        settings.FLAP_DOWN_THRESHOLD
        if raw_status == SiteStatus.DOWN
        else settings.FLAP_UP_THRESHOLD
    )
    threshold = max(threshold, 1)

    if threshold == 1:
        stable = True
    else:
        last_statuses = await checks_repo.get_last_statuses(
            site_id=site.id,
            limit=threshold,
        )
        stable = (
                len(last_statuses) == threshold
                and all(s == raw_status for s in last_statuses)
        )

    old_status = site.last_status
    status_changed = stable and (old_status != raw_status)

    if status_changed:
        site.last_status = raw_status

    latest_ssl = await results_repo.get_latest_ssl(site_id=site.id)

    def _ssl_state(valid, warning):
        if valid is None and warning is None:
            return "no_data"
        if warning == "critical":
            return "critical"
        if warning == "warning":
            return "warning"
        if valid is False:
            return "invalid"
        return "ok"

    prev_state = (
        _ssl_state(latest_ssl["ssl_valid"], latest_ssl["ssl_warning"])
        if latest_ssl
        else "no_data"
    )

    curr_state = _ssl_state(raw.ssl_valid, ssl_warning)

    ssl_changed = (
            curr_state != prev_state
            and not (curr_state == "no_data" and prev_state == "no_data")
    )

    notify_payload = None

    if status_changed or ssl_changed:
        notify_payload = NotifyPayload(
            site_id=site.id,
            site_name=site.name,
            url=site.url,
            old_status=old_status,
            new_status=raw_status,
            status_code=raw.status_code,
            response_time_ms=raw.response_time_ms,
            ssl_warning=ssl_warning,
            ssl_days_left=raw.ssl_days_left,
        )

    return ProcessResult(
        status_changed=status_changed,
        old_status=old_status,
        new_status=raw_status,
        notify_payload=notify_payload,
    )