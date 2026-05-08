def resolve_ssl_state(
    ssl_valid,
    ssl_warning,
    url: str,
    ssl_error: str | None = None,
) -> str:

    if url.startswith("http://") or ssl_error == "no_ssl":
        return "http"

    if ssl_error == "cert_invalid" or ssl_valid is False:
        return "invalid"

    if ssl_error in ("handshake_error", "timeout", "unknown"):
        return "no_data"

    if ssl_warning == "critical":
        return "critical"

    if ssl_warning in ("warning", "expiring"):
        return "warning"

    if ssl_valid is True:
        return "ok"

    return "no_data"