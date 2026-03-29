# app/monitoring/status.py
from enum import Enum

class SiteStatus(str, Enum):
    UP = "UP"
    DOWN = "DOWN"
