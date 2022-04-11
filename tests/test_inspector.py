"""Tests for all functions in inspector."""

from datetime import datetime
import pytest
import inspector
from error import LanguageNotSupportedError, VCSNotSupportedError
from handle_env import get_db
from helper import Result


@pytest.fixture
def psql():
    """
    Returns DB connection if available
    """
    return get_db()


@pytest.fixture
def dependency_payload():
    """
    Generates a fixed payload to test the script
    :return: List of dependencies with language as key
    """
    return {
        'javascript':
            [
                'react;0.12.0',
                'react;17.0.2',
                'jQuery;1.7.4',
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
        'import_name': '',
        'lang_ver': [],
        'pkg_name': '',
        'pkg_ver': '',
        'pkg_lic': ["Other"],
        'pkg_err': {},
        'pkg_dep': [],
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


def test_make_single_request_py(psql):
    """Test version and license for python"""
    result = inspector.make_single_request(
        psql,
        "murdock",
        "python",
        "aiohttp",
        "3.7.2",
        force_schema=False
    )[0]
    assert result['pkg_name'] == 'aiohttp'
    assert result['pkg_ver'] == '3.7.2'
    assert result['pkg_lic'][0] == 'Apache 2'
    assert result['pkg_dep']


def test_make_single_request_js(psql):
    """Test version and license for javascript"""
    result = inspector.make_single_request(
        psql,
        "murdock",
        "javascript",
        "react",
        "17.0.2",
        force_schema=False
    )[0]
    assert result['pkg_name'] == 'react'
    assert result['pkg_ver'] == '17.0.2'
    assert result['pkg_lic'][0] == 'MIT'
    assert result['pkg_dep']


def test_make_single_request_go(psql):
    """Test version and license for go"""
    result = inspector.make_single_request(
        psql,
        "murdock",
        "go",
        "github.com/getsentry/sentry-go",
        "v0.12.0",
        force_schema=False
    )[0]
    assert result['pkg_name'] == 'github.com/getsentry/sentry-go'
    assert result['pkg_ver'] == 'v0.12.0'
    assert result['pkg_lic'][0] == 'BSD-2-Clause'
    assert result['pkg_dep']


def test_make_single_request_go_redirect(psql):
    """Test version and license for go on redirects"""
    result = inspector.make_single_request(
        psql,
        "murdock",
        "go",
        "http",
        "go1.16.13",
        force_schema=False
    )[0]
    assert result['pkg_name'] == 'http'
    assert result['pkg_ver'] == 'go1.16.13'
    assert result['pkg_lic'][0] == 'BSD-3-Clause'


def test_make_single_request_go_github(psql):
    """Test version and license for go GitHub fallthrough"""
    result = inspector.make_single_request(
        psql,
        "murdock",
        "go",
        "https://github.com/go-yaml/yaml",
        force_schema=False
    )[0]
    assert result['pkg_name'] == 'https://github.com/go-yaml/yaml'
    assert result['pkg_ver']
    assert result['pkg_lic'][0] == 'Apache Software License'
    assert result['pkg_dep']


def test_make_multiple_requests(dependency_payload, psql):
    """Multiple package requests for JavaScript NPM and Go"""
    result = [
        inspector.make_multiple_requests(psql, "murdock", lang, dependencies)
        for lang, dependencies
        in dependency_payload.items()
    ]
    assert len(result) == 3


def test_make_vcs_request(result_payload):
    """Test VCS handler"""
    inspector.handle_vcs("go", "github.com/getsentry/sentry-go", result_payload)
    assert result_payload["pkg_lic"] == ['BSD 2-Clause "Simplified" License']


def test_unsupported_language_fails():
    """Checks if exception is raised for unsupported language"""
    with pytest.raises(
        LanguageNotSupportedError,
        match="bhailang"
    ):
        inspector.make_url("bhailang", "foo")


def test_unsupported_vcs_fails(result_payload):
    """Checks if exception is raised for unsupported pattern"""
    with pytest.raises(
        VCSNotSupportedError,
        match="gitlab"
    ):
        inspector.handle_vcs(
            "go",
            "gitlab.com/secmask/awserver",
            result_payload
        )


def test_unsupported_repo(result_payload):
    """Checks if missing dependency or requirement files are handled"""
    inspector.handle_github(
        "go",
        "https://github.com/rust-lang/cargo",
        result_payload
    )
    assert result_payload["pkg_lic"] == ["Other"]
