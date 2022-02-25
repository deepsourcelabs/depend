"""VCS Handler for GitHub"""

import datetime
import logging
import re
import time
from typing import Optional
import github.GithubException
from github import Github
import constants
from helper import parse_license, Result, handle_dep_file


def handle_github(
        language: str,
        dependency: str,
        result: Result,
        gh_token: Optional[str]
):
    """VCS fallthrough for GitHub based GO"""
    # VERIFY_RUN_REQUIRED
    if gh_token is None:
        logging.warning("Proceeding without GitHub Authentication")
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
    files = repo.get_contents("", commit_branch_tag)
    license_filename = "LICENSE"
    for f in files:
        if f.name in constants.LICENSE_FILES:
            license_filename = f.name
            break
    try:
        lic_file = repo.get_contents(
            license_filename,
            ref=commit_branch_tag
        ).decoded_content.decode()
    except github.GithubException:
        lic_file = ""
    repo_lic = parse_license(
        lic_file,
        constants.LICENSE_DICT
    )
    if repo_lic == "Other":
        repo_lic = repo.get_license().license.name
    releases = [release.tag_name for release in repo.get_releases()]
    if not releases:
        logging.error("No releases found, defaulting to tags")
        releases = [tag.name for tag in repo.get_tags()]
    logging.info(releases)
    req_filename = "requirements.txt"
    for f in files:
        if f.name in constants.REQ_FILES[language]:
            req_filename = f.name
            break
    try:
        dep_file = repo.get_contents(
            req_filename,
            ref=commit_branch_tag
        ).decoded_content.decode()
    except github.GithubException:
        dep_file = ""
    result['pkg_name'] = dependency
    result['pkg_ver'] = commit_branch_tag or releases[0]
    result['pkg_lic'] = repo_lic
    result['pkg_dep'] = handle_dep_file(
        req_filename, dep_file
    ).get("pkg_dep", [])
