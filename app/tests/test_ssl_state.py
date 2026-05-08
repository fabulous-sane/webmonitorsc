from app.utils.ssl_state import resolve_ssl_state


def test_ssl_ok():
    assert resolve_ssl_state(True, None, "https://a.com", None) == "ok"


def test_ssl_invalid():
    assert resolve_ssl_state(False, None, "https://a.com", None) == "invalid"


def test_ssl_warning():
    assert resolve_ssl_state(True, "expiring", "https://a.com", None) == "warning"


def test_ssl_http():
    assert resolve_ssl_state(True, None, "http://a.com", None) == "http"