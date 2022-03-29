"""Functions that require environment variables to be defined"""

import  os, logging
from github import Github
from dotenv import load_dotenv
import psycopg2.extras

load_dotenv()

if "GITHUB_TOKEN" in os.environ:
    gh_token = os.environ.get("GITHUB_TOKEN")
else:
    gh_token = None
    logging.warning("Proceeding without GitHub Authentication")
github_object = Github(gh_token)


conn = None
if "HOSTNAME" in os.environ:
    HOSTNAME    = os.environ.get("HOSTNAME")
    DATABASE    = os.environ.get("DATABASE")
    USERNAME    = os.environ.get("USERNAME")
    PWD         = os.environ.get("PWD")
    PORT_ID     = os.environ.get("PORT_ID")
    try:
        conn = psycopg2.connect(
            host = HOSTNAME,
            dbname = DATABASE,
            user = USERNAME,
            password = PWD,
            port = PORT_ID
        )
    except Exception as error:
        logging.error(error)


def get_github():
    """
    Returns an authenticated GitHub object if env variable is defined
    """
    return github_object


def get_db():
    """
    Returns an authenticated Postgres connection
    """
    return conn