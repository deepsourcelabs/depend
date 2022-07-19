"""Type hinting and request helper"""
from datetime import timedelta

from requests_cache import CachedSession

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


def red_req(url):
    """Request get with protection against 302 redirects"""
    response = requests.get(url)
    red_url = url
    if response.status_code == 200:
        # Handle 302: Redirection
        if response.history:
            red_url = response.url
            response = requests.get(red_url)
    return red_url, response
