from dataclasses import dataclass
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from app.utils.ssl_state import resolve_ssl_state
from app.models.site import Site
from app.monitoring.status import SiteStatus
from app.monitoring.run_check import CheckRawResult
from app.repositories.checks import ChecksRepository
from app.repositories.check_results import CheckResultsRepository
from app.core.config import settings
from app.monitoring.health_calc import compute_health
from app.monitoring.health import HealthStatus

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
    ssl_valid: bool | None = None
    health: HealthStatus | None = None

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

    # --- 1. MAP STATUS ---
    if raw.error_type == "timeout":
        raw_status = SiteStatus.TIMEOUT
    elif raw.error_type in ("connection_error", "request_error"):
        raw_status = SiteStatus.ERROR
    elif raw.status_code in (401, 403):
        raw_status = SiteStatus.UP
    elif raw.status_code and raw.status_code >= 500:
        raw_status = SiteStatus.DOWN
    elif raw.status_code and raw.status_code >= 400:
        raw_status = SiteStatus.ERROR
    else:
        raw_status = SiteStatus.UP

    await checks_repo.add_result(
        site_id=site.id,
        status=raw_status,
        status_code=raw.status_code,
        response_time_ms=raw.response_time_ms,
        ssl_valid=raw.ssl_valid,
        ssl_expires_at=raw.ssl_expires_at,
        ssl_days_left=raw.ssl_days_left,
        ssl_warning=raw.ssl_warning,
    )

    ssl_state = resolve_ssl_state(
        raw.ssl_valid,
        raw.ssl_warning,
        site.url,
    )

    current_health = compute_health(raw_status, ssl_state)

    if raw_status in (SiteStatus.DOWN, SiteStatus.ERROR, SiteStatus.TIMEOUT):
        threshold = settings.FLAP_DOWN_THRESHOLD
    else:
        threshold = settings.FLAP_UP_THRESHOLD

    threshold = max(threshold, 1)

    last_statuses = await checks_repo.get_last_statuses(
        site_id=site.id,
        limit=threshold,
    )

    http_stable = (
            len(last_statuses) == threshold
            and all(s == raw_status for s in last_statuses)
    )

    old_status = site.last_status
    new_status = raw_status if http_stable else (old_status or raw_status)

    status_changed = new_status != old_status

    if status_changed:
        site.last_status = new_status

    ssl_changed = False

    if not site.url.startswith("http://"):

        last_rows = await results_repo.get_last_ssl_states(site.id, limit=3)

        states = [
            resolve_ssl_state(v, w, site.url)
            for v, w in last_rows
        ]

        if ssl_state in ("critical", "invalid"):
            threshold = settings.FLAP_DOWN_THRESHOLD
        else:
            threshold = settings.FLAP_UP_THRESHOLD

        states = states[:threshold]

        threshold = max(threshold, 1)

        stable = (
                len(states) >= threshold
                and all(s == ssl_state for s in states[:threshold])
        )

        prev_state = None
        if len(last_rows) > 0:
            prev_valid, prev_warning = last_rows[0]
            prev_state = resolve_ssl_state(prev_valid, prev_warning, site.url)

        ssl_changed = (
                stable
                and prev_state is not None
                and prev_state != ssl_state
        )

    notify_payload = None

    if status_changed:
        notify_payload = NotifyPayload(
            site_id=site.id,
            site_name=site.name,
            url=site.url,
            old_status=old_status,
            new_status=new_status,
            status_code=raw.status_code,
            response_time_ms=raw.response_time_ms,
            ssl_warning=raw.ssl_warning,
            ssl_days_left=raw.ssl_days_left,
            ssl_valid=raw.ssl_valid,
            health=current_health,
        )


    elif ssl_changed:
        notify_payload = NotifyPayload(
            site_id=site.id,
            site_name=site.name,
            url=site.url,
            old_status=None,
            new_status=new_status,
            status_code=raw.status_code,
            response_time_ms=raw.response_time_ms,
            ssl_warning=raw.ssl_warning,
            ssl_days_left=raw.ssl_days_left,
            ssl_valid=raw.ssl_valid,
            health=current_health
        )

    return ProcessResult(
        status_changed=status_changed,
        old_status=old_status,
        new_status=new_status,
        notify_payload=notify_payload,
    )