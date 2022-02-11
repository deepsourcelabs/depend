"""Functions to handle Python files"""
from pkg_resources import parse_requirements

from dependencies.py.setup_reader import LaxSetupReader


def handle_requirements_txt(req_file_data: str) -> list:
    """
    Parse requirements file
    :param req_file_data: Content of requirements.txt
    :return: list of requirement and specs
    """
    install_reqs = parse_requirements(req_file_data)
    return [
        [ir.key, ir.specs]
        for ir in install_reqs
    ]


def handle_setup_py(req_file_data: str) -> dict:
    """
    Parse setup.cfg
    :param req_file_data: Content of setup.py
    :return: dict containing dependency info and specs
    """
    parser = LaxSetupReader()
    return parser.read_setup_py(req_file_data)
