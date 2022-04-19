"""Functions to handle JavaScript files"""
import json

import yaml
from pyarn import lockfile


def handle_yarn_lock(req_file_data: str) -> dict:
    """
    Parse yarn lock file
    :param req_file_data: Content of yarn.lock
    :return: list of requirement and specs
    """
    res = {}
    if "lockfile v1" in req_file_data:
        parsed_lockfile = lockfile.Lockfile.from_str(req_file_data)
        unfiltered_content: dict = json.loads(parsed_lockfile.to_json())
    else:
        unfiltered_content = yaml.safe_load(req_file_data)
    keys = ["resolution", "dependencies"]
    for name, obj in unfiltered_content.items():
        flat = {}
        gen = (x for x in keys if x in obj)
        for k in gen:
            if isinstance(obj[k], dict):
                flat[k] = list(
                    map(lambda x: str(x[0]) + ";" + str(x[1]), obj[k].items())
                )
            else:
                flat[k] = obj[k]
        res[name] = flat
    return res


def handle_json(req_file_data: str) -> dict:
    """
    Parse json files generated by npm or yarn
    :param req_file_data: Content of package.json
    :return: list of requirement and specs
    """
    package_data = json.loads(req_file_data)
    filter_dict = {
        "name": "",
        "version": "",
        "license": "",
        "dependencies": {},
        "engines": {},
    }
    for k, v in package_data.items():
        if k in filter_dict:
            filter_dict[k] = v
    filtered_dep = filter_dict.get("dependencies")
    if any(isinstance(i, dict) for i in filtered_dep.values()):
        dependency_data = {
            k: v.get("version", "")
            for k, v in filtered_dep.items()
            if isinstance(v, dict)
        }
        filter_dict["dependencies"] = dependency_data
    return filter_dict
