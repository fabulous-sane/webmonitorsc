from enum import Enum

class HealthStatus(str, Enum):
    OK = "ok"
    WARNING = "warning"
    CRITICAL = "critical"
    NO_DATA = "no_data"