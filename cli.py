"""CLI for dependency-inspector."""
import json
from pathlib import Path
from typing import Optional
import typer
from db.ElasticWorker import connect_elasticsearch
import configparser
import logging

from inspector import make_multiple_requests

app = typer.Typer(add_completion=False)
configfile = configparser.ConfigParser()


@app.callback(invoke_without_command=True)
def main(
        config: Optional[Path] = typer.Option(None),
        host: str = typer.Option("localhost"),
        port: int = typer.Option(9200), es_db: bool = False,
        gh_token: Optional[str] = typer.Option(None),
        es_uid: Optional[str] = typer.Option(None),
        es_pass: Optional[str] = typer.Option(None)
):
    """
    Dependency Inspector

    Retrieves licenses and dependencies of Python, JavaScript and Go packages.
    Uses Package Indexes for Python and Javascript
    Go is temporarily handled by scraping go.pkg.dev and VCS
    VCS support is currently limited to GitHub for fallthrough cases in Go
    Parameters such as auth tokens and passwords can be defined in config.ini
    rather than specifying as an argument

    :param config: Specify location of a .ini file | refer config.ini sample

    :param es_db: pass --es-db to link to Elastic instance

    :param host: Host info for Elastic server

    :param port: Port info for Elastic server

    :param es_uid: Username for authenticating Elastic

    :param es_pass: Password to authenticate Elastic

    :param gh_token: GitHub token to authorize VCS and bypass rate limit
    """
    if config is None or not config.is_file():
        logging.error("Configuration file not found")
        raise typer.Abort()
    configfile.read(config)
    if gh_token is None and configfile.has_option("secrets", "gh_token"):
        gh_token = configfile.get("secrets", "gh_token").strip()
    if es_uid is None and configfile.has_option("secrets", "es_uid"):
        es_uid = configfile.get("secrets", "es_uid").strip()
    if es_pass is None and configfile.has_option("secrets", "es_pass"):
        es_pass = configfile.get("secrets", "es_pass").strip()
    if es_db:
        es = connect_elasticsearch({'host': host, 'port': port}, (es_uid, es_pass))
    else:
        es = None
    if not configfile.has_section("dependencies"):
        logging.error("dependencies section missing from config file")
        raise typer.Abort()
    for lang, dependencies in configfile["dependencies"].items():
        dep_list = dependencies.split("\n")
        dep_list = list(filter(None, dep_list))
        if dep_list:
            logging.info(
                json.dumps(
                    make_multiple_requests(
                        es, lang, dep_list, gh_token
                    ),
                    indent=3
                )
            )


if __name__ == "__main__":
    logging.getLogger().setLevel(logging.INFO)
    app()
