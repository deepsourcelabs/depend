"""VCS Handler for Github"""

import datetime
import logging
import re
import time
from typing import Optional
from github import Github
import github.GithubException
import Constants
from helper import parse_license, Result


def handle_github(
        dependency: str,
        result: Result,
        gh_token: Optional[str]
):
    """VCS fallthrough for GitHub based GO"""
    if gh_token is None:
        logging.warning("Proceeding without Github Authentication")
    g = Github(gh_token)
    rl = g.get_rate_limit()
    if rl.core.remaining == 0:
        logging.error("GitHub API limit exhausted - Sleeping")
        time.sleep(
            (
                    rl.core.reset - datetime.datetime.now()
            ).total_seconds()
        )
    repo_identifier = re.search(
        r"github.com/([^/]+)/([^/.\r\n]+)(?:/tree/|)?([^/.\r\n]+)?",
        dependency
    )
    repo = g.get_repo(repo_identifier.group(1) + "/" + repo_identifier.group(2))
    commit_branch_tag = repo_identifier.group(3) or repo.default_branch
    try:
        lic_file = repo.get_contents(
            "LICENSE",
            ref=commit_branch_tag
        ).decoded_content.decode()
    except github.GithubException:
        lic_file = ""
    repo_lic = parse_license(
        lic_file,
        Constants.LICENSE_DICT
    )
    if repo_lic == "Other":
        repo_lic = repo.get_license().license.name
    releases = [release.tag_name for release in repo.get_releases()]
    if not releases:
        logging.error("No releases found, defaulting to tags")
        releases = [tag.name for tag in repo.get_tags()]
    logging.info(releases)
    try:
        dep_file = repo.get_contents(
            "go.mod",
            ref=commit_branch_tag
        ).decoded_content.decode()
    except github.GithubException:
        dep_file = ""
    dep_data = re.findall(
        r"[\s/]+[\"|\']?([^\s\n(\"\']+)[\"|\']?\s+[\"|\']?v([^\s\n]+)[\"|\']?",
        dep_file
    )
    result['name'] = dependency
    result['version'] = commit_branch_tag or releases[0]
    result['license'] = repo_lic
    result['dependencies'] = dep_data
