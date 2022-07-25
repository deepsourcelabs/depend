"""VCS Handler for GitHub"""

import calendar
import logging
import re
import time
from typing import Iterable

import github.GithubException
from github.ContentFile import ContentFile

import depend.constants as constants
from depend.dependencies.helper import Result, handle_dep_file, parse_license
from depend.handle_env import get_github


def verify_run(language, result, file_extension="git") -> list[str]:
    """
    Check if analysis should be continued further
    :param language: language of package
    :param result: current version of result dict
    :param file_extension: optional filetype being checked
    """
    unavailable_keys = constants.DEP_FIELDS_MISSED.get(language, {}).get(
        file_extension, []
    )
    # If v is None that means pkg_dep was null from PyPI
    retrievable_keys = [
        k
        for k, v in result.items()
        if not v and v is not None and k not in unavailable_keys
    ]
    if result["pkg_lic"][0] == "Other" and "pkg_lic" not in unavailable_keys:
        retrievable_keys.append("pkg_lic")
    return retrievable_keys


def handle_github(
    language: str,
    dependency: str,
    result: Result,
):
    """VCS fallthrough for GitHub based GO"""
    # Check if run is actually required
    if retrievable_keys := verify_run(language, result):
        g = get_github()
        rl = g.get_rate_limit()
        reset_timestamp = calendar.timegm(rl.core.reset.timetuple())
        if rl.core.remaining == 0:
            logging.error("GitHub API limit exhausted - Sleeping")
            time.sleep(reset_timestamp - calendar.timegm(time.gmtime()) + 5)

        repo_identifier = re.search(
            r"github.com/([^/]+)/([^/\\\r\n\s]+)(?:/tree/|)?([^/.\\\r\n\s]+)?",
            dependency,
        )
        if repo_identifier:
            try:
                repo = g.get_repo(
                    repo_identifier.group(1) + "/" + repo_identifier.group(2)
                )
            except github.GithubException:
                logging.error(f"{dependency} cannot be parsed")
            else:
                commit_branch_tag = repo_identifier.group(3) or repo.default_branch
                try:
                    files = repo.get_contents("", commit_branch_tag)
                except github.GithubException:
                    commit_branch_tag = repo.default_branch
                    files = repo.get_contents("", commit_branch_tag)
                if isinstance(files, Iterable):
                    files_s = [str(f.name) for f in files]
                else:
                    files_s = []

                if "pkg_lic" in retrievable_keys:
                    license_filename = "LICENSE"
                    for f in files_s:
                        if f in constants.LICENSE_FILES:
                            license_filename = f
                            break
                    try:
                        repo_file_content = repo.get_contents(
                            license_filename, ref=commit_branch_tag
                        )
                        if isinstance(repo_file_content, ContentFile):
                            lic_file = repo_file_content.decoded_content.decode()
                        else:
                            lic_file = ""
                    except github.GithubException:
                        lic_file = ""
                    repo_lic = parse_license(lic_file, constants.LICENSE_DICT)
                    if repo_lic[0] == "Other":
                        try:
                            if r_lic := repo.get_license():
                                repo_lic = [r_lic.license.name]
                        except github.GithubException:
                            repo_lic = ["Other"]

                    result["pkg_lic"] = repo_lic

                if "pkg_name" in retrievable_keys:
                    result["pkg_name"] = dependency

                if "pkg_ver" in retrievable_keys:
                    releases = [release.tag_name for release in repo.get_releases()]
                    if not releases:
                        logging.error("No releases found, defaulting to tags")
                        releases = [tag.name for tag in repo.get_tags()]
                    logging.info(releases)
                    result["pkg_ver"] = commit_branch_tag or releases[0]

                req_files: list = constants.REQ_FILES[language]
                if ".nuspec" in req_files:
                    req_files.append(dependency + ".nuspec")
                for f in set(files_s).intersection(req_files):
                    req_filename = f
                    file_extension = req_filename.split(".")[-1]
                    if retrievable_keys := verify_run(language, result, file_extension):
                        try:
                            repo_file_content = repo.get_contents(
                                req_filename, ref=commit_branch_tag
                            )
                            if (
                                isinstance(repo_file_content, ContentFile)
                                and repo_file_content.encoding == "base64"
                            ):
                                dep_file = repo_file_content.decoded_content.decode()
                            else:
                                continue
                        except github.GithubException:
                            continue
                        dep_resp = handle_dep_file(req_filename, dep_file)
                        for key in retrievable_keys:
                            result[key] = dep_resp.get(key)  # type: ignore
                    else:
                        break
