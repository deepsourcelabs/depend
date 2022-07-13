"""Functions that require environment variables to be defined"""

import logging
import os

from dotenv import load_dotenv
from github import Github

load_dotenv()

if "GITHUB_TOKEN" in os.environ:
    gh_token = os.environ.get("GITHUB_TOKEN")
    if not gh_token:
        gh_token = None
else:
    gh_token = None
    logging.warning("Proceeding without GitHub Authentication")
github_object = Github(gh_token)


def get_github():
    """
    Returns an authenticated GitHub object if env variable is defined
    """
    return github_object
