def resolve_ssl_state(
    ssl_valid,
    ssl_warning,
    url: str,
    ssl_error: str | None = None,
) -> str:

    if url.startswith("http://"):
        return "http"

    # ❗ КРИТИЧНО: timeout ≠ invalid
    if ssl_error == "timeout":
        return "no_data"

    if ssl_warning == "critical":
        return "critical"

    if ssl_warning == "warning":
        return "warning"

    if ssl_valid is False:
        return "invalid"

    if ssl_valid is True:
        return "ok"

    return "no_data"