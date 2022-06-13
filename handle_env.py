"""Functions that require environment variables to be defined"""

import logging
import os

from dotenv import load_dotenv
from github import Github
from psycopg2 import OperationalError, connect

from error import ParamMissing

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


def get_db():
    """
    Returns an authenticated Postgres connection
    """
    conn = None
    if "PG_HOSTNAME" in os.environ:
        HOSTNAME = os.environ.get("PG_HOSTNAME")
        DATABASE = os.environ.get("PG_DATABASE")
        USERNAME = os.environ.get("PG_USERNAME")
        PWD = os.environ.get("PG_PWD")
        PORT_ID = os.environ.get("PG_PORT_ID")
        TABLE_NAME = os.environ.get("TABLE_NAME")
        req_var = {
            'PG_DATABASE': DATABASE,
            'PG_USERNAME': USERNAME,
            'PG_PORT_ID': PORT_ID,
            'TABLE_NAME': TABLE_NAME
        }
        for v in req_var:
            if not req_var[v]:
                raise ParamMissing(v)
        try:
            conn = connect(
                host=HOSTNAME,
                dbname=DATABASE,
                user=USERNAME,
                password=PWD,
                port=PORT_ID,
            )
        except OperationalError as error:
            logging.error(error)
    return conn
