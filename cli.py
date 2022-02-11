"""CLI for dependency-inspector."""
import json
from pathlib import Path
from typing import Optional
import typer
from db.ElasticWorker import connect_elasticsearch
from error import LanguageNotSupportedError, VCSNotSupportedError
import configparser
import logging

from inspector import make_multiple_requests

app = typer.Typer(add_completion=False)
configfile = configparser.ConfigParser()


@app.callback(invoke_without_command=True)
def main(
        lang: Optional[str] = typer.Option(None),
        packages: Optional[str] = typer.Option(None),
        config: Optional[Path] = typer.Option(None),
        gh_token: Optional[str] = typer.Option(None),
        host: Optional[str] = typer.Option(None),
        port: Optional[int] = typer.Option(None),
        es_uid: Optional[str] = typer.Option(None),
        es_pass: Optional[str] = typer.Option(None)
):
    """
    Dependency Inspector

    Retrieves licenses and dependencies of Python, JavaScript and Go packages.
    Uses Package Indexes for Python and Javascript
    Go is temporarily handled by scraping pkg.go.dev and VCS
    VCS support is currently limited to GitHub for fallthrough cases in Go
    Parameters such as auth tokens and passwords can be defined in config.ini
    rather than specifying as an argument

    :param lang: go, python or javascript

    :param packages: list of packages to check

    :param config: Specify location of a .ini file | refer config.ini sample

    :param host: Host info for Elastic server

    :param port: Port info for Elastic server

    :param es_uid: Username for authenticating Elastic

    :param es_pass: Password to authenticate Elastic

    :param gh_token: GitHub token to authorize VCS and bypass rate limit
    """
    payload = {}
    if config is not None:
        if not config.is_file():
            logging.error("Configuration file not found")
            raise typer.Exit(code=-1)
        configfile.read(config)
        es_uid = es_uid or configfile.get("secrets", "es_uid", fallback=None)
        es_pass = es_pass or configfile.get("secrets", "es_pass", fallback=None)
        gh_token = gh_token or configfile.get("secrets", "gh_token", fallback=None)
        if not configfile.has_section("dependencies"):
            logging.error("dependencies section missing from config file")
            raise typer.Exit(code=-1)
        payload = configfile["dependencies"]
    else:
        if lang not in ["go", "python", "javascript"]:
            logging.error("Please specify a supported language!")
            raise typer.Exit(code=-1)
        payload[lang] = packages
    if host and port:
        es = connect_elasticsearch({'host': host, 'port': port}, (es_uid, es_pass))
    else:
        logging.warning("Elastic not connected")
        es = None
    for language, dependencies in payload.items():
        dep_list = dependencies.replace(',', '\n').split('\n')
        dep_list = list(filter(None, dep_list))
        try:
            if dep_list:
                logging.info(
                    json.dumps(
                        make_multiple_requests(
                            es, language, dep_list, gh_token
                        ),
                        indent=3
                    )
                )
        except (LanguageNotSupportedError, VCSNotSupportedError) as e:
            logging.error(e.msg)
            raise typer.Exit(code=-1)


if __name__ == "__main__":
    logging.getLogger().setLevel(logging.INFO)
    app()
