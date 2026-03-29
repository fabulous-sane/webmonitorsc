import asyncio

import httpx
import time
import socket
import ipaddress
from dataclasses import dataclass
from urllib.parse import urlparse

from app.core.config import settings
from app.core.http_client import client


@dataclass
class CheckRawResult:
    reachable: bool
    status_code: int | None
    response_time_ms: int | None
    error_type: str | None = None


def _is_private_host(host: str | None) -> bool:
    if not host:
        return True

    try:
        ip = ipaddress.ip_address(socket.gethostbyname(host))
        return (
            ip.is_private
            or ip.is_loopback
            or ip.is_reserved
            or ip.is_multicast
        )
    except Exception:
        return True


async def run_check(url: str) -> CheckRawResult:
    parsed = urlparse(url)

    if parsed.scheme not in ("http", "https"):
        return CheckRawResult(
            reachable=False,
            status_code=None,
            response_time_ms=None,
            error_type="invalid_scheme",
        )

    if _is_private_host(parsed.hostname):
        return CheckRawResult(
            reachable=False,
            status_code=None,
            response_time_ms=None,
            error_type="blocked_private_ip",
        )

    for attempt in range(settings.RETRY_COUNT):
        try:
            start = time.monotonic()
            response = await client.get(url)
            duration = int((time.monotonic() - start) * 1000)

            return CheckRawResult(
                reachable=True,
                status_code=response.status_code,
                response_time_ms=duration,
                error_type=None,
            )

        except httpx.TimeoutException:
            await asyncio.sleep(settings.BACKOFF_BASE * (2 ** attempt))

        except httpx.RequestError:
            return CheckRawResult(
            reachable=False,
            status_code=None,
            response_time_ms=None,
            error_type="request_error",
        )

    return CheckRawResult(
        reachable=False,
        status_code=None,
        response_time_ms=None,
        error_type="timeout",
    )
