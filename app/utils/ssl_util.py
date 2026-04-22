import ssl
import math
import socket
import asyncio
import logging
from datetime import datetime, timezone

from app.core.config import settings

logger = logging.getLogger(__name__)

def compute_ssl_warning(days_left: int | None) -> str | None:
    if days_left is None:
        return None
    if days_left <= settings.SSL_CRITICAL_DAYS:
        return "critical"
    if days_left <= settings.SSL_WARNING_DAYS:
        return "warning"
    return None

def _get_ssl_info_sync(hostname: str, port: int = 443):
    if not hostname:
        raise ValueError("Empty hostname")

    context = ssl.create_default_context()
    context.check_hostname = True
    context.verify_mode = ssl.CERT_REQUIRED

    with socket.create_connection((hostname, port), timeout=3) as sock:
        with context.wrap_socket(sock, server_hostname=hostname) as ssock:
            cert = ssock.getpeercert()

    expires_str = cert.get("notAfter")

    if not expires_str:
        raise ValueError("No expiration in cert")

    expires_at = datetime.strptime(
        expires_str, "%b %d %H:%M:%S %Y %Z"
    ).replace(tzinfo=timezone.utc)

    now = datetime.now(timezone.utc)

    is_expired = expires_at <= now
    delta = expires_at - now
    days_left = max(math.ceil(delta.total_seconds() / 86400), 0)
    warning = compute_ssl_warning(days_left)

    return {
        "ssl_valid": not is_expired,
        "ssl_expires_at": expires_at,
        "ssl_days_left": days_left,
        "ssl_warning": warning,
        "ssl_error": None,
    }

async def get_ssl_info(hostname: str):
    try:
        return await asyncio.wait_for(
            asyncio.to_thread(_get_ssl_info_sync, hostname),
            timeout=5,
        )

    except asyncio.TimeoutError:
        return {
            "ssl_valid": False,
            "ssl_expires_at": None,
            "ssl_days_left": None,
            "ssl_warning": None,
            "ssl_error": "timeout",
        }

    except ssl.SSLCertVerificationError:
        return {
            "ssl_valid": False,
            "ssl_expires_at": None,
            "ssl_days_left": None,
            "ssl_warning": None,
            "ssl_error": "cert_invalid",
        }

    except ssl.SSLError:
        return {
            "ssl_valid": False,
            "ssl_expires_at": None,
            "ssl_days_left": None,
            "ssl_warning": None,
            "ssl_error": "ssl_error",
        }

    except Exception:
        return {
            "ssl_valid": False,
            "ssl_expires_at": None,
            "ssl_days_left": None,
            "ssl_warning": None,
            "ssl_error": "unknown",
        }
