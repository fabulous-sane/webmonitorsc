from app.monitoring.health import HealthStatus

def compute_health(http_status: str | None, ssl_state: str) -> HealthStatus:

    if http_status in ("DOWN", "ERROR"):
        return HealthStatus.CRITICAL

    if http_status == "TIMEOUT":
        return HealthStatus.WARNING

    if ssl_state in ("critical", "invalid"):
        return HealthStatus.CRITICAL

    if ssl_state == "warning":
        return HealthStatus.WARNING

    if http_status is None:
        return HealthStatus.NO_DATA

    if ssl_state == "no_data":
        return HealthStatus.WARNING

    if ssl_state == "http":
        return HealthStatus.OK

    return HealthStatus.OK