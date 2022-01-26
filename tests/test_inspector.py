"""Tests for all functions in inspector."""

import pytest
import inspector
from db.ElasticWorker import connect_elasticsearch, create_index, clear_index
import configparser


@pytest.fixture
def es():
    """Return ES object"""
    configfile = configparser.ConfigParser()
    configfile.read("configuration.ini")
    es = connect_elasticsearch(
        {'host': 'localhost', 'port': 9200},
        (
            configfile.get("secrets", "es_uid").strip(),
            configfile.get("secrets", "es_pass").strip()
        )
    )
    return es


@pytest.fixture(autouse=True)
def skip_by_status(request: pytest.FixtureRequest, es: any):
    """
    :param request: pytest request
    :param es: database object
    """
    if request.node.get_closest_marker('skip_status'):
        if request.node.get_closest_marker('skip_status').args[0] == es:
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


@pytest.mark.skip_status(None)
def test_clear_database():
    """Delete database indices - Only for local use"""
    assert clear_index(es, "python")
    assert clear_index(es, "javascript")
    assert clear_index(es, "go")


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
    assert inspector.make_url(
        'java',
        'maven',
        'random'
    ) == ""


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


@pytest.mark.skip_status(None)
def test_created_index():
    """Create language indices again for caching"""
    assert create_index(es, "python")
    assert create_index(es, "javascript")
    assert create_index(es, "go")


def test_make_single_request_py():
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
    assert len(result['dependencies']) == 10


def test_make_single_request_js():
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
    assert len(result['dependencies']) == 2


def test_make_single_request_go():
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
    assert len(result['dependencies']) == 32


def test_make_single_request_go_github():
    """Test version and license for go GitHub fallthrough"""
    result = inspector.make_single_request(
        es,
        "go",
        "https://github.com/go-yaml/yaml",
    )
    assert result['name'] == 'https://github.com/go-yaml/yaml'
    assert result['version']
    assert result['license'] == 'Apache Software License'
    assert len(result['dependencies']) != 0


def test_make_multiple_requests(dependency_payload):
    """Multiple package requests for JavaScript NPM and Go"""
    result = [
        inspector.make_multiple_requests(es, lang, dependencies)
        for lang, dependencies
        in dependency_payload.items()
    ]
    assert len(result) == 3


def test_make_vcs_request():
    """Test VCS handler"""
    assert inspector.handle_vcs("code.didiapp.com/server-go/checker") == {}
    result = inspector.handle_vcs("github.com/getsentry/sentry-go")
    assert result["license"] == 'BSD 2-Clause "Simplified" License'
