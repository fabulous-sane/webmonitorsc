import asyncio
from datetime import datetime
import httpx
import time
import socket
import ipaddress
import logging
from dataclasses import dataclass
from urllib.parse import urlparse
from typing import Optional, Tuple

from app.core.config import settings
from app.core.http_client import client
from app.utils.ssl_util import get_ssl_info

logger = logging.getLogger(__name__)


@dataclass
class CheckRawResult:
    reachable: bool
    status_code: int | None
    response_time_ms: int | None
    error_type: str | None = None

    ssl_valid: bool | None = None
    ssl_expires_at: datetime | None = None
    ssl_days_left: int | None = None
    ssl_error: str | None = None


def _is_private_host(host: str | None) -> bool:
    if not host:
        return True

    try:
        infos = socket.getaddrinfo(host, None)

        for info in infos:
            ip_str = info[4][0]
            ip = ipaddress.ip_address(ip_str)

            if (
                ip.is_private
                or ip.is_loopback
                or ip.is_reserved
                or ip.is_multicast
                or ip.is_link_local
            ):
                return True

        return False

    except Exception:
        return True


def _map_ssl(
    ssl_data: Optional[dict],
) -> Tuple[Optional[bool], Optional[datetime], Optional[int], Optional[str]]:
    if ssl_data is None:
        return None, None, None, None

    return (
        ssl_data.get("ssl_valid"),
        ssl_data.get("ssl_expires_at"),
        ssl_data.get("ssl_days_left"),
        ssl_data.get("ssl_error"),
    )

async def _safe_ssl(host: str | None, scheme: str):
    if not host or scheme != "https":
        return None

    return await get_ssl_info(host)

async def run_check(url: str) -> CheckRawResult:
    parsed = urlparse(url)
    ssl_data = None
    if parsed.scheme not in ("http", "https"):
        return CheckRawResult(False, None, None, "invalid_scheme")

    if _is_private_host(parsed.hostname):
        return CheckRawResult(False, None, None, "blocked_private_ip")

    for attempt in range(settings.RETRY_COUNT):
        try:
            start = time.monotonic()

            response = await client.get(url)

            duration = int((time.monotonic() - start) * 1000)

            final_url = urlparse(str(response.url))
            host = final_url.hostname or parsed.hostname

            if _is_private_host(host):
                return CheckRawResult(False, None, None, "blocked_private_ip")

            if ssl_data is None or ssl_data.get("ssl_valid") is None:
                ssl_data = await _safe_ssl(host, final_url.scheme)

            ssl_valid, ssl_expires_at, ssl_days_left, ssl_error = _map_ssl(ssl_data)

            return CheckRawResult(
                reachable=True,
                status_code=response.status_code,
                response_time_ms=duration,
                error_type=None,
                ssl_valid=ssl_valid,
                ssl_expires_at=ssl_expires_at,
                ssl_days_left=ssl_days_left,
                ssl_error=ssl_error,
            )

        except (httpx.TimeoutException, httpx.ConnectError, httpx.RequestError) as e:

            if attempt == settings.RETRY_COUNT - 1:
                error_type = (
                    "timeout"
                    if isinstance(e, httpx.TimeoutException)
                    else "connection_error"
                    if isinstance(e, httpx.ConnectError)
                    else "request_error"
                )
                if ssl_data is None:
                    ssl_data = await _safe_ssl(parsed.hostname, parsed.scheme)

                ssl_valid, ssl_expires_at, ssl_days_left, ssl_error = _map_ssl(ssl_data)

                return CheckRawResult(
                    reachable=False,
                    status_code=None,
                    response_time_ms=None,
                    error_type=error_type,
                    ssl_valid=ssl_valid,
                    ssl_expires_at=ssl_expires_at,
                    ssl_days_left=ssl_days_left,
                    ssl_error=ssl_error,
                )

            await asyncio.sleep(settings.BACKOFF_BASE * (2 ** attempt))

    if ssl_data is None:
        ssl_data = await _safe_ssl(parsed.hostname, parsed.scheme)

    ssl_valid, ssl_expires_at, ssl_days_left, ssl_error = _map_ssl(ssl_data)

    return CheckRawResult(
        False,
        None,
        None,
        "timeout",
        ssl_valid,
        ssl_expires_at,
        ssl_days_left,
        ssl_error,
    )