"""Functions to handle JavaScript files"""
import json
from datetime import datetime

import yaml
from pyarn import lockfile


def handle_yarn_lock(req_file_data: str) -> dict:
    """
    Parse yarn lock file
    :param req_file_data: Content of yarn.lock
    :return: list of requirement and specs
    """
    res = {
        "lang_ver": [],
        "pkg_name": "",
        "pkg_ver": "",
        "pkg_lic": ["Other"],
        "pkg_err": {},
        "pkg_dep": [],
        "timestamp": datetime.utcnow().isoformat(),
    }
    if "lockfile v1" in req_file_data:
        parsed_lockfile = lockfile.Lockfile.from_str(req_file_data)
        unfiltered_content: dict = json.loads(parsed_lockfile.to_json())
    else:
        unfiltered_content = yaml.safe_load(req_file_data)
    for package in unfiltered_content.keys():
        if package.startswith("_"):
            continue
        res["pkg_dep"].append(
            str(package.split(",")[0].rsplit("@", 1)[0])
            + ";"
            + str(unfiltered_content[package].get("version", ""))
        )
    return res


def handle_json(req_file_data: str) -> dict:
    """
    Parse json files generated by npm or yarn
    :param req_file_data: Content of package.json
    :return: list of requirement and specs
    """
    package_data = json.loads(req_file_data)
    filter_dict = {
        "lang_ver": [package_data.get("engines", {}).get("node", "")],
        "pkg_name": package_data.get("name", ""),
        "pkg_ver": package_data.get("version", ""),
        "pkg_lic": package_data.get("license", "Other").split(","),
        "pkg_dep": package_data.get("dependencies", {}),
        "timestamp": datetime.utcnow().isoformat(),
    }
    for k, v in filter_dict.items():
        if k == "pkg_dep":
            handle_json_dep(filter_dict, k, v)
        elif k not in ["lang_ver", "pkg_lic"]:
            flatten_content(filter_dict, k, v)
    filter_dict["pkg_err"] = {}
    return filter_dict


def handle_json_dep(filter_dict, k, v):
    """
    Flattens variants of dependencies to uniform
    :param filter_dict: any dict or list
    :param k: key to check
    :param v: associated value
    """
    if any(isinstance(i, dict) for i in v.values()):
        filter_dict[k] = [i + ";" + v[i].get("version", "") for i in v.keys()]
    else:
        filter_dict[k] = [";".join(i) for i in v.items()]


def flatten_content(filter_dict, k, v):
    """
    Flattens a dict/list - used to handle deprecated formats
    :param filter_dict: any dict or list
    :param k: key to check
    :param v: associated value
    """
    if isinstance(v, dict):
        filter_dict[k] = ";".join(v.values())
    elif isinstance(v, list):
        if any(isinstance(i, dict) for i in v):
            temp_list = [";".join(s.values()) for s in v if isinstance(s, dict)]
            filter_dict[k] = ";".join(temp_list)
        else:
            filter_dict[k] = ";".join(v)
    else:
        filter_dict[k] = str(filter_dict[k])
