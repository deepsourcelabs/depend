"""CLI for murdock."""
import json
import logging
import os.path
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import typer

from dependencies.helper import handle_dep_file, parse_dep_response
from error import LanguageNotSupportedError, ParamMissing, VCSNotSupportedError
from handle_env import get_db
from inspector import make_multiple_requests

app = typer.Typer(add_completion=False)


@app.callback(invoke_without_command=True)
def main(
    lang: str = typer.Option(...),
    packages: Optional[str] = typer.Option(None),
    dep_file: Optional[Path] = typer.Option(None),
    max_depth: Optional[int] = typer.Option(None),
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

    :param max_depth: dependency query recursion level

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
        if max_depth == 0:
            logging.info(result)
            return result
    else:
        payload[lang] = packages
    if lang not in ["go", "python", "javascript"]:
        raise LanguageNotSupportedError(lang)
    if psql := get_db():
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
                result.extend(
                    make_multiple_requests(psql, language, dep_list, max_depth)
                )
        except (LanguageNotSupportedError, VCSNotSupportedError, ParamMissing) as e:
            logging.error(e.msg)
            sys.exit(-1)
    logging.info(json.dumps(result, indent=3))
    return result


if __name__ == "__main__":
    logging.getLogger().setLevel(logging.INFO)
    app()
