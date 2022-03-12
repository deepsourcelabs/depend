"""CLI for dependency-inspector."""
import json
import os.path
from pathlib import Path
from typing import Optional
import typer
from db.elastic_worker import connect_elasticsearch
from error import LanguageNotSupportedError, VCSNotSupportedError
from helper import parse_dep_response, handle_dep_file
import configparser
import logging

from inspector import make_multiple_requests

app = typer.Typer(add_completion=False)
configfile = configparser.ConfigParser()


@app.callback(invoke_without_command=True)
def main(
        lang: Optional[str] = typer.Option(None),
        packages: Optional[str] = typer.Option(None),
        dep_file: Optional[Path] = typer.Option(None),
        deep_search: Optional[bool] = typer.Option(False),
        config: Optional[Path] = typer.Option(None),
        gh_token: Optional[str] = typer.Option(None),
        host: Optional[str] = typer.Option(None),
        port: Optional[int] = typer.Option(None),
        es_uid: Optional[str] = typer.Option(None),
        es_pass: Optional[str] = typer.Option(None)
) -> list:
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

    :param dep_file: location of file to parse for packages

    :param deep_search: when true populating all fields is attempted

    :param config: Specify location of a .ini file | refer config.ini sample

    :param host: Host info for Elastic server

    :param port: Port info for Elastic server

    :param es_uid: Username for authenticating Elastic

    :param es_pass: Password to authenticate Elastic

    :param gh_token: GitHub token to authorize VCS and bypass rate limit
    """
    payload = {}
    result = []
    if config is not None:
        if not config.is_file():
            logging.error("Configuration file not found")
            raise typer.Exit(code=-1)
        configfile.read(config)
        es_uid = configfile.get("secrets", "es_uid", fallback=None) or es_uid
        es_pass = configfile.get("secrets", "es_pass", fallback=None) or es_pass
        gh_token = configfile.get("secrets", "gh_token", fallback=None) or gh_token
        if not configfile.has_section("dependencies"):
            logging.error("dependencies section missing from config file")
            raise typer.Exit(code=-1)
        payload = configfile["dependencies"]
    if dep_file is not None:
        payload = {}
        if not dep_file.is_file():
            logging.error("Dependency file cannot be read")
            raise typer.Exit(code=-1)
        dep_content = handle_dep_file(
            os.path.basename(dep_file), dep_file.read_text(), gh_token
        )
        payload[lang] = dep_content.get("pkg_dep")
        # pkg_name = dep_content.get("pkg_name")
        # pkg_ver = dep_content.get("pkg_ver")
        result.append(parse_dep_response([dep_content]))
        if not deep_search:
            logging.info(result)
            return result
    else:
        payload[lang] = packages
        # pkg_name = ""
        # pkg_ver = ""
    if lang not in ["go", "python", "javascript"]:
        logging.error("Please specify a supported language!")
        raise typer.Exit(code=-1)
    if host and port:
        es = connect_elasticsearch({'host': host, 'port': port}, (es_uid, es_pass))
    else:
        logging.warning("Elastic not connected")
        es = None
    for language, dependencies in payload.items():
        if isinstance(dependencies, str):
            dep_list = dependencies.replace(',', '\n').split('\n')
            dep_list = list(filter(None, dep_list))
        elif isinstance(dependencies, list):
            dep_list = dependencies
        else:
            dep_list = []
            logging.error("Unknown Response")

        try:

            if dep_list:
                # if pkg_name:
                # result[pkg_name]["versions"][pkg_ver]["pkg_dep"] = make_multiple_requests(
                #     es, language, dep_list, gh_token
                # )
                result.extend(make_multiple_requests(
                    es, language, dep_list, gh_token
                ))

                logging.info(
                    json.dumps(
                        result,
                        indent=3
                    )
                )
                return result
        except (LanguageNotSupportedError, VCSNotSupportedError) as e:
            logging.error(e.msg)
            raise typer.Exit(code=-1)


if __name__ == "__main__":
    logging.getLogger().setLevel(logging.INFO)
    app()
