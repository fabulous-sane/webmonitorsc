from dataclasses import dataclass
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.site import Site
from app.monitoring.status import SiteStatus
from app.monitoring.run_check import CheckRawResult
from app.repositories.checks import ChecksRepository
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

    policy_errors = {"blocked_private_ip", "invalid_scheme"}

    if raw.error_type in policy_errors:
        return ProcessResult(
            status_changed=False,
            old_status=site.last_status,
            new_status=site.last_status,
            notify_payload=None,
        )

    if not raw.reachable or raw.status_code is None:
        raw_status = SiteStatus.DOWN
    elif raw.status_code >= 500:
        raw_status = SiteStatus.DOWN
    else:
        raw_status = SiteStatus.UP

    await checks_repo.add_result(
        site_id=site.id,
        status=raw_status,
        status_code=raw.status_code,
        response_time_ms=raw.response_time_ms,
    )

    if raw_status == SiteStatus.DOWN:
        threshold = settings.FLAP_DOWN_THRESHOLD
    else:
        threshold = settings.FLAP_UP_THRESHOLD

    threshold = max(threshold, 1)

    last_statuses = await checks_repo.get_last_statuses(
        site_id=site.id,
        limit=threshold,
    )

    stable = (
        len(last_statuses) == threshold
        and all(s == raw_status for s in last_statuses)
    )

    old_status = site.last_status
    status_changed = stable and old_status != raw_status

    if status_changed:
        site.last_status = raw_status

    notify_payload = None
    if status_changed:
        notify_payload = NotifyPayload(
            site_id=site.id,
            site_name=site.name,
            url=site.url,
            old_status=old_status,
            new_status=raw_status,
            status_code=raw.status_code,
            response_time_ms=raw.response_time_ms,
        )

    return ProcessResult(
        status_changed=status_changed,
        old_status=old_status,
        new_status=raw_status,
        notify_payload=notify_payload,
    )