"""CLI for murdock."""
import json
import logging
import os.path
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import coloredlogs
import typer
from rich import print as rprint

from depend.dependencies.helper import handle_dep_file, parse_dep_response
from depend.error import LanguageNotSupportedError, ParamMissing, VCSNotSupportedError
from depend.inspector import make_multiple_requests

app = typer.Typer()
coloredlogs.install(
    level="WARNING", fmt="%(name)s[%(process)d] %(levelname)s %(message)s"
)


@app.callback(invoke_without_command=True)
def main(
    lang: str = typer.Option(..., help="python, javascript, go, cs, php, rust"),
    packages: Optional[str] = typer.Option(None, help="rich;latest,pygit2;~=1.9.2,..."),
    dep_file: Optional[Path] = typer.Option(None, help="Absolute or Relative Path"),
    depth: Optional[int] = typer.Option(None, help="Recursive resolution by default"),
) -> List[Any]:
    """
    Dependency Inspector

    Retrieves licenses and dependencies of Python, JavaScript, C#, PHP, Rust and Go packages.
    Uses Package Indexes for Python and Javascript
    Go is temporarily handled by scraping pkg.go.dev and VCS
    VCS support is currently limited to GitHub for fallthrough cases in Go
    Parameters such as auth tokens and passwords can be defined in config.ini
    rather than specifying as an argument

    :param lang: language associated with the packages or dependency file

    :param packages: list of packages to check

    :param dep_file: location of file to parse for packages

    :param depth: dependency query recursion level

    """
    payload: Dict[str, Union[None, str, list[str]]] = {}
    result: List[Any] = []
    file_extension = ""
    if dep_file:
        payload = {}
        if not dep_file.is_file():
            logging.error("Dependency file cannot be read")
            sys.exit(-1)
        file_extension = os.path.basename(dep_file).split(".")[-1]
        dep_content = handle_dep_file(os.path.basename(dep_file), dep_file.read_text())
        payload[lang] = dep_content.get("pkg_dep")
        result.append(parse_dep_response([dep_content]))
        if depth == 0:
            rprint(result)
            return result
    elif packages:
        payload[lang] = packages
    else:
        logging.error("Nothing to process please specify either dep_file or packages")
        sys.exit(-1)
    if lang not in ["go", "python", "javascript", "rust", "php", "cs"]:
        raise LanguageNotSupportedError(lang)
    for language, dependencies in payload.items():
        if isinstance(dependencies, str):
            dep_list = dependencies.replace(",", "\n").split("\n")
            dep_list = list(filter(None, dep_list))
        elif isinstance(dependencies, list):
            dep_list = dependencies
        else:
            dep_list = []
        try:
            if file_extension == "lock":
                # For a lockfile, we just want to fetch details of the dependencies
                # given, and not recurse any further. Hence depth=1
                result.extend(make_multiple_requests(language, dep_list, depth=1))
            else:
                result.extend(make_multiple_requests(language, dep_list, depth))
        except (LanguageNotSupportedError, VCSNotSupportedError, ParamMissing) as e:
            logging.error(e.msg)
            sys.exit(-1)
    rprint(json.dumps(result, indent=3))
    return result
