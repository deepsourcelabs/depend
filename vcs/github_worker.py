"""VCS Handler for GitHub"""

import datetime
import logging
import re
import time
from typing import Optional, Literal
import github.GithubException
from github import Github
import constants
from helper import parse_license, Result, handle_dep_file


def verify_run(language, result, file_extension="git") -> list[str]:
    """
    Check if analysis should be continued further
    :param language: language of package
    :param result: current version of result dict
    :param file_extension: optional filetype being checked
    """
    unavailable_keys = constants.DEP_FIELDS_MISSED.get(
        language, {}
    ).get(file_extension, [])
    retrievable_keys = [
        k for k, v in result.items()
        if not v and k not in unavailable_keys
    ]
    return retrievable_keys


def handle_github(
        language: str,
        dependency: str,
        result: Result,
        gh_token: Optional[str],
):
    """VCS fallthrough for GitHub based GO"""
    if retrievable_keys := verify_run(language, result):

        if not gh_token:
            gh_token = None
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
        try:
            files = repo.get_contents("", commit_branch_tag)
        except github.GithubException:
            commit_branch_tag = repo.default_branch
            files = repo.get_contents("", commit_branch_tag)
        files = [f.name for f in files]

        if "pkg_lic" in retrievable_keys:
            license_filename = "LICENSE"
            for f in files:
                if f in constants.LICENSE_FILES:
                    license_filename = f
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
                if r_lic := repo.get_license():
                    repo_lic = r_lic.license.name
            result['pkg_lic'] = repo_lic

        if "pkg_name" in retrievable_keys:
            result['pkg_name'] = dependency

        if "pkg_ver" in retrievable_keys:
            releases = [release.tag_name for release in repo.get_releases()]
            if not releases:
                logging.error("No releases found, defaulting to tags")
                releases = [tag.name for tag in repo.get_tags()]
            logging.info(releases)
            result['pkg_ver'] = commit_branch_tag or releases[0]

        req_files = constants.REQ_FILES[language]
        for f in files:
            if f in req_files:
                req_filename = f
                file_extension = req_filename.split(".")[-1]
                if retrievable_keys := verify_run(language, result, file_extension):
                    try:
                        dep_file = repo.get_contents(
                            req_filename,
                            ref=commit_branch_tag
                        ).decoded_content.decode()
                    except github.GithubException:
                        continue
                    dep_resp = handle_dep_file(
                        req_filename, dep_file, gh_token
                    )
                    for key in retrievable_keys:
                        key: Literal[
                            "import_name",
                            "lang_ver", "pkg_name",
                            "pkg_ver", "pkg_lic",
                            "pkg_err", "pkg_dep",
                            'timestamp'
                        ]
                        result[key] = dep_resp.get(key)
