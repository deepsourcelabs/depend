"""Type definitions for murdock"""
from typing import Optional, TypedDict


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
