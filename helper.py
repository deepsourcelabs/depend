"""Helper Functions for Inspector"""

from typing import TypedDict, List


def parse_license(license_file: str, license_dict: dict) -> str:
    """
    Checks the license file contents to return possible license type
    :param license_file: String containing license file contents
    :param license_dict: Dictionary mapping license files and unique substring
    :return: Detected license type as a String, Other if failed to detect
    """
    for lic in license_dict:
        if lic in license_file:
            return license_dict[lic]
    return "Other"


class Result(TypedDict):
    """Type hinting for results"""

    name: str
    version: str
    license: str
    dependencies: List[str]
    timestamp: str
