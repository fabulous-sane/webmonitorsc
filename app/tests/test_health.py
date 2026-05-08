from app.monitoring.health_calc import compute_health


def test_health_ok():
    assert compute_health("UP", "ok") == "ok"


def test_health_warning_ssl():
    assert compute_health("UP", "warning") == "warning"


def test_health_critical_ssl():
    assert compute_health("UP", "critical") == "critical"


def test_health_critical_status():
    assert compute_health("DOWN", "ok") == "critical"


def test_health_timeout():
    assert compute_health("TIMEOUT", "ok") == "critical"