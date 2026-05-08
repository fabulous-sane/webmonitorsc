from app.utils.ssl_state import resolve_ssl_state


def test_ssl_ok():
    assert resolve_ssl_state(True, None, "https://a.com", None) == "ok"


def test_ssl_invalid():
    assert resolve_ssl_state(False, None, "https://a.com", None) == "invalid"


def test_ssl_warning():
    assert resolve_ssl_state(True, "expiring", "https://a.com", None) == "warning"


def test_ssl_http():
    assert resolve_ssl_state(True, None, "http://a.com", None) == "http"

def test_ssl_critical():
    assert resolve_ssl_state(True, "critical", "https://a.com", None) == "critical"


def test_ssl_error_invalid():
    assert resolve_ssl_state(None, None, "https://a.com", "cert_invalid") == "invalid"


def test_ssl_error_timeout():
    assert resolve_ssl_state(None, None, "https://a.com", "timeout") == "no_data"


def test_ssl_error_handshake():
    assert resolve_ssl_state(None, None, "https://a.com", "handshake_error") == "no_data"


def test_ssl_no_data():
    assert resolve_ssl_state(None, None, "https://a.com", None) == "no_data"