from app.monitoring.health import HealthStatus

def normalize_health(h):
    if isinstance(h, HealthStatus):
        return h.value
    if h in ("critical", "warning", "ok", "no_data"):
        return h
    return "no_data"