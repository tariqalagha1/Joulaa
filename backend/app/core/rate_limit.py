from slowapi import Limiter
from slowapi.util import get_remote_address

from .config import settings


# Use Redis as shared storage so limits work across app instances.
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["60/minute"],
    storage_uri=settings.REDIS_URL,
    headers_enabled=True,
)
