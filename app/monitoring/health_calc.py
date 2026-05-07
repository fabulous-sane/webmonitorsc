from app.monitoring.status import SiteStatus
from app.monitoring.health import HealthStatus


def compute_health(http_status, ssl_state):

    if http_status == SiteStatus.DOWN:
        return HealthStatus.CRITICAL

    if http_status == SiteStatus.ERROR:
        return HealthStatus.CRITICAL

    if http_status == SiteStatus.TIMEOUT:
        return HealthStatus.WARNING

    if ssl_state == "critical":
        return HealthStatus.CRITICAL

    if ssl_state == "warning":
        return HealthStatus.WARNING

    if http_status == SiteStatus.UP:
        return HealthStatus.OK

    return HealthStatus.NO_DATA