"""Type hinting and request helper"""
from datetime import timedelta
from typing import Optional, TypedDict

from requests_cache import CachedSession


class Result(TypedDict):
    """Current result structure"""

    import_name: Optional[str]
    lang_ver: list[str]
    pkg_name: str
    pkg_ver: str
    pkg_lic: list[str]
    pkg_err: dict
    pkg_dep: list[str]
    timestamp: str


requests = CachedSession(
    "murdock_cache",
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