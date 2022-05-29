"""CLI for murdock."""
import json
import logging
import os.path
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import typer

from dependencies.helper import handle_dep_file, parse_dep_response
from error import LanguageNotSupportedError, VCSNotSupportedError
from handle_env import get_db
from inspector import make_multiple_requests

app = typer.Typer(add_completion=False)


@app.callback(invoke_without_command=True)
def main(
    lang: str = typer.Option(None),
    packages: Optional[str] = typer.Option(None),
    dep_file: Optional[Path] = typer.Option(None),
    db_name: Optional[str] = typer.Option(None),
    deep_search: Optional[bool] = typer.Option(False),
) -> List[Any]:
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

    :param db_name: Postgres database to be used

    :param deep_search: when true populating all fields is attempted

    """
    payload: Dict[str, Union[None, str, list[str]]] = {}
    result: List[Any] = []
    if dep_file:
        payload = {}
        if not dep_file.is_file():
            logging.error("Dependency file cannot be read")
            sys.exit(-1)
        dep_content = handle_dep_file(os.path.basename(dep_file), dep_file.read_text())
        payload[lang] = dep_content.get("pkg_dep")
        result.append(parse_dep_response([dep_content]))
        if not deep_search:
            logging.info(result)
            return result
    else:
        payload[lang] = packages
    if lang not in ["go", "python", "javascript", "rust", "php", "cs"]:
        raise LanguageNotSupportedError(lang)
    if psql := get_db():
        if not db_name:
            logging.error("Please specify DB Name!")
            sys.exit(-1)
        logging.info("Postgres DB connected")
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
                result.extend(make_multiple_requests(psql, db_name, language, dep_list))

                logging.info(json.dumps(result, indent=3))
                return result
        except (LanguageNotSupportedError, VCSNotSupportedError) as e:
            logging.error(e.msg)
            sys.exit(-1)
    return []


if __name__ == "__main__":
    logging.getLogger().setLevel(logging.INFO)
    app()
