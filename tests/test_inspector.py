"""Tests for all functions in inspector."""

import configparser
from datetime import datetime
import pytest
import inspector
from db.ElasticWorker import connect_elasticsearch
from error import LanguageNotSupportedError, VCSNotSupportedError
from helper import Result


@pytest.fixture
def es():
    """Return ES object"""
    configfile = configparser.ConfigParser()
    configfile.read("./data/config.ini")
    es = connect_elasticsearch(
        {
            'host': configfile.get("secrets", "host", fallback="localhost"),
            'port': configfile.get("secrets", "port", fallback=9200),
        },
        (
            configfile.get("secrets", "es_uid", fallback=""),
            configfile.get("secrets", "es_pass", fallback="")
        )
    )
    return es


@pytest.fixture(autouse=True)
def skip_by_status(request: pytest.FixtureRequest, es: any):
    """
    :param request: pytest request
    :param es: database object
    """
    if request.node.get_closest_marker('skip_status') and \
            request.node.get_closest_marker('skip_status').args[0] == es:
        pytest.skip('Skipped as es connection status: {}'.format(es))


@pytest.fixture
def dependency_payload():
    """
    Generates a fixed payload to test the script
    :return: List of dependencies with language as key
    """
    return {
        'javascript':
            [
                'react@0.12.0',
                'react@17.0.2',
                'jQuery@1.7.4',
                'jQuery'
            ],
        "python":
            [
                'pygithub'
            ],
        "go":
            [
                "https://github.com/go-yaml/yaml",
                "github.com/getsentry/sentry-go",
                "github.com/cactus/go-statsd-client/v5/statsd",
            ]
    }


@pytest.fixture
def result_payload():
    """
    Generates a result object to test the script
    :return: Result object to manipulate
    """
    result: Result = {
        'name': '',
        'version': '',
        'license': '',
        'dependencies': [],
        'timestamp': datetime.utcnow().isoformat()
    }
    return result


def test_make_url_with_version():
    """Check if version specific url is generated for all languages"""
    assert inspector.make_url(
        'python',
        'aiohttp',
        '3.7.2'
    ) == 'https://pypi.org/pypi/aiohttp/3.7.2/json'
    assert inspector.make_url(
        'javascript',
        'diff',
        '5.0.0'
    ) == 'https://registry.npmjs.org/diff/5.0.0'
    assert inspector.make_url(
        'go',
        'bufio',
        'go1.17.6'
    ) == 'https://pkg.go.dev/bufio@go1.17.6'


def test_make_url_without_version():
    """Check if correct url is generated for all languages"""
    assert inspector.make_url(
        'python',
        'aiohttp'
    ) == 'https://pypi.org/pypi/aiohttp/json'
    assert inspector.make_url(
        'javascript',
        'diff'
    ) == 'https://registry.npmjs.org/diff'
    assert inspector.make_url(
        'go',
        'bufio'
    ) == 'https://pkg.go.dev/bufio'


def test_make_single_request_py(es):
    """Test version and license for python"""
    result = inspector.make_single_request(
        es,
        "python",
        "aiohttp",
        "3.7.2"
    )
    assert result['name'] == 'aiohttp'
    assert result['version'] == '3.7.2'
    assert result['license'] == 'Apache 2'
    assert result['dependencies']


def test_make_single_request_js(es):
    """Test version and license for javascript"""
    result = inspector.make_single_request(
        es,
        "javascript",
        "react",
        "17.0.2"
    )
    assert result['name'] == 'react'
    assert result['version'] == '17.0.2'
    assert result['license'] == 'MIT'
    assert result['dependencies']


def test_make_single_request_go(es):
    """Test version and license for go"""
    result = inspector.make_single_request(
        es,
        "go",
        "github.com/getsentry/sentry-go",
        "v0.12.0"
    )
    assert result['name'] == 'github.com/getsentry/sentry-go'
    assert result['version'] == 'v0.12.0'
    assert result['license'] == 'BSD-2-Clause'
    assert result['dependencies']


def test_make_single_request_go_redirect(es):
    """Test version and license for go on redirects"""
    result = inspector.make_single_request(
        es,
        "go",
        "http",
        "go1.16.13"
    )
    assert result['name'] == 'http'
    assert result['version'] == 'go1.16.13'
    assert result['license'] == 'BSD-3-Clause'


def test_make_single_request_go_github(es):
    """Test version and license for go GitHub fallthrough"""
    result = inspector.make_single_request(
        es,
        "go",
        "https://github.com/go-yaml/yaml",
    )
    assert result['name'] == 'https://github.com/go-yaml/yaml'
    assert result['version']
    assert result['license'] == 'Apache Software License'
    assert result['dependencies']


def test_make_multiple_requests(dependency_payload, es):
    """Multiple package requests for JavaScript NPM and Go"""
    result = [
        inspector.make_multiple_requests(es, lang, dependencies)
        for lang, dependencies
        in dependency_payload.items()
    ]
    assert len(result) == 3


def test_make_vcs_request(result_payload):
    """Test VCS handler"""
    inspector.handle_vcs("github.com/getsentry/sentry-go", result_payload)
    assert result_payload["license"] == 'BSD 2-Clause "Simplified" License'


def test_unsupported_language_fails():
    """"""
    with pytest.raises(
        LanguageNotSupportedError,
        match="java"
    ):
        inspector.make_url("java", "foo")


def test_unsupported_vcs_fails(result_payload):
    with pytest.raises(
        VCSNotSupportedError,
        match="gitlab"
    ):
        inspector.handle_vcs(
            "gitlab.com/secmask/awserver",
            result_payload
        )
