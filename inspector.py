#!/usr/bin/env python3
"""
Provides an implementation for Dependency and License Analyzer.
"""

import json
import requests

# Registry
source = { 'python':
	   {'registry': 'PyPI',
	    'url': 'https://pypi.org/pypi',
	    'name': 'name',
	    'version': 'version',
	    'license': 'license',
	    'dependency': 'requires_dist',
	    },
	   'javascript':
	   {'registry': 'npmjs',
	    'url': 'https://registry.npmjs.org',
	    'name': 'name',
	    'version': 'version',
	    'license': 'license',
	    'dependency': 'dependencies',
	    },
	  }

def make_url(language, package, version=""):
    """
    Construct the API JSON request URL.
    """
    if language == "python":
        if version:
            url_elements=(source[language]['url'], package, version, 'json')
        else:
            url_elements=(source[language]['url'], package, 'json')
    else: # JavaScript
        if version:
            url_elements=(source[language]['url'], package, version)
        else:
            url_elements=(source[language]['url'], package)
    return "/".join(url_elements).rstrip("/")

def make_single_request(language, url):
    """
    Obtain package license and dependency information.
    """
    result = {}

    response = requests.get(url)
    data = json.loads(response.text)
    name = source[language]['name']
    version = source[language]['version']
    licence = source[language]['license']
    dependencies =source[language]['dependency']

    if language == "python":
        result['name'] = data["info"][name]
        result['version'] = data["info"][version]
        result['license'] = data["info"][licence]
        result['dependencies'] = data["info"][dependencies]
    else: # JavaScript
        if 'versions' in data.keys():
            latest = data['dist-tags']['latest']
            result['name'] = data['versions'][latest][name]
            result['version']=latest
            result['license']=data['versions'][latest]['license']
            result['dependencies'] = data['versions'][latest]['dependencies']
        else:
            result['name'] = data[name]
            result['version'] = data[version]
            result['license'] = data[licence]
            result['dependencies'] = data[dependencies]
    return result

def make_multiple_requests(language, packages):
    """
    Obtain license and dependency information for list of packages.
    """
    result = {}

    for package in packages:
        url = make_url(language, package)
        result[package] = make_single_request(language, url)
    return result

def main():
    """
    The main function
    """
    url = make_url('javascript', 'react')
    print(make_single_request('javascript', url))

if __name__ == "__main__":
    main()
