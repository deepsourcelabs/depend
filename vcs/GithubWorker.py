"""VCS Handler for Github"""

import time
from typing import Dict, List, Any, Optional
from github import Github
from helper import parse_license
import logging
import re
import Constants
import datetime


def handle_github(
        dependency: str,
        gh_token: Optional[str]
) -> Dict[str, str | List[Any]]:
    """VCS fallthrough for GitHub based GO"""
    g = Github(gh_token)
    result = {}
    rl = g.get_rate_limit()
    if rl.core.remaining == 0:
        logging.error("GitHub API limit exhausted - Sleeping")
        time.sleep(
            (
                    rl.core.reset - datetime.datetime.now()
            ).total_seconds()
        )
    repo_identifier = re.search(r"github.com/([^/]+)/([^/.\r\n]+)", dependency)
    repo = g.get_repo(repo_identifier.group(1) + "/" + repo_identifier.group(2))
    repo_license = repo.get_license()
    if repo_license.license.name == "Other":
        repo_lic = parse_license(
            repo_license.decoded_content.decode(),
            Constants.LICENSE_DICT
        )
    else:
        repo_lic = repo_license.license.name
    releases = [release.tag_name for release in repo.get_releases()]
    if len(releases) == 0:
        logging.error("No releases found, defaulting to tags")
        releases = [tag.name for tag in repo.get_tags()]
    logging.info(releases)
    dep_file = repo.get_contents("go.mod").decoded_content.decode()
    dep_data = re.findall(r"[\s/]+([^\s\n(]+)\s+v([^\s\n]+)", dep_file)
    data = dict(dep_data)
    result['name'] = dependency
    result['version'] = releases[0]
    result['license'] = repo_lic
    result['dependencies'] = list(data.items())
    return result
