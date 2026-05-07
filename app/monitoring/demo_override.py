from app.monitoring.run_check import CheckRawResult

def extract_demo_mode(site) -> str | None:
    if site.name and site.name.startswith("demo:"):
        return site.name.split("demo:")[1]
    return None


def apply_demo_override(site, raw: CheckRawResult) -> CheckRawResult:
    demo = extract_demo_mode(site)

    if not demo:
        return raw

    if demo == "http_down":
        raw.status_code = 500
        raw.error_type = None

    elif demo == "http_timeout":
        raw.status_code = None
        raw.error_type = "timeout"


    elif demo == "ssl_critical":
        raw.ssl_valid = True
        raw.ssl_days_left = 1
        raw.ssl_warning = "critical"
        raw.ssl_error = None
        raw.status_code = 200

    elif demo == "ssl_warning":
        raw.ssl_valid = True
        raw.ssl_days_left = 5
        raw.ssl_warning = "warning"

    elif demo == "ssl_invalid":
        raw.ssl_valid = False
        raw.ssl_days_left = None
        raw.ssl_warning = None

    elif demo == "ssl_ok":
        raw.ssl_valid = True
        raw.ssl_days_left = 90
        raw.ssl_warning = None

    return raw