import asyncio

from app.core.config import settings

check_semaphore = asyncio.Semaphore(settings.MAX_CONCURRENT_CHECKS)
