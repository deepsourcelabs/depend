"""CLI for murdock."""
import configparser
import json
import logging
import os.path
from pathlib import Path
from typing import Dict, Optional, Union

import typer

from db.elastic_worker import connect_elasticsearch
from dependencies.helper import handle_dep_file, parse_dep_response
from error import LanguageNotSupportedError, VCSNotSupportedError
from inspector import make_multiple_requests

app = typer.Typer(add_completion=False)
configfile = configparser.ConfigParser()


@app.callback(invoke_without_command=True)
def main(
    lang: str = typer.Option(None),
    packages: Optional[str] = typer.Option(None),
    dep_file: Optional[Path] = typer.Option(None),
    deep_search: Optional[bool] = typer.Option(False),
    config: Optional[Path] = typer.Option(None),
    host: Optional[str] = typer.Option(None),
    port: Optional[int] = typer.Option(None),
    es_uid: Optional[str] = typer.Option(None),
    es_pass: Optional[str] = typer.Option(None),
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

    """
    payload: Dict[str, Union[None, str, list]] = {}
    result = []
    if config is not None:
        if not config.is_file():
            logging.error("Configuration file not found")
            raise typer.Exit(code=-1)
        configfile.read(config)
        if not configfile.has_section("dependencies"):
            logging.error("dependencies section missing from config file")
            raise typer.Exit(code=-1)
        payload = dict(configfile["dependencies"])
    if dep_file is not None:
        payload = {}
        if not dep_file.is_file():
            logging.error("Dependency file cannot be read")
            raise typer.Exit(code=-1)
        dep_content = handle_dep_file(os.path.basename(dep_file), dep_file.read_text())
        payload[lang] = dep_content.get("pkg_dep")
        result.append(parse_dep_response([dep_content]))
        if not deep_search:
            logging.info(result)
            return result
    else:
        payload[lang] = packages
    if lang not in ["go", "python", "javascript"]:
        raise LanguageNotSupportedError(lang)
    if host and port:
        es = connect_elasticsearch({"host": host, "port": port}, (es_uid, es_pass))
    else:
        logging.warning("Elastic not connected")
        es = None
    for language, dependencies in payload.items():
        if isinstance(dependencies, str):
            dep_list = dependencies.replace(",", "\n").split("\n")
            dep_list = list(filter(None, dep_list))
        elif isinstance(dependencies, list):
            dep_list = dependencies
        else:
            dep_list = []
            logging.error("Unknown Response")
        try:
            if dep_list:
                result.extend(make_multiple_requests(es, language, dep_list))
                logging.info(json.dumps(result, indent=3))
                return result
        except (LanguageNotSupportedError, VCSNotSupportedError) as e:
            logging.error(e.msg)
            raise typer.Exit(code=-1)
    return []


if __name__ == "__main__":
    logging.getLogger().setLevel(logging.INFO)
    app()
