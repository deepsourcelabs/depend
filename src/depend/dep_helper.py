"""Type hinting and request helper"""
from datetime import timedelta

from requests_cache import CachedSession
from requests_futures.sessions import FuturesSession

cached_requests = CachedSession(
    "depend_cache",
    use_cache_dir=True,  # Save files in the default user cache dir
    cache_control=True,  # Use Cache-Control headers for expiration, if available
    expire_after=timedelta(days=1),  # Otherwise expire responses after one day
    allowable_methods=[
        "GET",
        "POST",
    ],  # Cache POST requests to avoid sending the same data twice
    allowable_codes=[200, 400],  # Cache 400 responses as well
    match_headers=True,  # Match all request headers
)
requests = FuturesSession(session=cached_requests, max_workers=10)
